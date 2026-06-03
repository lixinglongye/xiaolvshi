import base64
import io
import logging
import os
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

try:
    import fitz
except ImportError:  # pragma: no cover - depends on runtime optional dependency
    fitz = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional local OCR dependency
    Image = None

try:
    import pytesseract
except ImportError:  # pragma: no cover - optional local OCR dependency
    pytesseract = None

logger = logging.getLogger(__name__)


MAX_EXTRACTED_CHARS = 220_000
PDF_TEXT_MIN_CHARS_PER_PAGE = 20
PDF_DEFAULT_OCR_DPI = 180
PDF_DEFAULT_MAX_OCR_PAGES = 40


class DocumentExtractionError(ValueError):
    """Raised when an uploaded document cannot be converted to reviewable text."""


@dataclass
class ExtractionResult:
    text: str
    parser: str
    page_count: int | None = None
    char_count: int = 0
    warnings: list[str] = field(default_factory=list)
    text_layer_pages: list[int] = field(default_factory=list)
    ocr_pages: list[int] = field(default_factory=list)
    low_text_pages: list[int] = field(default_factory=list)


class DocumentExtractionService:
    """Extract reviewable text from uploaded legal-document files."""

    TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".rtf"}
    TEXT_MIME_PREFIXES = ("text/",)
    TEXT_MIME_TYPES = {
        "application/json",
        "application/xml",
        "application/csv",
        "application/rtf",
    }
    PDF_MIME_TYPES = {"application/pdf"}
    DOCX_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def extract(self, data: bytes, file_name: str = "", mime_type: str = "") -> ExtractionResult:
        if not data:
            raise DocumentExtractionError("上传文件为空，无法进行法律审查。")

        suffix = Path(file_name or "").suffix.lower()
        normalized_mime = (mime_type or "").split(";")[0].strip().lower()

        if suffix == ".pdf" or normalized_mime in self.PDF_MIME_TYPES:
            return self._extract_pdf(data)
        if suffix == ".docx" or normalized_mime in self.DOCX_MIME_TYPES:
            return self._extract_docx(data)
        if suffix == ".doc":
            raise DocumentExtractionError("暂不支持旧版 .doc 文件，请另存为 .docx 或 PDF 后重新上传。")
        if self._looks_like_text(suffix, normalized_mime):
            return self._extract_text(data)

        # Last resort: try text decoding before rejecting the file. This helps with
        # browser uploads that omit or mislabel content types.
        try:
            return self._extract_text(data)
        except DocumentExtractionError:
            raise DocumentExtractionError("暂不支持该文件格式。请上传 PDF、DOCX、TXT、Markdown 或可复制文本。")

    async def extract_async(
        self,
        data: bytes,
        file_name: str = "",
        mime_type: str = "",
        *,
        enable_ocr: bool = True,
    ) -> ExtractionResult:
        """Async extraction path with OCR fallback for image/scanned PDFs."""
        if not data:
            raise DocumentExtractionError("上传文件为空，无法进行法律审查。")

        suffix = Path(file_name or "").suffix.lower()
        normalized_mime = (mime_type or "").split(";")[0].strip().lower()
        if suffix == ".pdf" or normalized_mime in self.PDF_MIME_TYPES:
            return await self._extract_pdf_async(data, enable_ocr=enable_ocr)
        return self.extract(data, file_name=file_name, mime_type=mime_type)

    def _looks_like_text(self, suffix: str, mime_type: str) -> bool:
        return (
            suffix in self.TEXT_EXTENSIONS
            or mime_type in self.TEXT_MIME_TYPES
            or any(mime_type.startswith(prefix) for prefix in self.TEXT_MIME_PREFIXES)
        )

    def _extract_text(self, data: bytes) -> ExtractionResult:
        errors: list[str] = []
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
            try:
                text = data.decode(encoding)
                return self._finalize_text(text, parser=f"text:{encoding}")
            except UnicodeDecodeError as exc:
                errors.append(f"{encoding}: {exc}")

        logger.warning("Text extraction failed with all encodings: %s", errors)
        raise DocumentExtractionError("文本文件编码无法识别，请转换为 UTF-8 后重新上传。")

    def _extract_pdf(self, data: bytes) -> ExtractionResult:
        if fitz is None:
            raise DocumentExtractionError("当前后端环境未安装 PyMuPDF，无法解析 PDF。请安装 requirements.txt 后重试。")
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise DocumentExtractionError("PDF 文件无法读取，可能已损坏或加密。") from exc

        warnings: list[str] = []
        page_texts: list[str] = []
        text_layer_pages: list[int] = []
        low_text_pages: list[int] = []
        total_pages = 0
        try:
            if doc.needs_pass:
                raise DocumentExtractionError("PDF 文件已加密，请解除密码后重新上传。")

            total_pages = doc.page_count
            for page_index, page in enumerate(doc, start=1):
                text = self._normalize_text(page.get_text("text") or "")
                if text.strip():
                    page_texts.append(f"[第 {page_index} 页]\n{text.strip()}")
                    text_layer_pages.append(page_index)
                    if len(text.strip()) < PDF_TEXT_MIN_CHARS_PER_PAGE:
                        low_text_pages.append(page_index)
                else:
                    warnings.append(f"第 {page_index} 页未提取到文本，可能是扫描件或图片页。")
        finally:
            doc.close()

        result = self._finalize_text("\n\n".join(page_texts), parser="pymupdf", warnings=warnings)
        result.page_count = total_pages or None
        result.text_layer_pages = text_layer_pages
        result.low_text_pages = low_text_pages
        return result

    async def _extract_pdf_async(self, data: bytes, *, enable_ocr: bool) -> ExtractionResult:
        if fitz is None:
            raise DocumentExtractionError("当前后端环境未安装 PyMuPDF，无法解析 PDF。请安装 requirements.txt 后重试。")
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise DocumentExtractionError("PDF 文件无法读取，可能已损坏或加密。") from exc

        warnings: list[str] = []
        page_text_by_number: dict[int, str] = {}
        text_layer_pages: list[int] = []
        low_text_pages: list[int] = []
        ocr_candidate_pages: list[int] = []
        ocr_pages: list[int] = []
        max_ocr_pages = self._int_env("PDF_OCR_MAX_PAGES", PDF_DEFAULT_MAX_OCR_PAGES)

        try:
            if doc.needs_pass:
                raise DocumentExtractionError("PDF 文件已加密，请解除密码后重新上传。")

            total_pages = doc.page_count
            for page_index, page in enumerate(doc, start=1):
                text = self._normalize_text(page.get_text("text") or "")
                if len(text) >= PDF_TEXT_MIN_CHARS_PER_PAGE:
                    page_text_by_number[page_index] = f"[第 {page_index} 页]\n{text}"
                    text_layer_pages.append(page_index)
                else:
                    if text:
                        low_text_pages.append(page_index)
                        page_text_by_number[page_index] = f"[第 {page_index} 页]\n{text}"
                    ocr_candidate_pages.append(page_index)

            if enable_ocr and ocr_candidate_pages:
                for page_number in ocr_candidate_pages[:max_ocr_pages]:
                    page = doc.load_page(page_number - 1)
                    ocr_text = await self._ocr_pdf_page(page, page_number)
                    if ocr_text:
                        existing = page_text_by_number.get(page_number, f"[第 {page_number} 页]")
                        page_text_by_number[page_number] = f"{existing}\n[OCR]\n{ocr_text}".strip()
                        ocr_pages.append(page_number)
                    else:
                        warnings.append(f"第 {page_number} 页 OCR 未识别到有效文本。")
                skipped = ocr_candidate_pages[max_ocr_pages:]
                if skipped:
                    warnings.append(
                        f"扫描页较多，仅 OCR 前 {max_ocr_pages} 页；剩余 {len(skipped)} 页未 OCR，可通过 PDF_OCR_MAX_PAGES 调整。"
                    )
            elif ocr_candidate_pages:
                warnings.append(f"{len(ocr_candidate_pages)} 页疑似扫描页，当前请求未启用 OCR。")
        finally:
            doc.close()

        ordered_text = "\n\n".join(page_text_by_number[idx] for idx in sorted(page_text_by_number))
        if not ordered_text.strip():
            detail = "未能从 PDF 提取到可分析文本。"
            if ocr_candidate_pages and not enable_ocr:
                detail += " 该文件疑似扫描件，请启用 OCR。"
            elif ocr_candidate_pages:
                detail += " OCR 未识别到有效文本，请确认图片清晰度或使用可复制文本版本。"
            raise DocumentExtractionError(detail)

        parser = "pymupdf+ocr" if ocr_pages else "pymupdf"
        result = self._finalize_text(ordered_text, parser=parser, warnings=warnings)
        result.page_count = total_pages or None
        result.text_layer_pages = text_layer_pages
        result.low_text_pages = low_text_pages
        result.ocr_pages = ocr_pages
        return result

    async def _ocr_pdf_page(self, page, page_number: int) -> str:
        local_text = self._ocr_pdf_page_local(page, page_number)
        if local_text:
            return local_text
        return await self._ocr_pdf_page_ai(page, page_number)

    def _ocr_pdf_page_local(self, page, page_number: int) -> str:
        if Image is None or pytesseract is None:
            return ""
        try:
            png_bytes = self._render_pdf_page_png(page)
            image = Image.open(io.BytesIO(png_bytes))
            text = pytesseract.image_to_string(image, lang=os.getenv("PDF_OCR_TESSERACT_LANG", "chi_sim+eng"))
            return self._normalize_text(text)
        except Exception as exc:
            logger.info("Local OCR failed on PDF page %s: %s", page_number, exc)
            return ""

    async def _ocr_pdf_page_ai(self, page, page_number: int) -> str:
        try:
            from core.config import settings
            from schemas.aihub import ChatMessage, ContentPartImage, ContentPartText, GenTxtRequest, ImageUrl
            from services.aihub import AIHubService
            from services.model_catalog import resolve_model

            png_bytes = self._render_pdf_page_png(page)
            image_data_uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
            model = resolve_model(getattr(settings, "app_ocr_model", None), task="ocr")
            response = await AIHubService().gentxt(
                GenTxtRequest(
                    messages=[
                        ChatMessage(
                            role="system",
                            content=(
                                "你是法律文档 OCR 引擎。只输出图片中可见的原文文本，不解释、不总结、不改写。"
                                "保留标题、条款编号、金额、日期、主体名称和换行。无法识别的字用 [?]。"
                            ),
                        ),
                        ChatMessage(
                            role="user",
                            content=[
                                ContentPartText(text=f"请 OCR 识别 PDF 第 {page_number} 页。"),
                                ContentPartImage(image_url=ImageUrl(url=image_data_uri)),
                            ],
                        ),
                    ],
                    model=model,
                    task="ocr",
                    stream=False,
                    temperature=0.0,
                    max_tokens=2500,
                )
            )
            text = self._normalize_text(response.content)
            if text.startswith("```"):
                text = text.strip("`").strip()
            return text
        except Exception as exc:
            logger.warning("AI OCR failed on PDF page %s: %s", page_number, exc)
            return ""

    def _render_pdf_page_png(self, page) -> bytes:
        dpi = self._int_env("PDF_OCR_DPI", PDF_DEFAULT_OCR_DPI)
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return pixmap.tobytes("png")

    def _int_env(self, name: str, default: int) -> int:
        try:
            value = int(os.getenv(name, str(default)))
            return max(1, value)
        except ValueError:
            return default

    def _extract_docx(self, data: bytes) -> ExtractionResult:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                document_xml = zf.read("word/document.xml")
                relationship_names = [name for name in zf.namelist() if name.startswith("word/") and name.endswith(".xml")]
                extra_xml = [
                    zf.read(name)
                    for name in relationship_names
                    if re.match(r"word/(header|footer)\d+\.xml$", name)
                ]
        except KeyError as exc:
            raise DocumentExtractionError("DOCX 文件结构不完整，无法读取正文。") from exc
        except zipfile.BadZipFile as exc:
            raise DocumentExtractionError("DOCX 文件无法读取，可能已损坏。") from exc

        parts = [self._extract_word_xml_text(document_xml)]
        parts.extend(self._extract_word_xml_text(xml) for xml in extra_xml)
        return self._finalize_text("\n\n".join(p for p in parts if p.strip()), parser="docx-xml")

    def _extract_word_xml_text(self, xml_bytes: bytes) -> str:
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        try:
            root = ElementTree.fromstring(xml_bytes)
        except ElementTree.ParseError:
            return ""

        paragraphs: list[str] = []
        for paragraph in root.findall(".//w:p", namespace):
            texts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs)

    def _finalize_text(
        self,
        text: str,
        parser: str,
        warnings: Iterable[str] | None = None,
    ) -> ExtractionResult:
        normalized = self._normalize_text(text)
        result_warnings = list(warnings or [])
        if not normalized.strip():
            detail = "未能从文件中提取到可分析文本。"
            if result_warnings:
                detail += " " + " ".join(result_warnings[:3])
            raise DocumentExtractionError(detail)

        if len(normalized) > MAX_EXTRACTED_CHARS:
            normalized = normalized[:MAX_EXTRACTED_CHARS]
            result_warnings.append(f"文档较长，已截取前 {MAX_EXTRACTED_CHARS} 字用于本次审查。")

        return ExtractionResult(
            text=normalized,
            parser=parser,
            char_count=len(normalized),
            warnings=result_warnings,
        )

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\x00", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

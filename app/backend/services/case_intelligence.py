import hashlib
import html
import io
import json
import logging
import mimetypes
import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Optional
from xml.etree import ElementTree

from core.config import settings
from models.case_files import Case_files
from models.case_facts import Case_facts
from models.case_materials import Case_materials
from models.case_parties import Case_parties
from models.cases import Cases
from models.claims import Claims
from models.evidence_items import Evidence_items
from models.evidences import Evidences
from models.fact_events import Fact_events
from models.generated_documents import Generated_documents
from models.import_jobs import Import_jobs
from models.legal_sources import Legal_sources
from services.document_extraction import DocumentExtractionError, DocumentExtractionService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DEFAULT_MAX_ZIP_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_EXTRACTED_BYTES = 500 * 1024 * 1024
MAX_ZIP_DEPTH = 5
MAX_TEXT_PER_FILE = 80_000
DISALLOWED_EXTENSIONS = {".exe", ".bat", ".cmd", ".com", ".dll", ".msi", ".ps1", ".sh", ".scr", ".jar"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
AUDIO_VIDEO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi", ".wmv"}

MATERIAL_CATEGORIES: list[tuple[str, str, str, list[str]]] = [
    ("identity", "主体身份材料", "身份证明/主体资格材料", ["身份证", "营业执照", "法定代表人", "授权委托", "统一社会信用代码"]),
    ("contract", "合同与基础法律关系材料", "合同/协议", ["合同", "协议", "订单", "报价", "招投标", "平台规则"]),
    ("performance", "履行过程材料", "履行/交付材料", ["发货", "收货", "验收", "交付", "进度", "签收"]),
    ("payment", "金钱往来材料", "付款/票据材料", ["付款", "转账", "流水", "发票", "收据", "对账", "欠款", "银行"]),
    ("communication", "沟通与通知材料", "沟通/通知材料", ["微信", "聊天", "邮件", "短信", "催告", "通知", "解除函", "回复"]),
    ("damage", "争议与损失材料", "损失/争议材料", ["损失", "维修", "评估", "鉴定", "照片", "视频", "投诉", "处罚"]),
    ("procedure", "诉讼/仲裁程序材料", "诉讼/仲裁材料", ["起诉状", "答辩状", "证据目录", "传票", "判决书", "裁定书", "调解书", "仲裁"]),
]

LAW_SOURCES = [
    {
        "source_type": "law",
        "title": "中华人民共和国民事诉讼法（2023修正）第一百二十三条",
        "code_ref": "第一百二十三条",
        "summary": "起诉应当向人民法院递交起诉状，并按照被告人数提出副本。",
        "legal_effect_level": "法律",
        "verified": True,
    },
    {
        "source_type": "law",
        "title": "中华人民共和国民事诉讼法（2023修正）第一百二十四条",
        "code_ref": "第一百二十四条",
        "summary": "起诉状应当记明当事人基本信息、诉讼请求和事实理由、证据和证据来源等。",
        "legal_effect_level": "法律",
        "verified": True,
    },
    {
        "source_type": "judicial_interpretation",
        "title": "最高人民法院关于民事诉讼证据的若干规定第十九条",
        "code_ref": "第十九条",
        "summary": "当事人应对证据材料逐一分类编号，对来源、证明对象和内容作简要说明。",
        "legal_effect_level": "司法解释/证据规则",
        "verified": True,
    },
]


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _json_loads(raw: Optional[str], fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _unique(items: list[str], limit: int = 12) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def _normalize_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _amount_to_float(value: str) -> Optional[float]:
    if not value:
        return None
    text = value.replace(",", "").replace("，", "")
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return None
    amount = float(match.group(1))
    if "万" in text:
        amount *= 10000
    return amount


@dataclass
class ParsedZipFile:
    file_id: str
    original_name: str
    relative_path: str
    storage_path: str
    mime_type: str
    file_hash: str
    size_bytes: int
    page_count: Optional[int]
    text_extracted: bool
    ocr_required: bool
    parsed_text: str
    text_excerpt: str
    doc_type: str
    evidence_category: str
    confidence: float
    parties: list[str]
    dates: list[str]
    amounts: list[str]
    processing_status: str
    quarantine_reason: Optional[str] = None


class CaseImportService:
    """ZIP case package ingestion pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.extractor = DocumentExtractionService()

    async def import_zip(
        self,
        *,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        upload_mode: str = "auto",
        workspace_id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._validate_zip_limits(file_bytes)
        job = Import_jobs(
            user_id=user_id,
            workspace_id=workspace_id,
            upload_mode=upload_mode,
            status="scanning",
            original_filename=filename,
            total_size_bytes=len(file_bytes),
            progress=0.05,
            warnings_json=_json_dumps([]),
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            root = self._job_storage_root(job.id)
            root.mkdir(parents=True, exist_ok=True)
            zip_path = root / self._safe_filename(filename or f"case_import_{job.id}.zip")
            zip_path.write_bytes(file_bytes)
            job.stored_path = str(zip_path)
            await self.db.commit()

            parsed_files, warnings = await self._scan_and_parse_zip(job, file_bytes, root)
            clusters = self._cluster_files(parsed_files, upload_mode=upload_mode)
            created_case_ids: list[int] = []
            for cluster in clusters:
                if cluster["confidence"] >= 0.85:
                    case_id = await self._create_case_from_cluster(user_id=user_id, cluster=cluster, parsed_files=parsed_files)
                    cluster["case_id"] = case_id
                    created_case_ids.append(case_id)
                else:
                    cluster["needs_human_review"] = True

            unclassified = [item.file_id for item in parsed_files if item.evidence_category.startswith("未分类")]
            job.status = "completed"
            job.upload_mode_inferred = "single_case" if len(clusters) <= 1 else "multi_case"
            job.total_files = len(parsed_files)
            job.parsed_files = len([item for item in parsed_files if item.text_extracted or item.processing_status == "parsed"])
            job.decompressed_size_bytes = sum(item.size_bytes for item in parsed_files)
            job.cluster_count = len(clusters)
            job.unclassified_count = len(unclassified)
            job.progress = 1.0
            job.clusters_json = _json_dumps(clusters)
            job.warnings_json = _json_dumps(warnings)
            await self.db.commit()
            await self.db.refresh(job)
            return await self.serialize_job(job, include_files=True, created_case_ids=created_case_ids)
        except Exception as exc:
            logger.error("ZIP import failed: %s", exc, exc_info=True)
            job.status = "failed"
            job.error_message = str(exc)
            job.progress = 1.0
            await self.db.commit()
            raise

    async def get_job(self, *, job_id: int, user_id: str) -> Import_jobs:
        result = await self.db.execute(select(Import_jobs).where(Import_jobs.id == job_id, Import_jobs.user_id == user_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError("Import job not found")
        return job

    async def serialize_job(
        self,
        job: Import_jobs,
        *,
        include_files: bool = False,
        created_case_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        data = {
            "import_job_id": job.id,
            "status": job.status,
            "upload_mode": job.upload_mode,
            "upload_mode_inferred": job.upload_mode_inferred,
            "total_files": job.total_files or 0,
            "parsed_files": job.parsed_files or 0,
            "progress": job.progress or 0,
            "clusters": _json_loads(job.clusters_json, []),
            "unclassified_files": job.unclassified_count or 0,
            "warnings": _json_loads(job.warnings_json, []),
            "error": job.error_message,
            "created_case_ids": created_case_ids or [],
        }
        if include_files:
            result = await self.db.execute(select(Case_files).where(Case_files.import_job_id == job.id).order_by(Case_files.id))
            data["files"] = [self.serialize_case_file(item) for item in result.scalars().all()]
        return data

    def serialize_case_file(self, item: Case_files) -> dict[str, Any]:
        return {
            "id": item.id,
            "file_id": item.file_id,
            "case_id": item.case_id,
            "original_name": item.original_name,
            "relative_path": item.relative_path,
            "mime_type": item.mime_type,
            "hash": item.file_hash,
            "size_bytes": item.size_bytes,
            "page_count": item.page_count,
            "text_extracted": item.text_extracted,
            "ocr_required": item.ocr_required,
            "doc_type": item.doc_type,
            "evidence_category": item.evidence_category,
            "confidence": item.confidence,
            "parties_detected": _json_loads(item.parties_detected, []),
            "dates_detected": _json_loads(item.dates_detected, []),
            "amounts_detected": _json_loads(item.amounts_detected, []),
            "processing_status": item.processing_status,
            "quarantine_reason": item.quarantine_reason,
        }

    async def confirm_clusters(
        self,
        *,
        job_id: int,
        user_id: str,
        clusters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        job = await self.get_job(job_id=job_id, user_id=user_id)
        files_result = await self.db.execute(select(Case_files).where(Case_files.import_job_id == job.id))
        file_rows = files_result.scalars().all()
        parsed_files = [self._parsed_file_from_row(row) for row in file_rows]
        created_case_ids: list[int] = []
        for cluster in clusters:
            normalized = {
                "cluster_id": cluster.get("cluster_id") or f"manual_{len(created_case_ids) + 1:03d}",
                "suggested_case_name": cluster.get("case_name") or cluster.get("suggested_case_name") or "人工确认案件",
                "confidence": 1.0,
                "main_parties": cluster.get("main_parties") or [],
                "case_number": cluster.get("case_number"),
                "reason": "律师人工确认案件分组",
                "file_ids": cluster.get("file_ids") or [],
                "needs_human_review": False,
            }
            case_id = await self._create_case_from_cluster(user_id=user_id, cluster=normalized, parsed_files=parsed_files)
            normalized["case_id"] = case_id
            created_case_ids.append(case_id)
        existing = _json_loads(job.clusters_json, [])
        job.clusters_json = _json_dumps(existing + clusters)
        job.status = "completed"
        await self.db.commit()
        return {"status": "completed", "created_case_ids": created_case_ids}

    def _validate_zip_limits(self, data: bytes) -> None:
        max_bytes = int(os.getenv("CASE_IMPORT_MAX_ZIP_MB", "100")) * 1024 * 1024
        if not data:
            raise ValueError("ZIP 文件为空")
        if len(data) > max(max_bytes, DEFAULT_MAX_ZIP_BYTES):
            raise ValueError("ZIP 文件超过当前导入大小限制")
        if not zipfile.is_zipfile(io.BytesIO(data)):
            raise ValueError("请上传有效 ZIP 压缩包")

    def _job_storage_root(self, job_id: int) -> Path:
        base = Path(settings.local_storage_dir or "./local_storage")
        if not base.is_absolute():
            base = Path.cwd() / base
        return base / "case_imports" / str(job_id)

    def _safe_filename(self, filename: str) -> str:
        name = Path(filename).name.strip() or "upload.zip"
        return re.sub(r"[^\w.\-\u4e00-\u9fa5（）() ]+", "_", name)

    async def _scan_and_parse_zip(self, job: Import_jobs, data: bytes, root: Path) -> tuple[list[ParsedZipFile], list[str]]:
        warnings: list[str] = []
        parsed_files: list[ParsedZipFile] = []
        seen_hashes: set[str] = set()
        total_uncompressed = 0
        max_uncompressed = int(os.getenv("CASE_IMPORT_MAX_EXTRACTED_MB", "500")) * 1024 * 1024

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = [info for info in zf.infolist() if not info.is_dir()]
            for index, info in enumerate(infos, start=1):
                relative = info.filename.replace("\\", "/")
                quarantine = self._validate_zip_member(relative, info.file_size)
                total_uncompressed += info.file_size
                if total_uncompressed > max(max_uncompressed, DEFAULT_MAX_EXTRACTED_BYTES):
                    raise ValueError("ZIP 解压后体积超过限制，已中止导入")
                if quarantine:
                    warnings.append(f"{relative} 已隔离：{quarantine}")
                    parsed = await self._record_quarantined_file(job, relative, info.file_size, quarantine)
                    parsed_files.append(parsed)
                    continue

                file_bytes = zf.read(info)
                file_hash = hashlib.sha256(file_bytes).hexdigest()
                if file_hash in seen_hashes:
                    warnings.append(f"{relative} 与已有文件重复，已标记为重复材料")
                    parsed = await self._record_duplicate_file(job, relative, file_bytes, root)
                    parsed_files.append(parsed)
                    continue
                seen_hashes.add(file_hash)

                parsed = await self._parse_member(job, relative, file_bytes, root, file_hash)
                parsed_files.append(parsed)
                job.progress = min(0.75, 0.1 + index / max(1, len(infos)) * 0.65)
                job.total_files = len(parsed_files)
                job.parsed_files = len([item for item in parsed_files if item.text_extracted])
                await self.db.commit()

        return parsed_files, warnings

    def _validate_zip_member(self, relative_path: str, file_size: int) -> Optional[str]:
        if "\x00" in relative_path:
            return "文件名包含非法字符"
        if re.match(r"^[a-zA-Z]:", relative_path) or relative_path.startswith("/"):
            return "压缩包内存在绝对路径"
        pure = PurePosixPath(relative_path)
        if ".." in pure.parts:
            return "压缩包内存在路径穿越"
        if len([part for part in pure.parts if part not in {"", "."}]) > MAX_ZIP_DEPTH + 1:
            return "嵌套层级超过限制"
        suffix = Path(relative_path).suffix.lower()
        if suffix in DISALLOWED_EXTENSIONS:
            return "可执行或脚本文件不进入解析流程"
        if file_size <= 0:
            return "空文件"
        return None

    async def _record_quarantined_file(self, job: Import_jobs, relative: str, size: int, reason: str) -> ParsedZipFile:
        parsed = ParsedZipFile(
            file_id=f"file_{job.id}_{len(relative)}_{abs(hash(relative)) % 100000}",
            original_name=Path(relative).name,
            relative_path=relative,
            storage_path="",
            mime_type="application/octet-stream",
            file_hash="",
            size_bytes=size,
            page_count=None,
            text_extracted=False,
            ocr_required=False,
            parsed_text="",
            text_excerpt="",
            doc_type="unknown",
            evidence_category="未分类/低置信材料",
            confidence=0.0,
            parties=[],
            dates=[],
            amounts=[],
            processing_status="quarantined",
            quarantine_reason=reason,
        )
        await self._persist_case_file(job, parsed)
        return parsed

    async def _record_duplicate_file(self, job: Import_jobs, relative: str, file_bytes: bytes, root: Path) -> ParsedZipFile:
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        safe_path = self._resolve_member_path(root, relative)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_bytes(file_bytes)
        parsed = ParsedZipFile(
            file_id=f"file_{job.id}_{file_hash[:10]}",
            original_name=Path(relative).name,
            relative_path=relative,
            storage_path=str(safe_path),
            mime_type=self._detect_mime(relative, file_bytes),
            file_hash=file_hash,
            size_bytes=len(file_bytes),
            page_count=None,
            text_extracted=False,
            ocr_required=False,
            parsed_text="",
            text_excerpt="",
            doc_type="duplicate",
            evidence_category="未分类/低置信材料",
            confidence=0.2,
            parties=[],
            dates=[],
            amounts=[],
            processing_status="duplicate",
            quarantine_reason="重复文件",
        )
        await self._persist_case_file(job, parsed)
        return parsed

    async def _parse_member(
        self,
        job: Import_jobs,
        relative: str,
        file_bytes: bytes,
        root: Path,
        file_hash: str,
    ) -> ParsedZipFile:
        target = self._resolve_member_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(file_bytes)
        mime_type = self._detect_mime(relative, file_bytes)
        parsed_text, page_count, text_extracted, ocr_required = await self._extract_text(relative, mime_type, file_bytes)
        doc_type, category, confidence = await self._classify_async(relative, parsed_text, mime_type)
        parties = self._extract_parties(f"{relative}\n{parsed_text}")
        dates = self._extract_dates(f"{relative}\n{parsed_text}")
        amounts = self._extract_amounts(f"{relative}\n{parsed_text}")
        parsed = ParsedZipFile(
            file_id=f"file_{job.id}_{len(file_hash)}_{abs(hash(relative)) % 100000}",
            original_name=Path(relative).name,
            relative_path=relative,
            storage_path=str(target),
            mime_type=mime_type,
            file_hash=file_hash,
            size_bytes=len(file_bytes),
            page_count=page_count,
            text_extracted=text_extracted,
            ocr_required=ocr_required,
            parsed_text=parsed_text[:MAX_TEXT_PER_FILE],
            text_excerpt=parsed_text[:1200],
            doc_type=doc_type,
            evidence_category=category,
            confidence=confidence,
            parties=parties,
            dates=dates,
            amounts=amounts,
            processing_status="parsed" if text_extracted or doc_type in {"image", "audio_video"} else "metadata_only",
        )
        await self._persist_case_file(job, parsed)
        return parsed

    def _resolve_member_path(self, root: Path, relative: str) -> Path:
        pure = PurePosixPath(relative)
        target = root.joinpath(*pure.parts).resolve()
        root_resolved = root.resolve()
        if root_resolved not in target.parents and target != root_resolved:
            raise ValueError("ZIP 路径越界")
        return target

    async def _extract_text(self, relative: str, mime_type: str, data: bytes) -> tuple[str, Optional[int], bool, bool]:
        suffix = Path(relative).suffix.lower()
        if suffix in IMAGE_EXTENSIONS or mime_type.startswith("image/"):
            return "", None, False, True
        if suffix in AUDIO_VIDEO_EXTENSIONS or mime_type.startswith(("audio/", "video/")):
            return "", None, False, False
        if suffix in {".xlsx", ".xls"}:
            return self._extract_spreadsheet_text(data, suffix), None, True, False
        if suffix in {".html", ".htm"}:
            return _normalize_text(self._decode_text(data)), None, True, False
        try:
            result = await self.extractor.extract_async(data, file_name=relative, mime_type=mime_type, enable_ocr=True)
            return result.text, result.page_count, True, bool(result.ocr_pages or result.low_text_pages)
        except DocumentExtractionError as exc:
            logger.info("Metadata-only parse for %s: %s", relative, exc)
            return "", None, False, suffix == ".pdf"

    def _extract_spreadsheet_text(self, data: bytes, suffix: str) -> str:
        if suffix != ".xlsx":
            return ""
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = [name for name in zf.namelist() if name.startswith("xl/sharedStrings") or name.startswith("xl/worksheets/sheet")]
                texts: list[str] = []
                for name in names[:8]:
                    raw = zf.read(name)
                    try:
                        root = ElementTree.fromstring(raw)
                    except ElementTree.ParseError:
                        continue
                    for node in root.iter():
                        if node.tag.endswith("}t") and node.text:
                            texts.append(node.text)
                return _normalize_text("\n".join(texts))[:MAX_TEXT_PER_FILE]
        except Exception:
            return ""

    def _decode_text(self, data: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return ""

    def _detect_mime(self, filename: str, data: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if data.startswith(b"%PDF"):
            return "application/pdf"
        if data.startswith(b"\x89PNG"):
            return "image/png"
        if data.startswith(b"\xff\xd8"):
            return "image/jpeg"
        if data.startswith(b"PK\x03\x04") and suffix == ".docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if data.startswith(b"PK\x03\x04") and suffix == ".xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return mimetypes.guess_type(filename)[0] or "application/octet-stream"

    def _classify(self, relative: str, text: str, mime_type: str) -> tuple[str, str, float]:
        suffix = Path(relative).suffix.lower()
        haystack = f"{relative}\n{text[:5000]}".lower()
        if suffix in IMAGE_EXTENSIONS or mime_type.startswith("image/"):
            return "image", "争议与损失材料", 0.72
        if suffix in AUDIO_VIDEO_EXTENSIONS or mime_type.startswith(("audio/", "video/")):
            return "audio_video", "争议与损失材料", 0.68
        best = ("other", "未分类/低置信材料", 0.45)
        for doc_type, category, label, keywords in MATERIAL_CATEGORIES:
            score = sum(1 for keyword in keywords if keyword.lower() in haystack)
            if score:
                confidence = min(0.95, 0.62 + score * 0.08)
                if confidence > best[2]:
                    best = (doc_type, category, confidence)
        if suffix in {".pdf", ".docx", ".txt", ".md"} and best[0] == "other":
            return "document", "未分类/低置信材料", 0.52
        return best

    async def _classify_async(self, relative: str, text: str, mime_type: str) -> tuple[str, str, float]:
        """Classify cheaply: deterministic rules first, small model only for uncertain files."""
        rule_doc_type, rule_category, rule_confidence = self._classify(relative, text, mime_type)
        if rule_confidence >= 0.85:
            return rule_doc_type, rule_category, rule_confidence
        if not getattr(settings, "case_import_ai_classifier_enabled", True):
            return rule_doc_type, rule_category, rule_confidence
        if not getattr(settings, "app_ai_key", None) or not getattr(settings, "app_ai_base_url", None):
            return rule_doc_type, rule_category, rule_confidence
        if not text.strip() and rule_doc_type not in {"document", "other"}:
            return rule_doc_type, rule_category, rule_confidence

        try:
            from schemas.aihub import ChatMessage, GenTxtRequest
            from services.aihub import AIHubService
            from services.model_catalog import resolve_model

            model = resolve_model(
                getattr(settings, "app_ai_classifier_model", None) or getattr(settings, "app_ai_fast_model", None),
                task="classification",
            )
            sample = text[:2400] if text.strip() else "无可抽取正文，请主要依据文件名、路径和 MIME 判断。"
            prompt = f"""请用低成本分类模型对律师案件材料做材料分类。

文件路径：{relative}
MIME：{mime_type}
规则分类：doc_type={rule_doc_type}, evidence_category={rule_category}, confidence={rule_confidence}

可选 doc_type：
identity, contract, performance, payment, communication, damage, procedure, document, image, audio_video, other

可选 evidence_category：
主体身份材料、合同与基础法律关系材料、履行过程材料、金钱往来材料、沟通与通知材料、争议与损失材料、诉讼/仲裁程序材料、未分类/低置信材料

材料正文片段：
{sample}

只输出 JSON：
{{"doc_type":"...","evidence_category":"...","confidence":0.0,"reason":"..."}}"""
            response = await AIHubService().gentxt(
                GenTxtRequest(
                    messages=[
                        ChatMessage(
                            role="system",
                            content="你是便宜快速的法律材料分类模型，只做分类，不做法律分析，不输出 Markdown。",
                        ),
                        ChatMessage(role="user", content=prompt),
                    ],
                    model=model,
                    stream=False,
                    temperature=0.0,
                    max_tokens=700,
                    response_format={"type": "json_object"},
                )
            )
            data = json.loads(response.content)
            doc_type = str(data.get("doc_type") or rule_doc_type)
            category = str(data.get("evidence_category") or rule_category)
            confidence = float(data.get("confidence") or rule_confidence)
            allowed_categories = {item[1] for item in MATERIAL_CATEGORIES} | {"未分类/低置信材料"}
            allowed_doc_types = {item[0] for item in MATERIAL_CATEGORIES} | {"document", "image", "audio_video", "other"}
            if doc_type not in allowed_doc_types or category not in allowed_categories:
                return rule_doc_type, rule_category, rule_confidence
            return doc_type, category, max(rule_confidence, min(0.95, confidence))
        except Exception as exc:
            logger.info("Cheap classifier fallback for %s: %s", relative, exc)
            return rule_doc_type, rule_category, rule_confidence

    def _extract_parties(self, text: str) -> list[str]:
        candidates = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9（）()·]{2,40}(?:公司|集团|律所|法院|仲裁委员会|合作社|个体工商户)", text)
        candidates += re.findall(r"(?:甲方|乙方|原告|被告|申请人|被申请人)[:：\s]*([\u4e00-\u9fa5A-Za-z0-9（）()·]{2,40})", text)
        return _unique(candidates, limit=10)

    def _extract_dates(self, text: str) -> list[str]:
        patterns = [
            r"\d{4}年\d{1,2}月\d{1,2}日",
            r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}",
            r"\d{4}年\d{1,2}月",
        ]
        matches: list[str] = []
        for pattern in patterns:
            matches += re.findall(pattern, text)
        return _unique(matches, limit=12)

    def _extract_amounts(self, text: str) -> list[str]:
        return _unique(re.findall(r"(?:人民币|¥|RMB)?\s*[0-9][0-9,，]*(?:\.[0-9]+)?\s*(?:万元|元)", text), limit=12)

    async def _persist_case_file(self, job: Import_jobs, parsed: ParsedZipFile) -> Case_files:
        row = Case_files(
            user_id=job.user_id,
            import_job_id=job.id,
            file_id=parsed.file_id,
            original_name=parsed.original_name,
            relative_path=parsed.relative_path,
            storage_path=parsed.storage_path,
            mime_type=parsed.mime_type,
            file_hash=parsed.file_hash,
            size_bytes=parsed.size_bytes,
            page_count=parsed.page_count,
            text_extracted=parsed.text_extracted,
            ocr_required=parsed.ocr_required,
            text_excerpt=parsed.text_excerpt,
            parsed_text=parsed.parsed_text,
            doc_type=parsed.doc_type,
            evidence_category=parsed.evidence_category,
            confidence=parsed.confidence,
            parties_detected=_json_dumps(parsed.parties),
            dates_detected=_json_dumps(parsed.dates),
            amounts_detected=_json_dumps(parsed.amounts),
            manual_override=False,
            processing_status=parsed.processing_status,
            quarantine_reason=parsed.quarantine_reason,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    def _cluster_files(self, files: list[ParsedZipFile], *, upload_mode: str) -> list[dict[str, Any]]:
        usable = [item for item in files if item.processing_status not in {"quarantined", "duplicate"}]
        if not usable:
            return []
        if upload_mode == "single_case":
            return [self._build_cluster("cluster_001", usable, confidence=0.95, reason="用户选择单案件材料包")]

        by_top_folder: dict[str, list[ParsedZipFile]] = {}
        for item in usable:
            parts = [part for part in PurePosixPath(item.relative_path).parts if part]
            top = parts[0] if len(parts) > 1 else ""
            if top:
                by_top_folder.setdefault(top, []).append(item)

        if upload_mode == "multi_case" or len(by_top_folder) >= 2:
            clusters = []
            for idx, (folder, group) in enumerate(by_top_folder.items(), start=1):
                confidence = 0.88 if len(group) >= 2 else 0.68
                clusters.append(self._build_cluster(f"cluster_{idx:03d}", group, confidence=confidence, reason=f"按文件夹“{folder}”聚类"))
            loose = [item for item in usable if not PurePosixPath(item.relative_path).parent.parts]
            if loose:
                clusters.append(self._build_cluster(f"cluster_{len(clusters) + 1:03d}", loose, confidence=0.62, reason="根目录散落文件，需人工确认"))
            return clusters

        return [self._build_cluster("cluster_001", usable, confidence=0.78 if upload_mode == "auto" else 0.95, reason="未发现清晰多案件结构，按单案件候选处理")]

    def _build_cluster(self, cluster_id: str, files: list[ParsedZipFile], *, confidence: float, reason: str) -> dict[str, Any]:
        parties = _unique([party for item in files for party in item.parties], limit=6)
        amounts = [amount for item in files for amount in item.amounts]
        case_number = self._extract_case_number("\n".join([item.relative_path + "\n" + item.text_excerpt for item in files]))
        suggested = self._suggest_case_name(files, parties, case_number)
        return {
            "cluster_id": cluster_id,
            "suggested_case_name": suggested,
            "confidence": round(confidence, 2),
            "main_parties": parties,
            "case_number": case_number,
            "amounts": _unique(amounts, limit=5),
            "reason": reason,
            "file_ids": [item.file_id for item in files],
            "file_count": len(files),
            "needs_human_review": confidence < 0.85,
        }

    def _extract_case_number(self, text: str) -> Optional[str]:
        match = re.search(r"（?\(?\d{4}[）)]?[\u4e00-\u9fa5]{1,6}\d{2,6}(?:民初|民终|执|仲|民申)?\d*号", text)
        return match.group(0) if match else None

    def _suggest_case_name(self, files: list[ParsedZipFile], parties: list[str], case_number: Optional[str]) -> str:
        if len(parties) >= 2:
            cause = self._guess_cause(files)
            return f"{parties[0]}与{parties[1]}{cause}"
        top_names = [PurePosixPath(item.relative_path).parts[0] for item in files if len(PurePosixPath(item.relative_path).parts) > 1]
        if top_names:
            return _unique(top_names, limit=1)[0]
        return case_number or "待确认案件"

    def _guess_cause(self, files: list[ParsedZipFile]) -> str:
        text = "\n".join(item.relative_path + "\n" + item.text_excerpt for item in files)
        if "租赁" in text:
            return "租赁合同纠纷"
        if "借款" in text or "欠款" in text:
            return "民间借贷/借款纠纷"
        if "买卖" in text or "货款" in text:
            return "买卖合同纠纷"
        if "劳动" in text or "工资" in text:
            return "劳动争议"
        return "民事纠纷"

    async def _create_case_from_cluster(
        self,
        *,
        user_id: str,
        cluster: dict[str, Any],
        parsed_files: list[ParsedZipFile],
    ) -> int:
        selected = [item for item in parsed_files if item.file_id in set(cluster.get("file_ids") or [])]
        if not selected:
            raise ValueError("确认分组没有可用文件")
        parties = cluster.get("main_parties") or _unique([party for item in selected for party in item.parties], limit=6)
        amounts = [amount for item in selected for amount in item.amounts]
        dates = _unique([date for item in selected for date in item.dates], limit=10)
        missing = self._case_missing_info(parties, selected)
        amount = _amount_to_float(amounts[0]) if amounts else None
        case = Cases(
            user_id=user_id,
            title=cluster.get("suggested_case_name") or "待确认案件",
            case_type="民事",
            stage="材料整理",
            client_name=parties[0] if parties else None,
            opposing_party=parties[1] if len(parties) > 1 else None,
            amount=amount,
            summary=self._build_case_summary(cluster, selected, dates, amounts),
            dispute_focus=self._guess_dispute_focus(selected),
            claims="【待补充：诉讼请求/仲裁请求】",
            legal_basis="《中华人民共和国民事诉讼法》第一百二十三条、第一百二十四条；《最高人民法院关于民事诉讼证据的若干规定》第十九条。",
            missing_materials="\n".join(missing),
            next_steps="确认案件分组；补齐当事人身份信息；核验证据原件；确认请求和管辖；生成证据目录草案。",
            risk_level="中",
            material_count=len(selected),
            evidence_completeness="中" if any(item.confidence >= 0.7 for item in selected) else "低",
        )
        self.db.add(case)
        await self.db.commit()
        await self.db.refresh(case)

        for idx, party in enumerate(parties[:6], start=1):
            self.db.add(
                Case_parties(
                    user_id=user_id,
                    case_id=case.id,
                    name=party,
                    party_type="委托方/原告候选" if idx == 1 else "对方/被告候选" if idx == 2 else "相关主体",
                    identity_type="法人或其他组织" if any(word in party for word in ("公司", "集团", "合作社")) else "待核实",
                )
            )

        evidence_sequence = 1
        material_sequence = 1
        fact_sequence = 1
        for file_item in selected:
            material_no = f"E-{evidence_sequence:03d}" if self._is_evidence_file(file_item) else f"M-{material_sequence:03d}"
            material_sequence += 1
            proof_purpose = self._proof_purpose(file_item)
            material = Case_materials(
                user_id=user_id,
                case_id=case.id,
                material_no=material_no,
                title=file_item.original_name,
                material_type=file_item.evidence_category,
                file_url=file_item.storage_path,
                parsed_text=file_item.parsed_text,
                ocr_status="需OCR" if file_item.ocr_required else "已解析" if file_item.text_extracted else "仅元数据",
                source="ZIP案件包导入",
                is_evidence=self._is_evidence_file(file_item),
                proof_purpose=proof_purpose,
                page_refs=f"共{file_item.page_count}页" if file_item.page_count else "待确认页码/份数",
                related_facts="",
                authenticity_status="待核实原件",
                relevance_status="AI初步相关",
                legality_status="待核实取得方式",
                admissibility_risk=self._admissibility_risk(file_item),
                need_notarization=file_item.doc_type in {"communication", "image", "audio_video"},
                source_reliability="中",
            )
            self.db.add(material)
            await self.db.flush()

            if self._is_evidence_file(file_item):
                evidence_id = f"E{evidence_sequence:03d}"
                self.db.add(
                    Evidences(
                        user_id=user_id,
                        case_id=case.id,
                        material_id=material.id,
                        evidence_no=evidence_id,
                        title=file_item.original_name,
                        evidence_type=file_item.evidence_category,
                        source="当事人提供/ZIP导入",
                        proof_purpose=proof_purpose,
                        related_fact_ids="",
                        authenticity="待核实",
                        relevance="初步相关",
                        legality="待核实",
                        risk_note=self._admissibility_risk(file_item),
                        need_reinforcement=file_item.confidence < 0.75 or file_item.ocr_required,
                        status="AI建议，待律师确认",
                    )
                )
                self.db.add(
                    Evidence_items(
                        user_id=user_id,
                        case_id=case.id,
                        material_id=material.id,
                        evidence_id=evidence_id,
                        group_no=self._evidence_group(file_item),
                        sequence_no=evidence_sequence,
                        evidence_name=file_item.original_name,
                        evidence_source="当事人提供/ZIP案件包导入",
                        file_ids_json=_json_dumps([file_item.file_id]),
                        original_or_copy="扫描件/电子件，原件需律师核验",
                        page_range=f"共{file_item.page_count}页" if file_item.page_count else "页码/份数待确认",
                        proof_purpose=proof_purpose,
                        related_fact_ids_json=_json_dumps([]),
                        related_claim_ids_json=_json_dumps([]),
                        weakness=self._admissibility_risk(file_item),
                        confidence=file_item.confidence,
                        manual_status="AI建议，待律师确认",
                        needs_review=True,
                    )
                )
                evidence_sequence += 1

            fact = self._fact_from_file(file_item, fact_sequence, material_no)
            if fact:
                self.db.add(
                    Case_facts(
                        user_id=user_id,
                        case_id=case.id,
                        fact_no=f"F-{fact_sequence:03d}",
                        event_date=fact["date"],
                        fact_text=fact["text"],
                        persons="、".join(file_item.parties[:4]),
                        amount="、".join(file_item.amounts[:3]),
                        source_refs=material_no,
                        confidence=str(round(file_item.confidence, 2)),
                        verified_by_user=False,
                        contradiction_note="AI从材料中抽取，需律师复核",
                    )
                )
                self.db.add(
                    Fact_events(
                        user_id=user_id,
                        case_id=case.id,
                        event_id=f"F{fact_sequence:03d}",
                        event_date=fact["date"],
                        date_confidence=0.85 if fact["date"] != "待确认" else 0.3,
                        event_title=fact["title"],
                        event_detail=fact["text"],
                        legal_relevance=fact["relevance"],
                        evidence_refs_json=_json_dumps([{"evidence_id": material_no, "page": None, "quote": file_item.text_excerpt[:120]}]),
                        confidence=file_item.confidence,
                        needs_review=True,
                    )
                )
                fact_sequence += 1

            row_result = await self.db.execute(
                select(Case_files).where(Case_files.user_id == user_id, Case_files.file_id == file_item.file_id)
            )
            row = row_result.scalar_one_or_none()
            if row:
                row.case_id = case.id

        await self._ensure_seed_legal_sources()
        await self.db.commit()
        return case.id

    def _parsed_file_from_row(self, row: Case_files) -> ParsedZipFile:
        return ParsedZipFile(
            file_id=row.file_id,
            original_name=row.original_name,
            relative_path=row.relative_path or row.original_name,
            storage_path=row.storage_path or "",
            mime_type=row.mime_type or "application/octet-stream",
            file_hash=row.file_hash or "",
            size_bytes=row.size_bytes or 0,
            page_count=row.page_count,
            text_extracted=bool(row.text_extracted),
            ocr_required=bool(row.ocr_required),
            parsed_text=row.parsed_text or "",
            text_excerpt=row.text_excerpt or "",
            doc_type=row.doc_type or "other",
            evidence_category=row.evidence_category or "未分类/低置信材料",
            confidence=row.confidence or 0.0,
            parties=_json_loads(row.parties_detected, []),
            dates=_json_loads(row.dates_detected, []),
            amounts=_json_loads(row.amounts_detected, []),
            processing_status=row.processing_status or "metadata_only",
            quarantine_reason=row.quarantine_reason,
        )

    def _case_missing_info(self, parties: list[str], files: list[ParsedZipFile]) -> list[str]:
        missing = []
        if len(parties) < 2:
            missing.append("双方当事人完整名称、证件号/统一社会信用代码、住所和联系方式")
        missing.extend(["诉讼请求或仲裁请求", "受诉法院/仲裁机构及管辖依据", "证据原件/复印件状态", "催告、送达或解除通知凭证"])
        if not any(item.doc_type == "contract" for item in files):
            missing.append("基础合同/协议或法律关系成立材料")
        return missing

    def _build_case_summary(self, cluster: dict[str, Any], files: list[ParsedZipFile], dates: list[str], amounts: list[str]) -> str:
        return "\n".join(
            [
                f"系统从 ZIP 案件包识别出 {len(files)} 份材料，建议案件名称：{cluster.get('suggested_case_name')}。",
                f"聚类理由：{cluster.get('reason')}；置信度：{cluster.get('confidence')}。",
                f"检测到关键日期：{'、'.join(dates[:6]) or '待补充'}。",
                f"检测到金额线索：{'、'.join(amounts[:4]) or '待补充'}。",
                "本概览由 AI 自动生成，案件分组、证据编号、证明目的和诉讼请求需律师确认。",
            ]
        )

    def _guess_dispute_focus(self, files: list[ParsedZipFile]) -> str:
        doc_types = {item.doc_type for item in files}
        focuses = []
        if "contract" in doc_types:
            focuses.append("合同关系是否成立及主要权利义务")
        if "payment" in doc_types:
            focuses.append("付款、欠款或损失金额如何计算")
        if "communication" in doc_types:
            focuses.append("催告、通知、协商记录能否证明违约及送达")
        if not focuses:
            focuses.append("案件基础事实和证据链需进一步确认")
        return "\n".join(focuses)

    def _is_evidence_file(self, item: ParsedZipFile) -> bool:
        return item.processing_status not in {"quarantined", "duplicate"} and not item.evidence_category.startswith("未分类")

    def _proof_purpose(self, item: ParsedZipFile) -> str:
        mapping = {
            "contract": "证明双方基础法律关系成立、主要权利义务、履行期限、付款/违约责任等约定。",
            "payment": "证明款项支付、欠付、往来流水或损失金额形成情况。",
            "communication": "证明双方沟通、催告、通知、对方确认或争议形成过程。",
            "identity": "证明当事人主体资格、身份信息、授权关系或代理权限。",
            "procedure": "证明既有诉讼/仲裁程序、案件进展或裁判/调解结果。",
            "performance": "证明交付、验收、收货、履行过程及是否存在违约。",
            "damage": "证明损失发生、损失范围、维修评估鉴定或争议后果。",
        }
        return mapping.get(item.doc_type, f"证明与本案相关的{item.evidence_category}事实，具体证明目的待律师确认。")

    def _admissibility_risk(self, item: ParsedZipFile) -> str:
        risks = []
        if item.ocr_required:
            risks.append("扫描/图片材料需核验 OCR 准确性")
        if item.doc_type in {"communication", "image", "audio_video"}:
            risks.append("电子证据需保留原始载体，必要时做公证/保全")
        if item.confidence < 0.75:
            risks.append("分类置信度偏低，需人工复核")
        return "；".join(risks) or "需核验证据原件、来源和完整性"

    def _evidence_group(self, item: ParsedZipFile) -> str:
        if item.doc_type == "contract":
            return "第一组：证明基础法律关系成立及主要约定"
        if item.doc_type == "payment":
            return "第二组：证明付款、欠款或损失金额"
        if item.doc_type == "communication":
            return "第三组：证明沟通、催告、通知和对方确认"
        if item.doc_type == "identity":
            return "主体身份材料组"
        return "其他证据组"

    def _fact_from_file(self, item: ParsedZipFile, sequence: int, evidence_no: str) -> Optional[dict[str, str]]:
        if not self._is_evidence_file(item):
            return None
        date = item.dates[0] if item.dates else "待确认"
        title = f"材料显示：{item.original_name}"
        if item.doc_type == "contract":
            title = "双方形成基础法律关系"
        elif item.doc_type == "payment":
            title = "出现款项往来或付款线索"
        elif item.doc_type == "communication":
            title = "存在沟通、催告或通知线索"
        detail = item.text_excerpt[:240] if item.text_excerpt else f"系统根据文件名和类型识别该材料为{item.evidence_category}。"
        return {
            "date": date,
            "title": title,
            "text": f"{title}：{detail}【来源：{evidence_no}】",
            "relevance": self._proof_purpose(item),
        }

    async def _ensure_seed_legal_sources(self) -> None:
        for item in LAW_SOURCES:
            result = await self.db.execute(select(Legal_sources).where(Legal_sources.title == item["title"]))
            if result.scalar_one_or_none():
                continue
            self.db.add(
                Legal_sources(
                    source_type=item["source_type"],
                    title=item["title"],
                    code_ref=item["code_ref"],
                    content_snippet=item["summary"],
                    jurisdiction="中国大陆",
                    source_name=item["title"],
                    article_no=item["code_ref"],
                    legal_effect_level=item["legal_effect_level"],
                    effective_status="现行有效/需上线前复核",
                    summary=item["summary"],
                    verified=item["verified"],
                )
            )


class CaseDraftingService:
    """Generate evidence catalogs and civil complaints from case workspace data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_workspace(self, case_id: int, user_id: str) -> dict[str, Any]:
        case = await self._get_case(case_id, user_id)
        materials = (await self.db.execute(select(Case_materials).where(Case_materials.case_id == case_id, Case_materials.user_id == user_id).order_by(Case_materials.id))).scalars().all()
        facts = (await self.db.execute(select(Case_facts).where(Case_facts.case_id == case_id, Case_facts.user_id == user_id).order_by(Case_facts.event_date, Case_facts.id))).scalars().all()
        parties = (await self.db.execute(select(Case_parties).where(Case_parties.case_id == case_id, Case_parties.user_id == user_id).order_by(Case_parties.id))).scalars().all()
        evidence_items = (await self.db.execute(select(Evidence_items).where(Evidence_items.case_id == case_id, Evidence_items.user_id == user_id).order_by(Evidence_items.sequence_no, Evidence_items.id))).scalars().all()
        claims = (await self.db.execute(select(Claims).where(Claims.case_id == case_id, Claims.user_id == user_id).order_by(Claims.claim_no, Claims.id))).scalars().all()
        return {"case": case, "materials": materials, "facts": facts, "parties": parties, "evidence_items": evidence_items, "claims": claims}

    async def generate_evidence_catalog(self, *, case_id: int, user_id: str) -> dict[str, Any]:
        workspace = await self.load_workspace(case_id, user_id)
        evidence_items = workspace["evidence_items"] or self._evidence_items_from_materials(workspace["materials"])
        missing = []
        rows = []
        for idx, item in enumerate(evidence_items, start=1):
            row = self._evidence_row(item, idx)
            rows.append(row)
            if not row["proof_purpose"] or "待" in row["proof_purpose"]:
                missing.append(f"{row['evidence_no']} 证明目的需具体化")
            if "待确认" in row["page_range"]:
                missing.append(f"{row['evidence_no']} 页码/份数需确认")
        markdown = self._render_evidence_catalog_markdown(workspace["case"], rows, missing)
        qa = self._qa_gate("证据目录", missing, rows)
        document = await self._persist_document(
            user_id=user_id,
            case_id=case_id,
            doc_type="证据目录",
            title=f"证据目录 - {workspace['case'].title}",
            content=markdown,
            content_json={"rows": rows, "missing_evidence": missing},
            generation_plan={"source": "case_workspace", "agent": "evidence_catalog_drafting"},
            evidence_citations=[{"evidence_id": row["evidence_no"], "evidence_name": row["evidence_name"]} for row in rows],
            legal_citations=[],
            qa_report=qa,
            status="待律师复核",
        )
        return {"success": True, "document_id": document.id, "document": self._serialize_document(document), "qa_report": qa}

    async def generate_civil_complaint(self, *, case_id: int, user_id: str, force_draft: bool = True) -> dict[str, Any]:
        workspace = await self.load_workspace(case_id, user_id)
        preflight = self.preflight_civil_complaint(workspace)
        if preflight["blocking"] and not force_draft:
            return {
                "success": False,
                "requires_plan_mode": True,
                "preflight": preflight,
                "message": "起诉状缺少关键字段，请先进入 Plan Mode 追问。",
            }
        content, evidence_citations, legal_citations = await self._render_civil_complaint(workspace, preflight)
        qa = self._qa_gate("民事起诉状", preflight["missing_required"], evidence_citations)
        document = await self._persist_document(
            user_id=user_id,
            case_id=case_id,
            doc_type="民事起诉状",
            title=f"民事起诉状 - {workspace['case'].title}",
            content=content,
            content_json={"preflight": preflight},
            generation_plan={"source": "case_workspace", "agent": "civil_complaint_drafting", "force_draft": force_draft},
            evidence_citations=evidence_citations,
            legal_citations=legal_citations,
            qa_report=qa,
            status="草稿-待补充" if preflight["blocking"] else "草稿-待律师复核",
        )
        return {
            "success": True,
            "requires_plan_mode": preflight["blocking"],
            "document_id": document.id,
            "document": self._serialize_document(document),
            "preflight": preflight,
            "qa_report": qa,
        }

    def preflight_civil_complaint(self, workspace: dict[str, Any]) -> dict[str, Any]:
        case: Cases = workspace["case"]
        materials: list[Case_materials] = workspace["materials"]
        facts: list[Case_facts] = workspace["facts"]
        missing: list[str] = []
        warnings: list[str] = []

        if not case.client_name:
            missing.append("原告基本信息")
        if not case.opposing_party:
            missing.append("被告基本信息")
        if not case.claims or "待补充" in case.claims:
            missing.append("明确诉讼请求")
        if not facts:
            missing.append("事实与理由")
        if not any(item.is_evidence for item in materials):
            missing.append("证据和证据来源")
        if not (case.court_or_arbitration or case.jurisdiction):
            missing.append("受诉法院/管辖依据")
        if case.legal_basis and "仲裁" in case.legal_basis and "法院" in (case.court_or_arbitration or ""):
            warnings.append("存在仲裁相关线索，需确认是否有有效仲裁条款。")
        unsupported_facts = [fact.fact_no or str(fact.id) for fact in facts if not fact.source_refs]
        if unsupported_facts:
            warnings.append(f"{len(unsupported_facts)} 项事实缺少证据来源，将在草稿中标注待核实。")
        return {
            "blocking": bool(missing),
            "missing_required": missing,
            "warnings": warnings,
            "checks": {
                "party_info": not any(field in missing for field in ("原告基本信息", "被告基本信息")),
                "claims_clear": "明确诉讼请求" not in missing,
                "facts_present": "事实与理由" not in missing,
                "evidence_present": "证据和证据来源" not in missing,
                "court_present": "受诉法院/管辖依据" not in missing,
            },
            "plan_mode_recommended": bool(missing or warnings),
        }

    async def _get_case(self, case_id: int, user_id: str) -> Cases:
        result = await self.db.execute(select(Cases).where(Cases.id == case_id, Cases.user_id == user_id))
        case = result.scalar_one_or_none()
        if not case:
            raise ValueError("Case not found")
        return case

    def _evidence_items_from_materials(self, materials: list[Case_materials]) -> list[dict[str, Any]]:
        rows = []
        for idx, material in enumerate([item for item in materials if item.is_evidence], start=1):
            rows.append(
                {
                    "evidence_no": material.material_no or f"E-{idx:03d}",
                    "evidence_name": material.title,
                    "evidence_source": material.source or "当事人提供",
                    "page_range": material.page_refs or "页码/份数待确认",
                    "original_or_copy": "扫描件/复印件，原件待核验",
                    "proof_purpose": material.proof_purpose or "待补充具体证明目的",
                    "related_facts": material.related_facts or "待关联事实",
                    "related_claims": "待关联诉讼请求/争议焦点",
                    "remark": material.admissibility_risk or "待律师复核",
                }
            )
        return rows

    def _evidence_row(self, item: Evidence_items | dict[str, Any], idx: int) -> dict[str, Any]:
        if isinstance(item, dict):
            return item
        return {
            "evidence_no": item.evidence_id or f"E{idx:03d}",
            "evidence_name": item.evidence_name,
            "evidence_source": item.evidence_source or "当事人提供",
            "page_range": item.page_range or "页码/份数待确认",
            "original_or_copy": item.original_or_copy or "扫描件/复印件，原件待核验",
            "proof_purpose": item.proof_purpose or "待补充具体证明目的",
            "related_facts": "、".join(_json_loads(item.related_fact_ids_json, [])) or "待关联事实",
            "related_claims": "、".join(_json_loads(item.related_claim_ids_json, [])) or "待关联请求/争议焦点",
            "remark": item.weakness or "待律师复核",
        }

    def _render_evidence_catalog_markdown(self, case: Cases, rows: list[dict[str, Any]], missing: list[str]) -> str:
        lines = [
            "# 证据目录",
            "",
            f"提交人：{case.client_name or '【待补充：提交人】'}",
            f"案由/案件名称：{case.title}",
            "提交日期：【待补充：提交日期】",
            "",
            "| 序号 | 证据名称 | 证据来源 | 页码/份数 | 原件/复印件 | 证明目的 | 对应事实/请求 | 备注 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for idx, row in enumerate(rows, start=1):
            lines.append(
                "| {idx} | {name} | {source} | {page} | {copy} | {purpose} | {related} | {remark} |".format(
                    idx=idx,
                    name=row["evidence_name"],
                    source=row["evidence_source"],
                    page=row["page_range"],
                    copy=row["original_or_copy"],
                    purpose=row["proof_purpose"],
                    related=row["related_facts"] or row["related_claims"],
                    remark=row["remark"],
                )
            )
        if missing:
            lines.extend(["", "## 待补强事项"])
            lines.extend(f"- {item}" for item in missing)
        lines.extend(["", "说明：本证据目录为 AI 草稿，证据原件、页码、证明目的和提交份数需由律师复核。"])
        return "\n".join(lines)

    async def _render_civil_complaint(
        self,
        workspace: dict[str, Any],
        preflight: dict[str, Any],
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        case: Cases = workspace["case"]
        facts: list[Case_facts] = workspace["facts"]
        materials: list[Case_materials] = workspace["materials"]
        evidences = [item for item in materials if item.is_evidence]
        legal_citations = await self._legal_citations_for_complaint()
        plaintiff = case.client_name or "【待补充：原告姓名/名称、证件号、住所、联系方式】"
        defendant = case.opposing_party or "【待补充：被告姓名/名称、证件号/统一社会信用代码、住所、联系方式】"
        court = case.court_or_arbitration or case.jurisdiction or "【待补充：受诉法院】"
        claims = self._split_lines(case.claims) or ["【待补充：明确诉讼请求、金额及计算方式】"]
        fact_lines = []
        evidence_citations: list[dict[str, Any]] = []
        if facts:
            for fact in facts:
                source = fact.source_refs or "【待补充：证据来源】"
                line = f"{fact.event_date or '【待补充：日期】'}，{fact.fact_text}（证据来源：{source}）。"
                fact_lines.append(line)
                evidence_citations.append({"sentence": line, "evidence_ids": [source], "fact_ids": [fact.fact_no or str(fact.id)]})
        else:
            fact_lines.append("【待补充：按时间顺序列明合同成立、履行、违约、催告、损失形成等事实，并逐项关联证据】。")

        evidence_lines = [
            f"{idx}. {item.material_no or f'E-{idx:03d}'}：{item.title}，来源：{item.source or '当事人提供'}，证明目的：{item.proof_purpose or '【待补充：证明目的】'}。"
            for idx, item in enumerate(evidences, start=1)
        ] or ["【待补充：证据名称、来源、页码/份数及证明目的】"]
        lines = [
            "# 民事起诉状",
            "",
            f"原告：{plaintiff}",
            "",
            f"被告：{defendant}",
            "",
            "## 诉讼请求",
        ]
        lines.extend(f"{idx}. {claim}" for idx, claim in enumerate(claims, start=1))
        lines.extend(["", "## 事实与理由"])
        lines.extend(fact_lines)
        lines.extend(
            [
                "",
                "依据《中华人民共和国民事诉讼法》第一百二十三条、第一百二十四条等规定，原告依法提起诉讼。上述事实和请求仍需结合证据原件、管辖依据、诉讼时效和金额计算由律师复核。",
                "",
                "## 证据和证据来源",
            ]
        )
        lines.extend(evidence_lines)
        if preflight["missing_required"] or preflight["warnings"]:
            lines.extend(["", "## 待补充/风险提示"])
            lines.extend(f"- 【待补充】{item}" for item in preflight["missing_required"])
            lines.extend(f"- {item}" for item in preflight["warnings"])
        lines.extend(
            [
                "",
                f"此致",
                f"{court}",
                "",
                f"具状人：{case.client_name or '【待补充：签名/盖章】'}",
                "日期：【待补充：提交日期】",
                "",
                "附件：",
                f"1. 本起诉状副本 {self._defendant_copy_count(defendant)} 份；",
                "2. 证据材料及证据目录；",
                "3. 当事人主体资格材料。",
                "",
                "声明：本草稿由 AI 基于案件工作台材料生成，不构成正式法律意见，提交前必须由执业律师复核。",
            ]
        )
        return "\n".join(lines), evidence_citations, legal_citations

    async def _legal_citations_for_complaint(self) -> list[dict[str, Any]]:
        await CaseImportService(self.db)._ensure_seed_legal_sources()
        await self.db.commit()
        result = await self.db.execute(select(Legal_sources).where(Legal_sources.title.in_([item["title"] for item in LAW_SOURCES])))
        sources = result.scalars().all()
        return [
            {
                "sentence": "起诉状法定要素和证据目录规则依据",
                "legal_source_ids": [str(item.id)],
                "source_name": item.title,
                "source_type": item.source_type,
                "authority_level": item.legal_effect_level or "待核验",
            }
            for item in sources
        ]

    def _defendant_copy_count(self, defendant: str) -> str:
        if "【待补充" in defendant:
            return "【待补充：按被告人数】"
        return "1"

    def _split_lines(self, value: Optional[str]) -> list[str]:
        return [item.strip() for item in re.split(r"\n|；|;", value or "") if item.strip() and "待补充" not in item.strip()]

    def _qa_gate(self, doc_type: str, missing: list[str], citations: list[Any]) -> dict[str, Any]:
        issues = []
        if missing:
            issues.extend(f"缺少必填字段：{item}" for item in missing)
        if doc_type in {"民事起诉状", "证据目录"} and not citations:
            issues.append("缺少证据引用或证据目录项")
        return {
            "pass": not issues,
            "severity": "high" if missing else "medium" if issues else "low",
            "issues": issues,
            "required_fixes": missing,
            "optional_improvements": ["核验证据原件/原始载体", "核验法律依据现行有效", "由执业律师复核后提交"],
            "human_review_required": True,
        }

    async def _persist_document(
        self,
        *,
        user_id: str,
        case_id: int,
        doc_type: str,
        title: str,
        content: str,
        content_json: dict[str, Any],
        generation_plan: dict[str, Any],
        evidence_citations: list[dict[str, Any]],
        legal_citations: list[dict[str, Any]],
        qa_report: dict[str, Any],
        status: str,
    ) -> Generated_documents:
        doc = Generated_documents(
            user_id=user_id,
            case_id=case_id,
            doc_type=doc_type,
            title=title,
            content=content,
            content_markdown=content,
            content_json=_json_dumps(content_json),
            generation_plan_json=_json_dumps(generation_plan),
            evidence_citations_json=_json_dumps(evidence_citations),
            legal_citations_json=_json_dumps(legal_citations),
            qa_report_json=_json_dumps(qa_report),
            draft_label="AI草稿-需律师复核",
            input_data_json=_json_dumps(generation_plan),
            citation_map=_json_dumps({"evidence": evidence_citations, "legal": legal_citations}),
            status=status,
            generated_by="legal_agent_team",
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    def _serialize_document(self, doc: Generated_documents) -> dict[str, Any]:
        return {
            "id": doc.id,
            "case_id": doc.case_id,
            "doc_type": doc.doc_type,
            "title": doc.title,
            "content": doc.content,
            "draft_label": doc.draft_label,
            "status": doc.status,
            "generated_by": doc.generated_by,
            "content_json": _json_loads(doc.content_json, {}),
            "generation_plan": _json_loads(doc.generation_plan_json, {}),
            "evidence_citations": _json_loads(doc.evidence_citations_json, []),
            "legal_citations": _json_loads(doc.legal_citations_json, []),
            "qa_report": _json_loads(doc.qa_report_json, {}),
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from models.legal_knowledge import LegalKnowledgeArticle
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "legal_knowledge" / "contract_law_seed.json"


class LegalKnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def default_seed_path() -> Path:
        return DEFAULT_SEED_PATH

    @staticmethod
    def _json_list(value: Any) -> str:
        if value is None:
            return "[]"
        if isinstance(value, str):
            return json.dumps([value], ensure_ascii=False)
        if isinstance(value, Iterable):
            return json.dumps([str(item) for item in value if str(item).strip()], ensure_ascii=False)
        return "[]"

    @staticmethod
    def _load_json_list(value: Optional[str]) -> List[str]:
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [str(item) for item in parsed if str(item).strip()]

    @staticmethod
    def _checksum(record: Dict[str, Any]) -> str:
        payload = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize(value: Optional[str]) -> str:
        if not value:
            return ""
        return re.sub(r"\s+", "", value).lower()

    @staticmethod
    def _query_terms(query: str) -> List[str]:
        normalized = LegalKnowledgeService._normalize(query)
        terms = [normalized] if normalized else []
        terms.extend(
            LegalKnowledgeService._normalize(part)
            for part in re.split(r"[,\s，。；;、/|]+", query or "")
            if LegalKnowledgeService._normalize(part)
        )
        seen = set()
        deduped = []
        for term in terms:
            if term and term not in seen:
                seen.add(term)
                deduped.append(term)
        return deduped

    @staticmethod
    def _to_article_dict(article: LegalKnowledgeArticle) -> Dict[str, Any]:
        return {
            "id": article.id,
            "source_id": article.source_id,
            "source_name": article.source_name,
            "article_number": article.article_number,
            "article_title": article.article_title,
            "source_type": article.source_type,
            "authority_level": article.authority_level,
            "jurisdiction": article.jurisdiction,
            "legal_domain": article.legal_domain,
            "topics": LegalKnowledgeService._load_json_list(article.topics_json),
            "keywords": LegalKnowledgeService._load_json_list(article.keywords_json),
            "text": article.text,
            "summary": article.summary,
            "legal_effect_note": article.legal_effect_note,
            "source_url": article.source_url,
            "official_source_url": article.official_source_url,
            "effective_status": article.effective_status,
            "verification_status": article.verification_status,
            "published_at": article.published_at,
            "effective_at": article.effective_at,
            "last_verified_at": article.last_verified_at,
            "updated_at": article.updated_at,
        }

    @staticmethod
    def _seed_to_columns(record: Dict[str, Any], checksum: str, now: datetime) -> Dict[str, Any]:
        return {
            "source_id": record["source_id"],
            "source_name": record["source_name"],
            "article_number": record["article_number"],
            "article_title": record.get("article_title"),
            "source_type": record.get("source_type", "法律"),
            "authority_level": record.get("authority_level", "裁判依据"),
            "jurisdiction": record.get("jurisdiction", "中国大陆"),
            "legal_domain": record.get("legal_domain", "合同审查"),
            "topics_json": LegalKnowledgeService._json_list(record.get("topics")),
            "keywords_json": LegalKnowledgeService._json_list(record.get("keywords")),
            "text": record["text"],
            "summary": record.get("summary"),
            "legal_effect_note": record.get("legal_effect_note"),
            "source_url": record.get("source_url"),
            "official_source_url": record.get("official_source_url") or record.get("source_url"),
            "effective_status": record.get("effective_status", "现行有效"),
            "verification_status": record.get("verification_status", "已校验"),
            "published_at": record.get("published_at"),
            "effective_at": record.get("effective_at"),
            "last_verified_at": now,
            "last_seeded_at": now,
            "checksum": checksum,
        }

    @staticmethod
    def load_seed_records(seed_path: Optional[str | Path] = None) -> tuple[Path, List[Dict[str, Any]]]:
        path = Path(seed_path) if seed_path else DEFAULT_SEED_PATH
        if not path.is_absolute():
            path = Path.cwd() / path
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        records = payload.get("records", payload if isinstance(payload, list) else [])
        if not isinstance(records, list):
            raise ValueError("Legal knowledge seed must contain a records list")
        return path, records

    async def upsert_seed_records(self, seed_path: Optional[str | Path] = None, dry_run: bool = False) -> Dict[str, Any]:
        path, records = self.load_seed_records(seed_path)
        inserted = 0
        updated = 0
        skipped = 0
        errors: List[str] = []
        now = datetime.now()

        required = {"source_id", "source_name", "article_number", "text"}
        for index, record in enumerate(records):
            missing = sorted(required - set(record.keys()))
            if missing:
                errors.append(f"record[{index}] missing required fields: {', '.join(missing)}")
                continue

            checksum = self._checksum(record)
            existing_result = await self.db.execute(
                select(LegalKnowledgeArticle).where(LegalKnowledgeArticle.source_id == record["source_id"])
            )
            existing = existing_result.scalar_one_or_none()
            columns = self._seed_to_columns(record, checksum, now)

            if existing is None:
                inserted += 1
                if not dry_run:
                    self.db.add(LegalKnowledgeArticle(**columns))
                continue

            if existing.checksum == checksum:
                skipped += 1
                continue

            updated += 1
            if not dry_run:
                for key, value in columns.items():
                    setattr(existing, key, value)

        if not dry_run:
            await self.db.commit()

        return {
            "seed_path": str(path),
            "dry_run": dry_run,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "total_records": len(records),
            "errors": errors,
        }

    async def get_by_source_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        result = await self.db.execute(select(LegalKnowledgeArticle).where(LegalKnowledgeArticle.source_id == source_id))
        article = result.scalar_one_or_none()
        return self._to_article_dict(article) if article else None

    async def search(
        self,
        query: str,
        legal_domain: Optional[str] = None,
        topic: Optional[str] = None,
        source_type: Optional[str] = None,
        authority_level: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        statement = select(LegalKnowledgeArticle)
        if legal_domain:
            statement = statement.where(LegalKnowledgeArticle.legal_domain == legal_domain)
        if source_type:
            statement = statement.where(LegalKnowledgeArticle.source_type == source_type)
        if authority_level:
            statement = statement.where(LegalKnowledgeArticle.authority_level == authority_level)

        result = await self.db.execute(statement)
        articles = result.scalars().all()
        terms = self._query_terms(query)
        topic_norm = self._normalize(topic)
        scored: List[Dict[str, Any]] = []

        for article in articles:
            article_dict = self._to_article_dict(article)
            topics = article_dict["topics"]
            keywords = article_dict["keywords"]
            if topic_norm and all(topic_norm not in self._normalize(item) for item in topics + keywords):
                continue

            score, matched_terms = self._score_article(article_dict, terms)
            if query and score <= 0:
                continue
            item = dict(article_dict)
            item["relevance_score"] = score
            item["matched_terms"] = matched_terms
            scored.append(item)

        scored.sort(key=lambda item: (item["relevance_score"], item["source_id"]), reverse=True)
        items = scored[:limit]
        return {"query": query, "total": len(scored), "items": items}

    @classmethod
    def _score_article(cls, article: Dict[str, Any], terms: Sequence[str]) -> tuple[float, List[str]]:
        if not terms:
            return 1.0, []

        title_blob = cls._normalize("".join([article["source_name"], article["article_number"], article.get("article_title") or ""]))
        keyword_blob = cls._normalize(" ".join(article["keywords"]))
        topic_blob = cls._normalize(" ".join(article["topics"]))
        summary_blob = cls._normalize(article.get("summary") or "")
        text_blob = cls._normalize(article["text"])
        note_blob = cls._normalize(article.get("legal_effect_note") or "")
        matched: List[str] = []
        score = 0.0

        for term in terms:
            term_score = 0.0
            if term in title_blob:
                term_score += 18.0
            if term in keyword_blob:
                term_score += 14.0
            if term in topic_blob:
                term_score += 10.0
            if term in summary_blob:
                term_score += 7.0
            if term in text_blob:
                term_score += 5.0
            if term in note_blob:
                term_score += 4.0
            if term_score:
                matched.append(term)
                score += term_score

        return score, matched

    async def stats(self) -> Dict[str, Any]:
        total_result = await self.db.execute(select(func.count(LegalKnowledgeArticle.id)))
        total = total_result.scalar() or 0
        return {
            "total": total,
            "by_domain": await self._count_by(LegalKnowledgeArticle.legal_domain),
            "by_source": await self._count_by(LegalKnowledgeArticle.source_name),
            "by_status": await self._count_by(LegalKnowledgeArticle.effective_status),
        }

    async def _count_by(self, column) -> Dict[str, int]:
        result = await self.db.execute(select(column, func.count(LegalKnowledgeArticle.id)).group_by(column))
        return {str(row[0]): int(row[1]) for row in result.fetchall()}

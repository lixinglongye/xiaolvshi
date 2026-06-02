import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.database import db_manager  # noqa: E402
from models.legal_knowledge import LegalKnowledgeArticle  # noqa: F401, E402
from services.legal_knowledge import LegalKnowledgeService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed or refresh the local legal knowledge database.")
    parser.add_argument("--seed-path", default=None, help="Path to a legal knowledge JSON seed file.")
    parser.add_argument("--dry-run", action="store_true", help="Compute changes without writing to SQLite.")
    parser.add_argument("--watch", action="store_true", help="Run repeatedly; suitable for long-running schedulers.")
    parser.add_argument("--interval-hours", type=float, default=24.0, help="Interval used with --watch.")
    parser.add_argument("--no-log", action="store_true", help="Do not append logs/legal_knowledge_update.jsonl.")
    return parser.parse_args()


def append_update_log(summary: dict) -> None:
    log_dir = BACKEND_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "legal_knowledge_update.jsonl"
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")


async def run_once(args: argparse.Namespace) -> dict:
    await db_manager.init_db()
    await db_manager.create_tables()

    if not db_manager.async_session_maker:
        raise RuntimeError("Database session maker is not initialized")

    async with db_manager.async_session_maker() as session:
        service = LegalKnowledgeService(session)
        summary = await service.upsert_seed_records(seed_path=args.seed_path, dry_run=args.dry_run)
        summary["run_at"] = datetime.now().isoformat(timespec="seconds")
        summary["mode"] = "dry_run" if args.dry_run else "upsert"

    if not args.no_log:
        append_update_log(summary)

    return summary


async def main() -> None:
    args = parse_args()
    try:
        while True:
            summary = await run_once(args)
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
            if not args.watch:
                break
            await asyncio.sleep(max(args.interval_hours, 0.01) * 3600)
    finally:
        await db_manager.close_db()


if __name__ == "__main__":
    asyncio.run(main())

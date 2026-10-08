import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.workbook_import import import_workbook, read_workbook


def main() -> int:
    parser = argparse.ArgumentParser(description="Import dated harvest rows from the cleaned 2026 workbook.")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--apply", action="store_true", help="Write records. Without this flag, only inspect the workbook.")
    parser.add_argument("--database-url", help="Explicit PostgreSQL target, required with --apply.")
    args = parser.parse_args()
    if args.apply and not args.database_url:
        parser.error("--apply requires --database-url")
    try:
        plan = read_workbook(args.workbook)
        print(json.dumps(plan.summary(), indent=2))
        if not args.apply:
            print("Dry run: no database connection or writes.")
            return 0
        engine = create_engine(args.database_url)
        try:
            if engine.dialect.name != "postgresql":
                raise ValueError("The import target must be PostgreSQL")
            with Session(engine) as db, db.begin():
                result = import_workbook(db, plan)
            print(json.dumps(result, indent=2))
        finally:
            engine.dispose()
    except (OSError, ValueError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("Database import failed. No changes were committed. Check the connection and table setup.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

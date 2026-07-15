"""Import the existing SQLite/JSON account state into PostgreSQL once."""
import json
import os
import sqlite3
import sys

from database import session_scope
from models import AccountState


def read_legacy():
    sqlite_path = os.environ.get("SUDANA_DATABASE", "data/sudana.db")
    if os.path.exists(sqlite_path):
        connection = sqlite3.connect(sqlite_path)
        try:
            rows = connection.execute("SELECT username, data FROM users").fetchall()
            if rows:
                return {key: json.loads(payload) for key, payload in rows}
        finally:
            connection.close()
    if os.path.exists("data/users.json"):
        with open("data/users.json") as source:
            return json.load(source)
    return {}


def main():
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required for the PostgreSQL import.")
    if os.environ.get("IMPORT_LEGACY_ON_EMPTY", "").lower() not in {"1", "true", "yes"} and "--force" not in sys.argv:
        print("Legacy import skipped. Set IMPORT_LEGACY_ON_EMPTY=true for the first deployment.")
        return
    legacy = read_legacy()
    with session_scope() as db_session:
        existing = db_session.query(AccountState).count()
        if existing:
            print(f"Import skipped: PostgreSQL already contains {existing} account records.")
            return
        for key, payload in legacy.items():
            db_session.add(AccountState(user_key=key, payload=payload))
    print(f"Imported {len(legacy)} account records into PostgreSQL without modifying the source data.")


if __name__ == "__main__":
    main()

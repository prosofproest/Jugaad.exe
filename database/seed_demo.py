#!/usr/bin/env python3
"""
Seed script for AI-Based Early Pest and Disease project.
Applies `database/schema/02-demo-seed.sql` to populate clearly labelled demo data.

Usage:
    python3 database/seed_demo.py [--db-url postgresql://user:pass@host:5432/dbname]
"""

import argparse
import os
import sys

def run_seed(db_url: str):
    try:
        import psycopg2
    except ImportError:
        print("[!] psycopg2 is not installed. You can pipe the SQL file directly using psql:")
        print("    psql $DATABASE_URL -f database/schema/02-demo-seed.sql")
        return False

    seed_path = os.path.join(os.path.dirname(__file__), "schema", "02-demo-seed.sql")
    if not os.path.exists(seed_path):
        print(f"[!] Error: Seed file not found at {seed_path}")
        return False

    with open(seed_path, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    print(f"[*] Connecting to database to apply demo seed...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(seed_sql)
        conn.close()
        print("[+] Successfully seeded demo data!")
        return True
    except Exception as e:
        print(f"[!] Failed to seed database: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database with demo data (is_demo=true).")
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pest_disease"),
        help="PostgreSQL connection string (defaults to DATABASE_URL or localhost)",
    )
    args = parser.parse_args()
    success = run_seed(args.db_url)
    sys.exit(0 if success else 1)


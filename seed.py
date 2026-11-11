"""Root seed script for Asghi.
Seeds sample passages, questions across all difficulties, and users for all 4 roles.
Usage:
    python seed.py
"""
import sys
from asghi.seed import seed_database

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "asghi.db"
    seed_database(db_path=db_path)

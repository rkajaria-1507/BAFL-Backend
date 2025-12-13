import os
import sys

# Ensure backend package is importable
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

from src.db.database import engine
from src.db.models.archery import ArcherySession, ArcheryResult
from src.db.models.archery_tournament import (
    ArcheryTournamentCategory,
    ArcheryTournamentSession,
    ArcheryTournamentResult,
)


def migrate_archery_tables() -> None:
    print("Dropping archery tables (if they exist)...")
    ArcheryTournamentResult.__table__.drop(engine, checkfirst=True)
    ArcheryTournamentSession.__table__.drop(engine, checkfirst=True)
    # ArcheryTournamentCategory.__table__.drop(engine, checkfirst=True)
    # ArcheryResult.__table__.drop(engine, checkfirst=True)
    # ArcherySession.__table__.drop(engine, checkfirst=True)

    print("Creating archery tables with updated schema...")
    # ArcheryTournamentCategory.__table__.create(engine)
    ArcheryTournamentSession.__table__.create(engine)
    ArcheryTournamentResult.__table__.create(engine)
    # ArcherySession.__table__.create(engine)
    # ArcheryResult.__table__.create(engine)

    print("Archery tables migrated successfully.")


if __name__ == "__main__":
    migrate_archery_tables()

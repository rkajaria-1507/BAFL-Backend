from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.db.models.archery_tournament import (
    ArcheryTournamentCategory,
    ArcheryTournamentResult,
    ArcheryTournamentSession,
)


class ArcheryTournamentCategoryRepository:
    @staticmethod
    def create(db: Session, category: ArcheryTournamentCategory) -> ArcheryTournamentCategory:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_all(db: Session) -> List[ArcheryTournamentCategory]:
        stmt = select(ArcheryTournamentCategory).order_by(ArcheryTournamentCategory.name.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[ArcheryTournamentCategory]:
        stmt = select(ArcheryTournamentCategory).where(ArcheryTournamentCategory.id == category_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[ArcheryTournamentCategory]:
        stmt = select(ArcheryTournamentCategory).where(ArcheryTournamentCategory.name == name)
        return db.scalar(stmt)

    @staticmethod
    def delete(db: Session, category_id: int) -> bool:
        stmt = delete(ArcheryTournamentCategory).where(ArcheryTournamentCategory.id == category_id)
        result = db.execute(stmt)
        db.commit()
        return (result.rowcount or 0) > 0


class ArcheryTournamentSessionRepository:
    @staticmethod
    def create(db: Session, session: ArcheryTournamentSession) -> ArcheryTournamentSession:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_by_id(db: Session, session_id: int) -> Optional[ArcheryTournamentSession]:
        stmt = select(ArcheryTournamentSession).where(ArcheryTournamentSession.id == session_id)
        return db.scalar(stmt)

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ArcheryTournamentSession]:
        stmt = select(ArcheryTournamentSession).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())


class ArcheryTournamentResultRepository:
    @staticmethod
    def create_all(db: Session, results: List[ArcheryTournamentResult]) -> List[ArcheryTournamentResult]:
        db.add_all(results)
        db.commit()
        return results

    @staticmethod
    def get_by_session(db: Session, session_id: int) -> List[ArcheryTournamentResult]:
        stmt = select(ArcheryTournamentResult).where(ArcheryTournamentResult.session_id == session_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_student(db: Session, student_id: int) -> List[ArcheryTournamentResult]:
        stmt = select(ArcheryTournamentResult).where(ArcheryTournamentResult.student_id == student_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def delete_by_session(db: Session, session_id: int) -> None:
        db.execute(delete(ArcheryTournamentResult).where(ArcheryTournamentResult.session_id == session_id))
        db.commit()

    @staticmethod
    def delete_for_student_in_session(db: Session, session_id: int, student_id: int) -> None:
        db.execute(
            delete(ArcheryTournamentResult)
            .where(ArcheryTournamentResult.session_id == session_id)
            .where(ArcheryTournamentResult.student_id == student_id)
        )
        db.commit()

    @staticmethod
    def delete_by_student(db: Session, student_id: int) -> int:
        stmt = delete(ArcheryTournamentResult).where(ArcheryTournamentResult.student_id == student_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount or 0

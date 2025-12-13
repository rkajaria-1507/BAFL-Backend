from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from src.db.models.archery import ArcherySession, ArcheryResult

class ArcherySessionRepository:
    @staticmethod
    def create(db: Session, session: ArcherySession) -> ArcherySession:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_by_id(db: Session, session_id: int) -> Optional[ArcherySession]:
        return db.scalar(select(ArcherySession).where(ArcherySession.id == session_id))

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ArcherySession]:
        return list(db.scalars(select(ArcherySession).offset(skip).limit(limit)).all())

class ArcheryResultRepository:
    @staticmethod
    def create_all(db: Session, results: List[ArcheryResult]) -> List[ArcheryResult]:
        db.add_all(results)
        db.commit()
        return results

    @staticmethod
    def get_by_session(db: Session, session_id: int) -> List[ArcheryResult]:
        return list(db.scalars(select(ArcheryResult).where(ArcheryResult.session_id == session_id)).all())

    @staticmethod
    def get_by_student(db: Session, student_id: int) -> List[ArcheryResult]:
        stmt = select(ArcheryResult).where(ArcheryResult.student_id == student_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_session_and_student(db: Session, session_id: int, student_id: int) -> List[ArcheryResult]:
        stmt = (
            select(ArcheryResult)
            .where(ArcheryResult.session_id == session_id)
            .where(ArcheryResult.student_id == student_id)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def delete_by_session(db: Session, session_id: int) -> None:
        db.execute(delete(ArcheryResult).where(ArcheryResult.session_id == session_id))
        db.commit()

    @staticmethod
    def delete_for_student_in_session(db: Session, session_id: int, student_id: int) -> None:
        db.execute(
            delete(ArcheryResult)
            .where(ArcheryResult.session_id == session_id)
            .where(ArcheryResult.student_id == student_id)
        )
        db.commit()

    @staticmethod
    def delete_by_student(db: Session, student_id: int) -> int:
        stmt = delete(ArcheryResult).where(ArcheryResult.student_id == student_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount or 0

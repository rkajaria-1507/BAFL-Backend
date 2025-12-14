from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from src.db.models.physical_assessment import PhysicalAssessmentDetail

class PhysicalResultsRepository:
    @staticmethod
    def create(db: Session, result: PhysicalAssessmentDetail) -> PhysicalAssessmentDetail:
        db.add(result)
        db.commit()
        # No refresh needed
        return result

    @staticmethod
    def get_by_id(db: Session, result_id: int) -> Optional[PhysicalAssessmentDetail]:
        return db.scalar(select(PhysicalAssessmentDetail).where(PhysicalAssessmentDetail.id == result_id))

    @staticmethod
    def get_by_session(db: Session, session_id: int) -> List[PhysicalAssessmentDetail]:
        stmt = select(PhysicalAssessmentDetail).where(PhysicalAssessmentDetail.session_id == session_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_student(db: Session, student_id: int) -> List[PhysicalAssessmentDetail]:
        stmt = select(PhysicalAssessmentDetail).where(PhysicalAssessmentDetail.student_id == student_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_session_and_student(db: Session, session_id: int, student_id: int) -> Optional[PhysicalAssessmentDetail]:
        stmt = (
            select(PhysicalAssessmentDetail)
            .where(PhysicalAssessmentDetail.session_id == session_id)
            .where(PhysicalAssessmentDetail.student_id == student_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def update(db: Session, result: PhysicalAssessmentDetail, update_data: dict) -> PhysicalAssessmentDetail:
        for key, value in update_data.items():
            setattr(result, key, value)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def delete(db: Session, result: PhysicalAssessmentDetail) -> None:
        db.delete(result)
        db.commit()

    @staticmethod
    def delete_by_student(db: Session, student_id: int) -> int:
        stmt = delete(PhysicalAssessmentDetail).where(PhysicalAssessmentDetail.student_id == student_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount or 0

    @staticmethod
    def create_all(db: Session, results: List[PhysicalAssessmentDetail]) -> List[PhysicalAssessmentDetail]:
        db.add_all(results)
        db.commit()
        for result in results:
            db.refresh(result)
        return results

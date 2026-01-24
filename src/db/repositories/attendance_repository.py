"""
Repository layer for attendance data access.
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, and_, func

from src.db.models.attendance import (
    AttendanceSession,
    StudentAttendance,
    CoachAttendance,
    AttendanceStatus,
)


class AttendanceSessionRepository:
    """Repository for AttendanceSession operations."""

    @staticmethod
    def create(db: Session, session: AttendanceSession) -> AttendanceSession:
        """Create a new attendance session."""
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_by_id(db: Session, session_id: int) -> Optional[AttendanceSession]:
        """Get attendance session by ID."""
        return db.scalar(
            select(AttendanceSession).where(AttendanceSession.id == session_id)
        )

    @staticmethod
    def get_by_batch_and_date(
        db: Session, batch_id: int, session_date: date
    ) -> Optional[AttendanceSession]:
        """Get attendance session by batch ID and date."""
        return db.scalar(
            select(AttendanceSession).where(
                and_(
                    AttendanceSession.batch_id == batch_id,
                    AttendanceSession.date == session_date,
                )
            )
        )

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        batch_id: Optional[int] = None,
        school_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[AttendanceSession]:
        """Get all attendance sessions with optional filters."""
        stmt = select(AttendanceSession)

        if batch_id is not None:
            stmt = stmt.where(AttendanceSession.batch_id == batch_id)
        if school_id is not None:
            stmt = stmt.where(AttendanceSession.school_id == school_id)
        if start_date is not None:
            stmt = stmt.where(AttendanceSession.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(AttendanceSession.date <= end_date)

        stmt = stmt.order_by(AttendanceSession.date.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_coach(
        db: Session,
        coach_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AttendanceSession]:
        """Get attendance sessions marked by a specific coach."""
        stmt = (
            select(AttendanceSession)
            .where(AttendanceSession.marked_by_coach_id == coach_id)
            .order_by(AttendanceSession.date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_all(
        db: Session,
        batch_id: Optional[int] = None,
        school_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Count all attendance sessions with optional filters."""
        stmt = select(func.count(AttendanceSession.id))

        if batch_id is not None:
            stmt = stmt.where(AttendanceSession.batch_id == batch_id)
        if school_id is not None:
            stmt = stmt.where(AttendanceSession.school_id == school_id)
        if start_date is not None:
            stmt = stmt.where(AttendanceSession.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(AttendanceSession.date <= end_date)

        return db.scalar(stmt) or 0

    @staticmethod
    def update(db: Session, session: AttendanceSession) -> AttendanceSession:
        """Update an attendance session."""
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete(db: Session, session_id: int) -> bool:
        """Delete an attendance session."""
        session = AttendanceSessionRepository.get_by_id(db, session_id)
        if session:
            db.delete(session)
            db.commit()
            return True
        return False


class StudentAttendanceRepository:
    """Repository for StudentAttendance operations."""

    @staticmethod
    def create(db: Session, attendance: StudentAttendance) -> StudentAttendance:
        """Create a student attendance record."""
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def create_all(db: Session, attendances: List[StudentAttendance]) -> List[StudentAttendance]:
        """Create multiple student attendance records."""
        db.add_all(attendances)
        db.commit()
        return attendances

    @staticmethod
    def get_by_id(db: Session, attendance_id: int) -> Optional[StudentAttendance]:
        """Get student attendance by ID."""
        return db.scalar(
            select(StudentAttendance).where(StudentAttendance.id == attendance_id)
        )

    @staticmethod
    def get_by_session(db: Session, session_id: int) -> List[StudentAttendance]:
        """Get all student attendances for a session."""
        stmt = select(StudentAttendance).where(
            StudentAttendance.session_id == session_id
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_student(
        db: Session,
        student_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[StudentAttendance]:
        """Get all attendance records for a student."""
        stmt = select(StudentAttendance).where(
            StudentAttendance.student_id == student_id
        )

        if start_date or end_date:
            stmt = stmt.join(AttendanceSession)
            if start_date:
                stmt = stmt.where(AttendanceSession.date >= start_date)
            if end_date:
                stmt = stmt.where(AttendanceSession.date <= end_date)

        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_session_and_student(
        db: Session, session_id: int, student_id: int
    ) -> Optional[StudentAttendance]:
        """Get attendance for a specific student in a session."""
        return db.scalar(
            select(StudentAttendance).where(
                and_(
                    StudentAttendance.session_id == session_id,
                    StudentAttendance.student_id == student_id,
                )
            )
        )

    @staticmethod
    def update(db: Session, attendance: StudentAttendance) -> StudentAttendance:
        """Update a student attendance record."""
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def delete_by_session(db: Session, session_id: int) -> int:
        """Delete all student attendances for a session."""
        result = db.execute(
            delete(StudentAttendance).where(StudentAttendance.session_id == session_id)
        )
        db.commit()
        return result.rowcount or 0

    @staticmethod
    def count_by_status(
        db: Session,
        session_id: int,
        status: AttendanceStatus,
    ) -> int:
        """Count students with specific status in a session."""
        return db.scalar(
            select(func.count(StudentAttendance.id)).where(
                and_(
                    StudentAttendance.session_id == session_id,
                    StudentAttendance.status == status,
                )
            )
        ) or 0


class CoachAttendanceRepository:
    """Repository for CoachAttendance operations."""

    @staticmethod
    def create(db: Session, attendance: CoachAttendance) -> CoachAttendance:
        """Create a coach attendance record."""
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def create_all(db: Session, attendances: List[CoachAttendance]) -> List[CoachAttendance]:
        """Create multiple coach attendance records."""
        db.add_all(attendances)
        db.commit()
        return attendances

    @staticmethod
    def get_by_id(db: Session, attendance_id: int) -> Optional[CoachAttendance]:
        """Get coach attendance by ID."""
        return db.scalar(
            select(CoachAttendance).where(CoachAttendance.id == attendance_id)
        )

    @staticmethod
    def get_by_session(db: Session, session_id: int) -> List[CoachAttendance]:
        """Get all coach attendances for a session."""
        stmt = select(CoachAttendance).where(CoachAttendance.session_id == session_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_coach(
        db: Session,
        coach_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CoachAttendance]:
        """Get all attendance records for a coach."""
        stmt = select(CoachAttendance).where(CoachAttendance.coach_id == coach_id)

        if start_date or end_date:
            stmt = stmt.join(AttendanceSession)
            if start_date:
                stmt = stmt.where(AttendanceSession.date >= start_date)
            if end_date:
                stmt = stmt.where(AttendanceSession.date <= end_date)

        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_session_and_coach(
        db: Session, session_id: int, coach_id: int
    ) -> Optional[CoachAttendance]:
        """Get attendance for a specific coach in a session."""
        return db.scalar(
            select(CoachAttendance).where(
                and_(
                    CoachAttendance.session_id == session_id,
                    CoachAttendance.coach_id == coach_id,
                )
            )
        )

    @staticmethod
    def update(db: Session, attendance: CoachAttendance) -> CoachAttendance:
        """Update a coach attendance record."""
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def delete_by_session(db: Session, session_id: int) -> int:
        """Delete all coach attendances for a session."""
        result = db.execute(
            delete(CoachAttendance).where(CoachAttendance.session_id == session_id)
        )
        db.commit()
        return result.rowcount or 0

    @staticmethod
    def count_by_status(
        db: Session,
        session_id: int,
        status: AttendanceStatus,
    ) -> int:
        """Count coaches with specific status in a session."""
        return db.scalar(
            select(func.count(CoachAttendance.id)).where(
                and_(
                    CoachAttendance.session_id == session_id,
                    CoachAttendance.status == status,
                )
            )
        ) or 0

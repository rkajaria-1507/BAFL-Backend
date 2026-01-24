"""
Service layer for attendance management.
Implements business logic for student and coach attendance.
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from src.db.models.attendance import (
    AttendanceSession,
    StudentAttendance,
    CoachAttendance,
    AttendanceStatus,
    AttendanceMarkedBy,
)
from src.db.models.batch import Batch
from src.db.models.school import School
from src.db.models.student import Student
from src.db.models.coach import Coach
from src.db.models.user import User, UserRole
from src.db.models.coach_batch import CoachBatch
from src.db.repositories.attendance_repository import (
    AttendanceSessionRepository,
    StudentAttendanceRepository,
    CoachAttendanceRepository,
)
from src.db.repositories.student_repository import StudentRepository
from src.schemas.attendance import (
    AttendanceSessionCreate,
    AttendanceSessionCreateByCoach,
    AttendanceSessionCreateByAdmin,
    AttendanceSessionUpdate,
    AttendanceSessionResponse,
    AttendanceSessionSummary,
    AttendanceSessionListResponse,
    StudentAttendanceResponse,
    CoachAttendanceResponse,
    StudentAttendanceHistoryResponse,
    StudentAttendanceHistoryItem,
    CoachAttendanceHistoryResponse,
    CoachAttendanceHistoryItem,
    AttendancePreCreateResponse,
    AttendancePreCreateBatch,
    AttendancePreCreateStudent,
    AttendancePreCreateCoach,
    StudentAttendanceInput,
    CoachAttendanceInput,
    AttendanceStatusEnum,
    AttendanceMarkedByEnum,
)


class AttendanceService:
    """Service class for attendance operations."""

    @staticmethod
    def get_pre_create_data(db: Session, user: User) -> AttendancePreCreateResponse:
        """
        Get pre-create data for attendance session.
        Returns batches, students grouped by batch, and coaches.
        """
        batches_query = select(Batch).join(School)

        # If user is a coach, filter to only their assigned batches
        if user.role == UserRole.COACH:
            coach = db.scalar(select(Coach).where(Coach.username == user.username))
            if coach:
                batch_ids = [
                    assignment.batch_id
                    for assignment in coach.batch_assignments
                    if assignment.batch_id is not None
                ]
                if batch_ids:
                    batches_query = batches_query.where(Batch.id.in_(batch_ids))
                else:
                    batches_query = batches_query.where(False)

        batches = list(db.scalars(batches_query).all())

        # Build batch info
        batch_list = []
        students_by_batch = {}

        for batch in batches:
            batch_list.append(
                AttendancePreCreateBatch(
                    id=batch.id,
                    name=batch.batch_name,
                    school_id=batch.school_id,
                    school_name=batch.school.name if batch.school else None,
                )
            )

            # Get students for this batch
            students = StudentRepository.get_by_batch(db, batch.id)
            students_by_batch[batch.id] = [
                AttendancePreCreateStudent(
                    id=student.id,
                    name=student.name,
                    batch_id=student.batch_id,
                )
                for student in students
            ]

        # Get all coaches (for admin view) or just the current coach
        if user.role == UserRole.ADMIN:
            coaches = list(db.scalars(select(Coach).where(Coach.is_active == True)).all())
            coach_list = [
                AttendancePreCreateCoach(id=coach.id, name=coach.name)
                for coach in coaches
            ]
        else:
            coach_list = []

        return AttendancePreCreateResponse(
            batches=batch_list,
            students_by_batch=students_by_batch,
            coaches=coach_list,
        )

    @staticmethod
    def create_session(
        db: Session,
        payload: AttendanceSessionCreate,
        user: User,
        coach: Optional[Coach] = None,
    ) -> AttendanceSessionResponse:
        """
        Create an attendance session.
        - For coaches: coach is auto-marked present, coach_attendances in payload is ignored
        - For admins: can mark both students and coaches
        """
        # Check if session already exists for this batch and date
        existing = AttendanceSessionRepository.get_by_batch_and_date(
            db, payload.batch_id, payload.date
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendance session already exists for batch {payload.batch_id} on {payload.date}",
            )

        # Verify batch exists
        batch = db.scalar(select(Batch).where(Batch.id == payload.batch_id))
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {payload.batch_id} not found",
            )

        # Handle coach-specific logic
        if user.role == UserRole.COACH:
            if coach is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Coach profile required",
                )
            # Check if coach is assigned to this batch
            assigned_batch_ids = {
                assignment.batch_id
                for assignment in coach.batch_assignments
                if assignment.batch_id is not None
            }
            if payload.batch_id not in assigned_batch_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this batch",
                )

            # Create session marked by coach
            session = AttendanceSession(
                batch_id=payload.batch_id,
                school_id=payload.school_id or batch.school_id,
                date=payload.date,
                marked_by_coach_id=coach.id,
                marked_by_type=AttendanceMarkedBy.COACH,
                notes=payload.notes,
            )
        else:
            # Admin creating session
            session = AttendanceSession(
                batch_id=payload.batch_id,
                school_id=payload.school_id or batch.school_id,
                date=payload.date,
                marked_by_user_id=user.id,
                marked_by_type=AttendanceMarkedBy.ADMIN,
                notes=payload.notes,
            )

        session = AttendanceSessionRepository.create(db, session)

        # Create student attendances
        student_attendances = []
        for student_input in payload.student_attendances:
            student = db.scalar(select(Student).where(Student.id == student_input.student_id))
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student {student_input.student_id} not found",
                )
            # For coaches, verify student belongs to the batch
            if user.role == UserRole.COACH and student.batch_id != payload.batch_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student {student_input.student_id} does not belong to batch {payload.batch_id}",
                )

            student_attendances.append(
                StudentAttendance(
                    session_id=session.id,
                    student_id=student_input.student_id,
                    status=AttendanceStatus(student_input.status.value),
                    notes=student_input.notes,
                )
            )

        if student_attendances:
            StudentAttendanceRepository.create_all(db, student_attendances)

        # Handle coach attendances
        if user.role == UserRole.COACH and coach:
            # Auto-mark coach as present
            coach_attendance = CoachAttendance(
                session_id=session.id,
                coach_id=coach.id,
                status=AttendanceStatus.PRESENT,
                auto_marked=True,
                notes="Auto-marked present for marking student attendance",
            )
            CoachAttendanceRepository.create(db, coach_attendance)
        elif user.role == UserRole.ADMIN:
            # Admin can explicitly mark coach attendance
            coach_attendances = []
            for coach_input in payload.coach_attendances:
                coach_obj = db.scalar(select(Coach).where(Coach.id == coach_input.coach_id))
                if not coach_obj:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Coach {coach_input.coach_id} not found",
                    )

                coach_attendances.append(
                    CoachAttendance(
                        session_id=session.id,
                        coach_id=coach_input.coach_id,
                        status=AttendanceStatus(coach_input.status.value),
                        auto_marked=False,
                        notes=coach_input.notes,
                    )
                )

            if coach_attendances:
                CoachAttendanceRepository.create_all(db, coach_attendances)

        # Refresh and return
        db.refresh(session)
        return AttendanceService._serialize_session(db, session)

    @staticmethod
    def create_session_by_coach(
        db: Session,
        payload: AttendanceSessionCreateByCoach,
        coach: Coach,
    ) -> AttendanceSessionResponse:
        """
        Create an attendance session by a coach.
        The coach is automatically marked as present.
        """
        # Check if session already exists for this batch and date
        existing = AttendanceSessionRepository.get_by_batch_and_date(
            db, payload.batch_id, payload.date
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendance session already exists for batch {payload.batch_id} on {payload.date}",
            )

        # Verify batch exists and coach has access
        batch = db.scalar(select(Batch).where(Batch.id == payload.batch_id))
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {payload.batch_id} not found",
            )

        # Check if coach is assigned to this batch
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in coach.batch_assignments
            if assignment.batch_id is not None
        }
        if payload.batch_id not in assigned_batch_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this batch",
            )

        # Create session
        session = AttendanceSession(
            batch_id=payload.batch_id,
            school_id=payload.school_id or batch.school_id,
            date=payload.date,
            marked_by_coach_id=coach.id,
            marked_by_type=AttendanceMarkedBy.COACH,
            notes=payload.notes,
        )
        session = AttendanceSessionRepository.create(db, session)

        # Create student attendances
        student_attendances = []
        for student_input in payload.student_attendances:
            # Verify student belongs to the batch
            student = db.scalar(select(Student).where(Student.id == student_input.student_id))
            if not student or student.batch_id != payload.batch_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student {student_input.student_id} does not belong to batch {payload.batch_id}",
                )

            student_attendances.append(
                StudentAttendance(
                    session_id=session.id,
                    student_id=student_input.student_id,
                    status=AttendanceStatus(student_input.status.value),
                    notes=student_input.notes,
                )
            )

        if student_attendances:
            StudentAttendanceRepository.create_all(db, student_attendances)

        # Auto-mark coach as present
        coach_attendance = CoachAttendance(
            session_id=session.id,
            coach_id=coach.id,
            status=AttendanceStatus.PRESENT,
            auto_marked=True,
            notes="Auto-marked present for marking student attendance",
        )
        CoachAttendanceRepository.create(db, coach_attendance)

        # Refresh and return
        db.refresh(session)
        return AttendanceService._serialize_session(db, session)

    @staticmethod
    def create_session_by_admin(
        db: Session,
        payload: AttendanceSessionCreateByAdmin,
        user: User,
    ) -> AttendanceSessionResponse:
        """
        Create an attendance session by an admin.
        Admin can mark both students and coaches.
        """
        # Check if session already exists for this batch and date
        existing = AttendanceSessionRepository.get_by_batch_and_date(
            db, payload.batch_id, payload.date
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendance session already exists for batch {payload.batch_id} on {payload.date}",
            )

        # Verify batch exists
        batch = db.scalar(select(Batch).where(Batch.id == payload.batch_id))
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {payload.batch_id} not found",
            )

        # Create session
        session = AttendanceSession(
            batch_id=payload.batch_id,
            school_id=payload.school_id or batch.school_id,
            date=payload.date,
            marked_by_user_id=user.id,
            marked_by_type=AttendanceMarkedBy.ADMIN,
            notes=payload.notes,
        )
        session = AttendanceSessionRepository.create(db, session)

        # Create student attendances
        student_attendances = []
        for student_input in payload.student_attendances:
            student = db.scalar(select(Student).where(Student.id == student_input.student_id))
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student {student_input.student_id} not found",
                )

            student_attendances.append(
                StudentAttendance(
                    session_id=session.id,
                    student_id=student_input.student_id,
                    status=AttendanceStatus(student_input.status.value),
                    notes=student_input.notes,
                )
            )

        if student_attendances:
            StudentAttendanceRepository.create_all(db, student_attendances)

        # Create coach attendances
        coach_attendances = []
        for coach_input in payload.coach_attendances:
            coach = db.scalar(select(Coach).where(Coach.id == coach_input.coach_id))
            if not coach:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Coach {coach_input.coach_id} not found",
                )

            coach_attendances.append(
                CoachAttendance(
                    session_id=session.id,
                    coach_id=coach_input.coach_id,
                    status=AttendanceStatus(coach_input.status.value),
                    auto_marked=False,
                    notes=coach_input.notes,
                )
            )

        if coach_attendances:
            CoachAttendanceRepository.create_all(db, coach_attendances)

        # Refresh and return
        db.refresh(session)
        return AttendanceService._serialize_session(db, session)

    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[AttendanceSessionResponse]:
        """Get a single attendance session by ID."""
        session = AttendanceSessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        return AttendanceService._serialize_session(db, session)

    @staticmethod
    def get_session_model(db: Session, session_id: int) -> Optional[AttendanceSession]:
        """Get the raw session model."""
        return AttendanceSessionRepository.get_by_id(db, session_id)

    @staticmethod
    def get_sessions(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        batch_id: Optional[int] = None,
        school_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AttendanceSessionListResponse:
        """Get all attendance sessions with filters."""
        sessions = AttendanceSessionRepository.get_all(
            db,
            skip=skip,
            limit=limit,
            batch_id=batch_id,
            school_id=school_id,
            start_date=start_date,
            end_date=end_date,
        )
        total = AttendanceSessionRepository.count_all(
            db,
            batch_id=batch_id,
            school_id=school_id,
            start_date=start_date,
            end_date=end_date,
        )

        summaries = [AttendanceService._create_summary(db, s) for s in sessions]
        return AttendanceSessionListResponse(sessions=summaries, total=total)

    @staticmethod
    def get_sessions_for_coach(
        db: Session,
        coach: Coach,
        skip: int = 0,
        limit: int = 100,
    ) -> AttendanceSessionListResponse:
        """Get attendance sessions accessible to a coach (their batches or created by them)."""
        # Get batch IDs assigned to this coach
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in coach.batch_assignments
            if assignment.batch_id is not None
        }

        # Get sessions for these batches
        all_sessions = []
        for batch_id in assigned_batch_ids:
            sessions = AttendanceSessionRepository.get_all(
                db, batch_id=batch_id, skip=0, limit=1000
            )
            all_sessions.extend(sessions)

        # Also include sessions marked by this coach
        marked_sessions = AttendanceSessionRepository.get_by_coach(db, coach.id)
        existing_ids = {s.id for s in all_sessions}
        for s in marked_sessions:
            if s.id not in existing_ids:
                all_sessions.append(s)

        # Sort by date descending and paginate
        all_sessions.sort(key=lambda x: x.date, reverse=True)
        paginated = all_sessions[skip : skip + limit]

        summaries = [AttendanceService._create_summary(db, s) for s in paginated]
        return AttendanceSessionListResponse(sessions=summaries, total=len(all_sessions))

    @staticmethod
    def update_session(
        db: Session,
        session_id: int,
        payload: AttendanceSessionUpdate,
    ) -> Optional[AttendanceSessionResponse]:
        """Update an attendance session."""
        session = AttendanceSessionRepository.get_by_id(db, session_id)
        if not session:
            return None

        # Update session fields
        if payload.date is not None:
            # Check for conflict
            existing = AttendanceSessionRepository.get_by_batch_and_date(
                db, session.batch_id, payload.date
            )
            if existing and existing.id != session_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attendance session already exists for this batch on {payload.date}",
                )
            session.date = payload.date

        if payload.notes is not None:
            session.notes = payload.notes

        # Update student attendances if provided
        if payload.student_attendances is not None:
            # Delete existing and recreate
            StudentAttendanceRepository.delete_by_session(db, session_id)
            student_attendances = []
            for student_input in payload.student_attendances:
                student_attendances.append(
                    StudentAttendance(
                        session_id=session.id,
                        student_id=student_input.student_id,
                        status=AttendanceStatus(student_input.status.value),
                        notes=student_input.notes,
                    )
                )
            if student_attendances:
                StudentAttendanceRepository.create_all(db, student_attendances)

        # Update coach attendances if provided
        if payload.coach_attendances is not None:
            # Delete existing and recreate
            CoachAttendanceRepository.delete_by_session(db, session_id)
            coach_attendances = []
            for coach_input in payload.coach_attendances:
                coach_attendances.append(
                    CoachAttendance(
                        session_id=session.id,
                        coach_id=coach_input.coach_id,
                        status=AttendanceStatus(coach_input.status.value),
                        auto_marked=False,
                        notes=coach_input.notes,
                    )
                )
            if coach_attendances:
                CoachAttendanceRepository.create_all(db, coach_attendances)

        AttendanceSessionRepository.update(db, session)
        return AttendanceService._serialize_session(db, session)

    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        """Delete an attendance session."""
        return AttendanceSessionRepository.delete(db, session_id)

    @staticmethod
    def get_student_attendance_history(
        db: Session,
        student_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> StudentAttendanceHistoryResponse:
        """Get attendance history for a specific student."""
        student = db.scalar(select(Student).where(Student.id == student_id))
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        attendances = StudentAttendanceRepository.get_by_student(
            db, student_id, start_date, end_date
        )

        history = []
        present_count = 0
        for att in attendances:
            session = att.session
            marked_by_name = None
            if session.marked_by_type == AttendanceMarkedBy.ADMIN and session.marked_by_user:
                marked_by_name = session.marked_by_user.name
            elif session.marked_by_type == AttendanceMarkedBy.COACH and session.marked_by_coach:
                marked_by_name = session.marked_by_coach.name

            history.append(
                StudentAttendanceHistoryItem(
                    session_id=session.id,
                    date=session.date,
                    batch_name=session.batch.batch_name if session.batch else None,
                    school_name=session.school.name if session.school else None,
                    status=AttendanceStatusEnum(att.status.value),
                    marked_by_type=AttendanceMarkedByEnum(session.marked_by_type.value),
                    marked_by_name=marked_by_name,
                )
            )
            if att.status == AttendanceStatus.PRESENT:
                present_count += 1

        total = len(attendances)
        return StudentAttendanceHistoryResponse(
            student_id=student_id,
            student_name=student.name,
            total_sessions=total,
            present_count=present_count,
            absent_count=total - present_count,
            attendance_percentage=round((present_count / total * 100) if total > 0 else 0.0, 2),
            history=history,
        )

    @staticmethod
    def get_coach_attendance_history(
        db: Session,
        coach_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> CoachAttendanceHistoryResponse:
        """Get attendance history for a specific coach."""
        coach = db.scalar(select(Coach).where(Coach.id == coach_id))
        if not coach:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coach {coach_id} not found",
            )

        attendances = CoachAttendanceRepository.get_by_coach(
            db, coach_id, start_date, end_date
        )

        history = []
        present_count = 0
        for att in attendances:
            session = att.session
            history.append(
                CoachAttendanceHistoryItem(
                    session_id=session.id,
                    date=session.date,
                    batch_name=session.batch.batch_name if session.batch else None,
                    school_name=session.school.name if session.school else None,
                    status=AttendanceStatusEnum(att.status.value),
                    auto_marked=att.auto_marked,
                )
            )
            if att.status == AttendanceStatus.PRESENT:
                present_count += 1

        total = len(attendances)
        return CoachAttendanceHistoryResponse(
            coach_id=coach_id,
            coach_name=coach.name,
            total_sessions=total,
            present_count=present_count,
            absent_count=total - present_count,
            attendance_percentage=round((present_count / total * 100) if total > 0 else 0.0, 2),
            history=history,
        )

    @staticmethod
    def update_student_attendance(
        db: Session,
        session_id: int,
        student_id: int,
        status: AttendanceStatusEnum,
        notes: Optional[str] = None,
    ) -> StudentAttendanceResponse:
        """Update a single student's attendance."""
        attendance = StudentAttendanceRepository.get_by_session_and_student(
            db, session_id, student_id
        )
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record not found for student {student_id} in session {session_id}",
            )

        attendance.status = AttendanceStatus(status.value)
        if notes is not None:
            attendance.notes = notes

        StudentAttendanceRepository.update(db, attendance)
        return AttendanceService._serialize_student_attendance(attendance)

    @staticmethod
    def update_coach_attendance(
        db: Session,
        session_id: int,
        coach_id: int,
        status: AttendanceStatusEnum,
        notes: Optional[str] = None,
    ) -> CoachAttendanceResponse:
        """Update a single coach's attendance."""
        attendance = CoachAttendanceRepository.get_by_session_and_coach(
            db, session_id, coach_id
        )
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record not found for coach {coach_id} in session {session_id}",
            )

        attendance.status = AttendanceStatus(status.value)
        attendance.auto_marked = False  # Override auto-marked since it's now manual
        if notes is not None:
            attendance.notes = notes

        CoachAttendanceRepository.update(db, attendance)
        return AttendanceService._serialize_coach_attendance(attendance)

    # ============= Private Helpers =============

    @staticmethod
    def _serialize_session(db: Session, session: AttendanceSession) -> AttendanceSessionResponse:
        """Serialize an AttendanceSession to response schema."""
        student_attendances = [
            AttendanceService._serialize_student_attendance(sa)
            for sa in session.student_attendances
        ]
        coach_attendances = [
            AttendanceService._serialize_coach_attendance(ca)
            for ca in session.coach_attendances
        ]

        present_count = sum(
            1 for sa in session.student_attendances if sa.status == AttendanceStatus.PRESENT
        )
        absent_count = sum(
            1 for sa in session.student_attendances if sa.status == AttendanceStatus.ABSENT
        )

        marked_by_name = None
        if session.marked_by_type == AttendanceMarkedBy.ADMIN and session.marked_by_user:
            marked_by_name = session.marked_by_user.name
        elif session.marked_by_type == AttendanceMarkedBy.COACH and session.marked_by_coach:
            marked_by_name = session.marked_by_coach.name

        return AttendanceSessionResponse(
            id=session.id,
            batch_id=session.batch_id,
            batch_name=session.batch.batch_name if session.batch else None,
            school_id=session.school_id,
            school_name=session.school.name if session.school else None,
            date=session.date,
            marked_by_type=AttendanceMarkedByEnum(session.marked_by_type.value),
            marked_by_user_id=session.marked_by_user_id,
            marked_by_coach_id=session.marked_by_coach_id,
            marked_by_name=marked_by_name,
            notes=session.notes,
            student_attendances=student_attendances,
            coach_attendances=coach_attendances,
            present_count=present_count,
            absent_count=absent_count,
            total_students=len(session.student_attendances),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    @staticmethod
    def _create_summary(db: Session, session: AttendanceSession) -> AttendanceSessionSummary:
        """Create a summary for an attendance session."""
        present_count = sum(
            1 for sa in session.student_attendances if sa.status == AttendanceStatus.PRESENT
        )
        absent_count = sum(
            1 for sa in session.student_attendances if sa.status == AttendanceStatus.ABSENT
        )
        coach_present_count = sum(
            1 for ca in session.coach_attendances if ca.status == AttendanceStatus.PRESENT
        )
        coach_absent_count = sum(
            1 for ca in session.coach_attendances if ca.status == AttendanceStatus.ABSENT
        )

        marked_by_name = None
        if session.marked_by_type == AttendanceMarkedBy.ADMIN and session.marked_by_user:
            marked_by_name = session.marked_by_user.name
        elif session.marked_by_type == AttendanceMarkedBy.COACH and session.marked_by_coach:
            marked_by_name = session.marked_by_coach.name

        return AttendanceSessionSummary(
            id=session.id,
            batch_id=session.batch_id,
            batch_name=session.batch.batch_name if session.batch else None,
            school_id=session.school_id,
            school_name=session.school.name if session.school else None,
            date=session.date,
            marked_by_type=AttendanceMarkedByEnum(session.marked_by_type.value),
            marked_by_name=marked_by_name,
            present_count=present_count,
            absent_count=absent_count,
            total_students=len(session.student_attendances),
            coach_present_count=coach_present_count,
            coach_absent_count=coach_absent_count,
            total_coaches=len(session.coach_attendances),
        )

    @staticmethod
    def _serialize_student_attendance(
        attendance: StudentAttendance,
    ) -> StudentAttendanceResponse:
        """Serialize a StudentAttendance record."""
        return StudentAttendanceResponse(
            id=attendance.id,
            session_id=attendance.session_id,
            student_id=attendance.student_id,
            student_name=attendance.student.name if attendance.student else None,
            status=AttendanceStatusEnum(attendance.status.value),
            notes=attendance.notes,
            created_at=attendance.created_at,
            updated_at=attendance.updated_at,
        )

    @staticmethod
    def _serialize_coach_attendance(
        attendance: CoachAttendance,
    ) -> CoachAttendanceResponse:
        """Serialize a CoachAttendance record."""
        return CoachAttendanceResponse(
            id=attendance.id,
            session_id=attendance.session_id,
            coach_id=attendance.coach_id,
            coach_name=attendance.coach.name if attendance.coach else None,
            status=AttendanceStatusEnum(attendance.status.value),
            auto_marked=attendance.auto_marked,
            notes=attendance.notes,
            created_at=attendance.created_at,
            updated_at=attendance.updated_at,
        )

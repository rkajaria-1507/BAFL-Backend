"""
API endpoints for attendance management.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.core.logging import api_logger
from src.db.models.user import User, UserRole
from src.api.v1.dependencies.auth import get_current_user
from src.api.v1.utils.coach import get_coach_profile_or_403
from src.services.attendance_service import AttendanceService
from src.schemas.attendance import (
    AttendanceSessionCreate,
    AttendanceSessionUpdate,
    AttendanceSessionResponse,
    AttendanceSessionListResponse,
    StudentAttendanceHistoryResponse,
    CoachAttendanceHistoryResponse,
    StudentAttendanceResponse,
    CoachAttendanceResponse,
    AttendancePreCreateResponse,
    AttendanceStatusEnum,
    StudentAttendanceUpdate,
    CoachAttendanceUpdate,
)


router = APIRouter(prefix="/attendance", tags=["Attendance"])


# ============= Session Endpoints =============


@router.get("/sessions/pre-create", response_model=AttendancePreCreateResponse)
def get_pre_create_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get data needed to create an attendance session.
    Returns batches, students grouped by batch, and coaches.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    api_logger.info(f"Fetching attendance pre-create data. User: {current_user.username}")
    return AttendanceService.get_pre_create_data(db, current_user)


@router.post("/sessions", response_model=AttendanceSessionResponse, status_code=status.HTTP_201_CREATED)
def create_attendance_session(
    payload: AttendanceSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new attendance session.
    - For coaches: coach is auto-marked present, coach_attendances is ignored
    - For admins: can mark both students and coaches
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    api_logger.info(f"Creating attendance session. User: {current_user.username}")
    
    coach = None
    if current_user.role == UserRole.COACH:
        coach = get_coach_profile_or_403(current_user, db)
    
    return AttendanceService.create_session(db, payload, current_user, coach)


@router.get("/sessions", response_model=AttendanceSessionListResponse)
def get_attendance_sessions(
    batch_id: Optional[int] = Query(None, description="Filter by batch ID"),
    school_id: Optional[int] = Query(None, description="Filter by school ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all attendance sessions with optional filters.
    - Admins see all sessions
    - Coaches see only sessions for their assigned batches
    """
    api_logger.info(f"Fetching attendance sessions. User: {current_user.username}")

    if current_user.role == UserRole.COACH:
        coach = get_coach_profile_or_403(current_user, db)
        return AttendanceService.get_sessions_for_coach(db, coach, skip, limit)

    return AttendanceService.get_sessions(
        db,
        skip=skip,
        limit=limit,
        batch_id=batch_id,
        school_id=school_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/sessions/{session_id}", response_model=AttendanceSessionResponse)
def get_attendance_session(
    session_id: int = Path(..., description="Session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific attendance session by ID."""
    api_logger.info(f"Fetching attendance session {session_id}. User: {current_user.username}")

    session_model = AttendanceService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check access for coaches
    if current_user.role == UserRole.COACH:
        coach = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in coach.batch_assignments
            if assignment.batch_id is not None
        }
        if (
            session_model.marked_by_coach_id != coach.id
            and session_model.batch_id not in assigned_batch_ids
        ):
            raise HTTPException(status_code=403, detail="Access denied")

    result = AttendanceService.get_session(db, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.put("/sessions/{session_id}", response_model=AttendanceSessionResponse)
def update_attendance_session(
    payload: AttendanceSessionUpdate,
    session_id: int = Path(..., description="Session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an attendance session."""
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    api_logger.info(f"Updating attendance session {session_id}. User: {current_user.username}")

    session_model = AttendanceService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check access for coaches
    if current_user.role == UserRole.COACH:
        coach = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in coach.batch_assignments
            if assignment.batch_id is not None
        }
        if (
            session_model.marked_by_coach_id != coach.id
            and session_model.batch_id not in assigned_batch_ids
        ):
            raise HTTPException(status_code=403, detail="Access denied")
        # Coaches cannot update coach attendance
        if payload.coach_attendances is not None:
            raise HTTPException(
                status_code=403, detail="Coaches cannot update coach attendance"
            )

    result = AttendanceService.update_session(db, session_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance_session(
    session_id: int = Path(..., description="Session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an attendance session."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    api_logger.info(f"Deleting attendance session {session_id}. User: {current_user.username}")

    if not AttendanceService.delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")


# ============= Individual Attendance Updates =============


@router.patch(
    "/sessions/{session_id}/students/{student_id}",
    response_model=StudentAttendanceResponse,
)
def update_student_attendance(
    student_update: StudentAttendanceUpdate,
    session_id: int = Path(..., description="Session ID"),
    student_id: int = Path(..., description="Student ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a specific student's attendance in a session."""
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    session_model = AttendanceService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check access for coaches
    if current_user.role == UserRole.COACH:
        coach = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in coach.batch_assignments
            if assignment.batch_id is not None
        }
        if (
            session_model.marked_by_coach_id != coach.id
            and session_model.batch_id not in assigned_batch_ids
        ):
            raise HTTPException(status_code=403, detail="Access denied")

    api_logger.info(
        f"Updating student {student_id} attendance in session {session_id}. User: {current_user.username}"
    )

    if student_update.status is None:
        raise HTTPException(status_code=400, detail="Status is required")

    return AttendanceService.update_student_attendance(
        db, session_id, student_id, student_update.status, student_update.notes
    )


@router.patch(
    "/sessions/{session_id}/coaches/{coach_id}",
    response_model=CoachAttendanceResponse,
)
def update_coach_attendance(
    coach_update: CoachAttendanceUpdate,
    session_id: int = Path(..., description="Session ID"),
    coach_id: int = Path(..., description="Coach ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a specific coach's attendance in a session. Admin only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    session_model = AttendanceService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    api_logger.info(
        f"Updating coach {coach_id} attendance in session {session_id}. User: {current_user.username}"
    )

    if coach_update.status is None:
        raise HTTPException(status_code=400, detail="Status is required")

    return AttendanceService.update_coach_attendance(
        db, session_id, coach_id, coach_update.status, coach_update.notes
    )


# ============= History Endpoints =============


@router.get("/students/{student_id}/history", response_model=StudentAttendanceHistoryResponse)
def get_student_attendance_history(
    student_id: int = Path(..., description="Student ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get attendance history for a specific student."""
    api_logger.info(
        f"Fetching attendance history for student {student_id}. User: {current_user.username}"
    )
    return AttendanceService.get_student_attendance_history(
        db, student_id, start_date, end_date
    )


@router.get("/coaches/{coach_id}/history", response_model=CoachAttendanceHistoryResponse)
def get_coach_attendance_history(
    coach_id: int = Path(..., description="Coach ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get attendance history for a specific coach."""
    if current_user.role == UserRole.COACH:
        coach = get_coach_profile_or_403(current_user, db)
        if coach.id != coach_id:
            raise HTTPException(
                status_code=403, detail="Coaches can only view their own attendance history"
            )

    api_logger.info(
        f"Fetching attendance history for coach {coach_id}. User: {current_user.username}"
    )
    return AttendanceService.get_coach_attendance_history(
        db, coach_id, start_date, end_date
    )

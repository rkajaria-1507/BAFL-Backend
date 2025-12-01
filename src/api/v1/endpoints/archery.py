from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.core.logging import api_logger
from src.schemas.archery import (
    ArcherySessionCreate,
    ArcherySessionResponse,
    ArcherySessionUpdate,
    ArcherySessionSummaryResponse,
    ArcheryStudentSummaryResponse,
    ArcheryStudentDetailResponse,
    ArcheryStudentUpdate,
)
from src.schemas.physical_assessment import PreCreateResponse
from src.services.archery_service import ArcheryService
from src.api.v1.dependencies.auth import get_current_user
from src.db.models.user import User, UserRole

router = APIRouter(prefix="/archery", tags=["Archery"])

# Permissions (reusing physical permissions or creating new ones? User didn't specify. 
# Assuming similar permissions structure. I'll use PHYSICAL_SESSIONS_* for now or generic ones if available.
# Actually, I should probably check if there are specific permissions. 
# If not, I'll assume coaches/admins can access.
# Let's stick to role based for now if permissions aren't granular enough.)

@router.post("/sessions", response_model=ArcherySessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: ArcherySessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Creating archery session. User: {current_user.username}")
    # Basic role check
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return ArcheryService.create_session(db, payload)

@router.get("/sessions/pre-create", response_model=PreCreateResponse)
def get_pre_create_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    api_logger.info(f"Fetching archery pre-create data. User: {current_user.username}")
    return ArcheryService.get_pre_create_data(db, current_user)


@router.get("/sessions/admin-view", response_model=ArcherySessionSummaryResponse)
def get_admin_view_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    api_logger.info(f"Fetching archery sessions (admin view). User: {current_user.username}")
    return ArcheryService.get_admin_view_sessions(db)


@router.get("/sessions/coach-view", response_model=ArcherySessionSummaryResponse)
def get_coach_view_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=403, detail="Coach access required")
    coach_profile = getattr(current_user, "coach_profile", None)
    if not coach_profile:
        raise HTTPException(status_code=403, detail="Coach profile not found")
    api_logger.info(f"Fetching archery sessions (coach view). User: {current_user.username}")
    return ArcheryService.get_coach_view_sessions(db, coach_profile.id)


@router.get("/sessions/{session_id}", response_model=ArcherySessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_model = ArcheryService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Coach profile not found")
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if session_model.coach_id != coach_profile.id and session_model.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    return ArcheryService.serialize_session(db, session_model)


@router.put("/sessions/{session_id}", response_model=ArcherySessionResponse)
def update_session(
    session_id: int,
    payload: ArcherySessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    session_model = ArcheryService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Coach profile not found")
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if session_model.coach_id != coach_profile.id and session_model.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    updated = ArcheryService.update_session(db, session_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    session_model = ArcheryService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Coach profile not found")
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if session_model.coach_id != coach_profile.id and session_model.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    ArcheryService.delete_session(db, session_id)
    return None


@router.get("/students/admin-view", response_model=ArcheryStudentSummaryResponse)
def get_admin_view_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return ArcheryService.get_admin_view_students(db)


@router.get("/students/coach-view", response_model=ArcheryStudentSummaryResponse)
def get_coach_view_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=403, detail="Coach access required")
    coach_profile = getattr(current_user, "coach_profile", None)
    if not coach_profile:
        raise HTTPException(status_code=403, detail="Coach profile not found")
    return ArcheryService.get_coach_view_students(db, coach_profile.id)


@router.get("/students/{student_id}", response_model=ArcheryStudentDetailResponse)
def get_student_detail(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    detail = ArcheryService.get_student_detail(db, student_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Coach profile not found")
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if detail.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    return detail


@router.put("/students/{student_id}", response_model=ArcheryStudentDetailResponse)
def update_student_results(
    student_id: int,
    payload: ArcheryStudentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Coach profile not found")
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        detail = ArcheryService.get_student_detail(db, student_id)
        if not detail or detail.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    return ArcheryService.update_student_results(db, student_id, payload)

@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_results(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    detail = ArcheryService.get_student_detail(db, student_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Coach profile not found")
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if detail.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    deleted = ArcheryService.delete_student_results(db, student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No archery results to delete")

    return None

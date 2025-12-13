from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies.auth import (
    AuthenticatedIdentity,
    get_current_identity,
    get_current_user,
    require_permission,
)
from src.api.v1.utils.coach import get_coach_profile_or_403
from src.core.logging import api_logger
from src.db.database import get_db
from src.db.models.permission import PermissionType
from src.db.models.user import User, UserRole
from src.schemas.physical_assessment import (
    PhysicalAssessmentLevelMappingResponse,
    PhysicalAssessmentSessionAdminViewResponse,
    PhysicalAssessmentSessionResponse,
    PhysicalAssessmentSessionUpdate,
    PhysicalAssessmentSessionWithResultsCreate,
    PhysicalAssessmentStudentDetailResponse,
    PhysicalAssessmentStudentSummaryResponse,
    PhysicalAssessmentStudentUpdate,
    PreCreateResponse,
)
from src.services.physical_assessment_service import PhysicalAssessmentService


router = APIRouter(prefix="/physical", tags=["Physical Assessments"])

# Permissions
require_view_sessions = require_permission(PermissionType.PHYSICAL_SESSIONS_VIEW)
require_edit_sessions = require_permission(PermissionType.PHYSICAL_SESSIONS_EDIT)
require_add_sessions = require_permission(PermissionType.PHYSICAL_SESSIONS_ADD)


@router.post("/sessions", response_model=PhysicalAssessmentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: PhysicalAssessmentSessionWithResultsCreate,
    current_user: User = Depends(require_add_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Creating physical assessment session. User: %s (ID: %s), Batch ID: %s",
        current_user.username,
        current_user.id,
        payload.batch_id,
    )

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        if payload.coach_id and payload.coach_id != coach_profile.id:
            api_logger.warning(
                "Coach %s attempted to create session for another coach ID: %s",
                current_user.username,
                payload.coach_id,
            )
            raise HTTPException(status_code=403, detail="Coach may only create sessions for their own id")
        # Ensure the session is always associated with the authenticated coach.
        if not payload.coach_id:
            payload.coach_id = coach_profile.id

    try:
        new_session = PhysicalAssessmentService.create_session_with_results(db, payload, current_user)
        api_logger.info("Successfully created physical assessment session. Session ID: %s", new_session.id)
        return new_session
    except HTTPException:
        raise
    except ValueError as exc:
        api_logger.warning("Validation error during session creation: %s", exc)
        raise HTTPException(
            status_code=400,
            detail={"code": "validation_error", "message": str(exc)},
        )
    except Exception as exc:  # pragma: no cover - unexpected
        api_logger.error("Unexpected error during session creation: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "server_error", "message": str(exc)})


@router.get("/sessions/pre-create", response_model=PreCreateResponse)
def get_pre_create_data(
    current_user: User = Depends(require_add_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Fetching pre-create data for user: %s (ID: %s)",
        current_user.username,
        current_user.id,
    )
    return PhysicalAssessmentService.get_pre_create_data(db, current_user)


@router.get("/sessions", response_model=PhysicalAssessmentSessionAdminViewResponse)
def get_sessions_view(
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Fetching physical assessment sessions. User: %s (ID: %s)",
        current_user.username,
        current_user.id,
    )
    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        return PhysicalAssessmentService.get_coach_view_sessions(db, coach_profile.id)

    return PhysicalAssessmentService.get_admin_view_sessions(db)


@router.get("/sessions/view", response_model=PhysicalAssessmentSessionAdminViewResponse, include_in_schema=False)
@router.get("/sessions/admin-view", response_model=PhysicalAssessmentSessionAdminViewResponse, include_in_schema=False)
@router.get("/sessions/coach-view", response_model=PhysicalAssessmentSessionAdminViewResponse, include_in_schema=False)
def get_sessions_view_alias(
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db),
):
    """Backward-compatible aliases for legacy session view routes."""
    return get_sessions_view(current_user=current_user, db=db)


@router.get("/sessions/{session_id}", response_model=PhysicalAssessmentSessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Fetching session details. Session ID: %s, User: %s",
        session_id,
        current_user.username,
    )
    session_model = PhysicalAssessmentService.get_session_model(db, session_id)
    if not session_model:
        api_logger.warning("Session not found. Session ID: %s", session_id)
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        batch_coach_id = session_model.batch.coach_id if session_model.batch else None
        if session_model.coach_id != coach_profile.id and batch_coach_id != coach_profile.id:
            api_logger.warning(
                "Coach %s denied access to session %s",
                current_user.username,
                session_id,
            )
            raise HTTPException(status_code=403, detail="Access denied")

    return PhysicalAssessmentService.serialize_session(db, session_model)


@router.get("/students", response_model=PhysicalAssessmentStudentSummaryResponse)
def get_students_view(
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Fetching physical assessment students. User: %s (ID: %s)",
        current_user.username,
        current_user.id,
    )
    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        return PhysicalAssessmentService.get_coach_view_students(db, coach_profile.id)

    return PhysicalAssessmentService.get_admin_view_students(db)


@router.get("/students/{student_id}", response_model=PhysicalAssessmentStudentDetailResponse)
def get_student_detail(
    student_id: int,
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Fetching physical assessment student detail. Student ID: %s, User: %s",
        student_id,
        current_user.username,
    )
    detail = PhysicalAssessmentService.get_student_detail(db, student_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if detail.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    return detail


@router.put("/students/{student_id}", response_model=PhysicalAssessmentStudentDetailResponse)
def update_student_results(
    student_id: int,
    payload: PhysicalAssessmentStudentUpdate,
    current_user: User = Depends(require_edit_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Updating physical assessment student results. Student ID: %s, User: %s",
        student_id,
        current_user.username,
    )

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        detail = PhysicalAssessmentService.get_student_detail(db, student_id)
        if not detail or detail.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    return PhysicalAssessmentService.update_student_results(db, student_id, payload)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_results(
    student_id: int,
    current_user: User = Depends(require_edit_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info(
        "Deleting physical assessment student results. Student ID: %s, User: %s",
        student_id,
        current_user.username,
    )

    detail = PhysicalAssessmentService.get_student_detail(db, student_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if detail.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    deleted = PhysicalAssessmentService.delete_student_results(db, student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No assessment results to delete")

    return None


@router.put("/sessions/{session_id}", response_model=PhysicalAssessmentSessionResponse)
def update_session(
    session_id: int,
    payload: PhysicalAssessmentSessionUpdate,
    current_user: User = Depends(require_edit_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info("Updating session %s. User: %s", session_id, current_user.username)

    session_model = PhysicalAssessmentService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        batch_coach_id = session_model.batch.coach_id if session_model.batch else None
        if session_model.coach_id != coach_profile.id and batch_coach_id != coach_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_session = PhysicalAssessmentService.update_session(db, session_id, payload)
        api_logger.info("Successfully updated session %s", session_id)
        return updated_session
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        api_logger.error("Failed to update session %s: %s", session_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "server_error", "message": str(exc)})


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(require_edit_sessions),
    db: Session = Depends(get_db),
):
    api_logger.info("Deleting session %s. User: %s", session_id, current_user.username)

    session_model = PhysicalAssessmentService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        batch_coach_id = session_model.batch.coach_id if session_model.batch else None
        if session_model.coach_id != coach_profile.id and batch_coach_id != coach_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    try:
        success = PhysicalAssessmentService.delete_session(db, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        api_logger.info("Successfully deleted session %s", session_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        api_logger.error("Failed to delete session %s: %s", session_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "server_error", "message": str(exc)})

    return None


@router.get("/level-mappings", response_model=PhysicalAssessmentLevelMappingResponse)
def get_level_mappings(
    current_identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    """Fetch exercise level mappings with optional coach scoping."""

    coach_id = None
    if current_identity.coach:
        coach_id = current_identity.coach.id
        api_logger.info(
            "Fetching level mappings. Coach: %s (ID: %s) - filtered",
            current_identity.coach.username,
            coach_id,
        )
    else:
        api_logger.info(
            "Fetching level mappings. User: %s (ID: %s) - all data",
            current_identity.user.username,
            current_identity.user.id,
        )

    try:
        return PhysicalAssessmentService.get_level_mappings(db, coach_id=coach_id)
    except Exception as exc:  # pragma: no cover - unexpected
        api_logger.error("Error fetching level mappings: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "server_error", "message": str(exc)})



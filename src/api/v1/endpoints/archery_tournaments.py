from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from src.api.v1.dependencies.auth import get_current_user
from src.api.v1.utils.coach import get_coach_profile_or_403
from src.core.logging import api_logger
from src.db.database import get_db
from src.db.models.user import User, UserRole
from src.schemas.archery_tournament import (
    ArcheryTournamentCategoryCreate,
    ArcheryTournamentCategoryResponse,
    ArcheryTournamentPreCreateResponse,
    ArcheryTournamentSessionCreate,
    ArcheryTournamentSessionResponse,
    ArcheryTournamentSessionSummaryResponse,
    ArcheryTournamentSessionUpdate,
)
from src.services.archery_tournament_service import ArcheryTournamentService


router = APIRouter(prefix="/archery/tournaments", tags=["Archery - Tournament"])


@router.post(
    "/categories",
    response_model=ArcheryTournamentCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tournament_category(
    payload: ArcheryTournamentCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    api_logger.info(f"Creating archery tournament category. User: {current_user.username}")
    return ArcheryTournamentService.create_category(db, payload)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tournament_category(
    category_id: int = Path(..., description="Tournament Category ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    api_logger.info(f"Deleting archery tournament category {category_id}. User: {current_user.username}")
    ArcheryTournamentService.delete_category(db, category_id)
    return None


@router.get(
    "/sessions/pre-create",
    response_model=ArcheryTournamentPreCreateResponse,
)
def get_tournament_pre_create_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    api_logger.info(f"Fetching archery tournament pre-create data. User: {current_user.username}")
    return ArcheryTournamentService.get_pre_create_data(db, current_user)


@router.post(
    "/sessions",
    response_model=ArcheryTournamentSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tournament_session(
    payload: ArcheryTournamentSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")
    api_logger.info(f"Creating archery tournament session. User: {current_user.username}")
    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        if payload.coach_id and payload.coach_id != coach_profile.id:
            raise HTTPException(status_code=403, detail="Coach may only create sessions for their own id")
        if not payload.coach_id:
            payload.coach_id = coach_profile.id
    return ArcheryTournamentService.create_session(db, payload)


@router.get(
    "/sessions",
    response_model=ArcheryTournamentSessionSummaryResponse,
)
def get_tournament_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        api_logger.info(f"Fetching archery tournament sessions (coach view). User: {current_user.username}")
        return ArcheryTournamentService.get_coach_view_sessions(db, coach_profile.id)

    api_logger.info(f"Fetching archery tournament sessions (general view). User: {current_user.username}")
    return ArcheryTournamentService.get_admin_view_sessions(db)


@router.get(
    "/sessions/view",
    response_model=ArcheryTournamentSessionSummaryResponse,
    include_in_schema=False,
)
@router.get(
    "/sessions/admin-view",
    response_model=ArcheryTournamentSessionSummaryResponse,
    include_in_schema=False,
)
@router.get(
    "/sessions/coach-view",
    response_model=ArcheryTournamentSessionSummaryResponse,
    include_in_schema=False,
)
def get_tournament_sessions_alias(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Backward-compatible aliases for legacy tournament session routes."""
    return get_tournament_sessions(current_user=current_user, db=db)


@router.get(
    "/sessions/{session_id}",
    response_model=ArcheryTournamentSessionResponse,
)
def get_tournament_session(
    session_id: int = Path(..., description="Tournament Session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_model = ArcheryTournamentService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if session_model.coach_id != coach_profile.id and session_model.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    return ArcheryTournamentService.serialize_session(db, session_model)


@router.put(
    "/sessions/{session_id}",
    response_model=ArcheryTournamentSessionResponse,
)
def update_tournament_session(
    payload: ArcheryTournamentSessionUpdate,
    session_id: int = Path(..., description="Tournament Session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    session_model = ArcheryTournamentService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if session_model.coach_id != coach_profile.id and session_model.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    updated = ArcheryTournamentService.update_session(db, session_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tournament_session(
    session_id: int = Path(..., description="Tournament Session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    session_model = ArcheryTournamentService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = get_coach_profile_or_403(current_user, db)
        assigned_batch_ids = {
            assignment.batch_id
            for assignment in getattr(coach_profile, "batch_assignments", [])
            if assignment.batch_id is not None
        }
        if session_model.coach_id != coach_profile.id and session_model.batch_id not in assigned_batch_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    ArcheryTournamentService.delete_session(db, session_id)
    return None

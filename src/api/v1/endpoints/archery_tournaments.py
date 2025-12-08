from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies.auth import get_current_user
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
    category_id: int,
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
    return ArcheryTournamentService.create_session(db, payload)


@router.get(
    "/sessions/admin-view",
    response_model=ArcheryTournamentSessionSummaryResponse,
)
def get_tournament_admin_view_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    api_logger.info(f"Fetching archery tournament sessions (admin view). User: {current_user.username}")
    return ArcheryTournamentService.get_admin_view_sessions(db)


@router.get(
    "/sessions/coach-view",
    response_model=ArcheryTournamentSessionSummaryResponse,
)
def get_tournament_coach_view_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=403, detail="Coach access required")
    coach_profile = getattr(current_user, "coach_profile", None)
    if not coach_profile:
        raise HTTPException(status_code=403, detail="Coach profile not found")
    api_logger.info(f"Fetching archery tournament sessions (coach view). User: {current_user.username}")
    return ArcheryTournamentService.get_coach_view_sessions(db, coach_profile.id)


@router.get(
    "/sessions/{session_id}",
    response_model=ArcheryTournamentSessionResponse,
)
def get_tournament_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_model = ArcheryTournamentService.get_session_model(db, session_id)
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

    return ArcheryTournamentService.serialize_session(db, session_model)


@router.put(
    "/sessions/{session_id}",
    response_model=ArcheryTournamentSessionResponse,
)
def update_tournament_session(
    session_id: int,
    payload: ArcheryTournamentSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    session_model = ArcheryTournamentService.get_session_model(db, session_id)
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

    updated = ArcheryTournamentService.update_session(db, session_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tournament_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized")

    session_model = ArcheryTournamentService.get_session_model(db, session_id)
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

    ArcheryTournamentService.delete_session(db, session_id)
    return None

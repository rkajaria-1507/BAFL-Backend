from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies.auth import get_current_user
from src.core.logging import api_logger
from src.db.database import get_db
from src.db.models.user import User, UserRole
from src.schemas.coach import (
    CoachContractDetails,
    CoachCreateRequest,
    CoachCreateResponse,
    CoachUpdateRequest,
    CoachUpdateResponse,
)
from src.services.coach_service import CoachService

router = APIRouter(prefix="/coaches", tags=["Coaches"])

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

@router.post("/", response_model=CoachCreateResponse, status_code=status.HTTP_201_CREATED)
def create_coach(
    payload: CoachCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CoachCreateResponse:
    api_logger.info(f"Creating coach '{payload.name}' by user {current_user.username} (ID: {current_user.id})")
    try:
        details = CoachService.create_coach(db, payload)
        api_logger.info(f"Successfully created coach '{details.name}' (ID: {details.coach_id})")
        return CoachCreateResponse(message="Coach created successfully", coach=details)
    except Exception as e:
        api_logger.error(f"Failed to create coach '{payload.name}': {str(e)}", exc_info=True)
        raise

@router.get("/", response_model=list[CoachContractDetails])
def get_coaches(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching coaches. User: {current_user.username} (ID: {current_user.id}), Skip: {skip}, Limit: {limit}")
    return CoachService.list_coaches(db, skip, limit)

@router.get("/{coach_id}", response_model=CoachContractDetails)
def get_coach(
    coach_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching coach details. Coach ID: {coach_id}, User: {current_user.username}")
    try:
        return CoachService.get_coach(db, coach_id)
    except HTTPException as e:
        api_logger.warning(f"Coach not found or error fetching coach {coach_id}: {e.detail}")
        raise

@router.put("/{coach_id}", response_model=CoachUpdateResponse)
def update_coach(
    coach_id: int,
    payload: CoachUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CoachUpdateResponse:
    api_logger.info(f"Updating coach {coach_id} by user {current_user.username}")
    try:
        details = CoachService.update_coach(db, coach_id, payload)
        api_logger.info(f"Successfully updated coach {coach_id}")
        return CoachUpdateResponse(message="Coach updated successfully", coach=details)
    except Exception as e:
        api_logger.error(f"Failed to update coach {coach_id}: {str(e)}", exc_info=True)
        raise

@router.delete("/{coach_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coach(
    coach_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Deleting coach {coach_id} by user {current_user.username}")
    try:
        CoachService.delete_coach(db, coach_id)
        api_logger.info(f"Successfully deleted coach {coach_id}")
    except Exception as e:
        api_logger.error(f"Failed to delete coach {coach_id}: {str(e)}", exc_info=True)
        raise
    return None

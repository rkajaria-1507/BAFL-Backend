from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.core.logging import api_logger
from src.schemas.physical_assessment import (
    PhysicalAssessmentSessionCreate, 
    PhysicalAssessmentSessionUpdate, 
    PhysicalAssessmentSessionResponse,
    PhysicalAssessmentResultUpdate,
    PhysicalAssessmentResultResponse,
    PreCreateResponse,
    PhysicalAssessmentSessionAdminViewResponse
)
from src.schemas.physical_assessment import PhysicalAssessmentSessionWithResultsCreate
from src.services.physical_assessment_service import PhysicalAssessmentService
from src.api.v1.dependencies.auth import get_current_user, require_permission
from src.db.models.user import User, UserRole
from src.db.models.permission import PermissionType
from src.utils.input_parsing import parse_request

router = APIRouter(prefix="/physical", tags=["Physical Assessments"])

# Permissions
require_view_sessions = require_permission(PermissionType.PHYSICAL_SESSIONS_VIEW)
require_edit_sessions = require_permission(PermissionType.PHYSICAL_SESSIONS_EDIT)
require_add_sessions = require_permission(PermissionType.PHYSICAL_SESSIONS_ADD)

@router.post("/sessions/create-with-results", response_model=PhysicalAssessmentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_with_results(
    payload: PhysicalAssessmentSessionWithResultsCreate,
    current_user: User = Depends(require_add_sessions),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Initiating session creation with results. User: {current_user.username} (ID: {current_user.id}), Batch ID: {payload.batch_id}")
    
    # Authorization: coaches can only create for batches they own
    if current_user.role == UserRole.COACH:
        # If coach_id provided, ensure it matches
        coach_profile = getattr(current_user, 'coach_profile', None)
        if payload.coach_id and coach_profile and payload.coach_id != coach_profile.id:
            api_logger.warning(f"Coach {current_user.username} attempted to create session for another coach ID: {payload.coach_id}")
            raise HTTPException(status_code=403, detail="Coach may only create sessions for their own id")

    try:
        new_session = PhysicalAssessmentService.create_session_with_results(db, payload, current_user)
        api_logger.info(f"Successfully created session with results. Session ID: {new_session.id}")
    except HTTPException as e:
        api_logger.warning(f"HTTPException during session creation: {e.detail}")
        raise
    except ValueError as e:
        api_logger.warning(f"Validation error during session creation: {str(e)}")
        raise HTTPException(status_code=400, detail={"code": "validation_error", "message": str(e)})
    except Exception as e:
        api_logger.error(f"Unexpected error during session creation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "server_error", "message": str(e)})

    return new_session

@router.get("/sessions/pre-create", response_model=PreCreateResponse)
def get_pre_create_data(
    current_user: User = Depends(require_add_sessions),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching pre-create data for user: {current_user.username} (ID: {current_user.id})")
    return PhysicalAssessmentService.get_pre_create_data(db, current_user)

@router.get("/sessions/admin-view", response_model=PhysicalAssessmentSessionAdminViewResponse)
def get_admin_view_sessions(
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching admin view sessions. User: {current_user.username} (ID: {current_user.id})")
    return PhysicalAssessmentService.get_admin_view_sessions(db)

@router.get("/sessions/coach-view", response_model=PhysicalAssessmentSessionAdminViewResponse)
def get_coach_view_sessions(
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching coach view sessions. User: {current_user.username} (ID: {current_user.id})")
    if current_user.role != UserRole.COACH:
        api_logger.warning(f"Non-coach user {current_user.username} attempted to access coach view")
        raise HTTPException(status_code=403, detail="Coach access required")
    
    coach_profile = getattr(current_user, "coach_profile", None)
    if not coach_profile:
        api_logger.error(f"Coach profile missing for user {current_user.username}")
        raise HTTPException(status_code=403, detail="Coach profile not found")
        
    return PhysicalAssessmentService.get_coach_view_sessions(db, coach_profile.id)

@router.get("/sessions/{session_id}", response_model=PhysicalAssessmentSessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(require_view_sessions),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching session details. Session ID: {session_id}, User: {current_user.username}")
    session_model = PhysicalAssessmentService.get_session_model(db, session_id)
    if not session_model:
        api_logger.warning(f"Session not found. Session ID: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Access denied")
        batch_coach_id = session_model.batch.coach_id if session_model.batch else None
        if session_model.coach_id != coach_profile.id and batch_coach_id != coach_profile.id:
            api_logger.warning(f"Coach {current_user.username} denied access to session {session_id}")
            raise HTTPException(status_code=403, detail="Access denied")

    return PhysicalAssessmentService.serialize_session(db, session_model)

@router.put("/sessions/{session_id}", response_model=PhysicalAssessmentSessionResponse)
def update_session(
    session_id: int,
    payload: PhysicalAssessmentSessionUpdate,
    current_user: User = Depends(require_edit_sessions),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Updating session {session_id}. User: {current_user.username}")
    
    # Check permissions/ownership if needed (similar to get_session)
    session_model = PhysicalAssessmentService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Access denied")
        # Coach can only update their own sessions or sessions for their batches
        batch_coach_id = session_model.batch.coach_id if session_model.batch else None
        if session_model.coach_id != coach_profile.id and batch_coach_id != coach_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_session = PhysicalAssessmentService.update_session(db, session_id, payload)
        api_logger.info(f"Successfully updated session {session_id}")
        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to update session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "server_error", "message": str(e)})

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(require_edit_sessions),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Deleting session {session_id}. User: {current_user.username}")
    
    session_model = PhysicalAssessmentService.get_session_model(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.COACH:
        coach_profile = getattr(current_user, "coach_profile", None)
        if not coach_profile:
            raise HTTPException(status_code=403, detail="Access denied")
        batch_coach_id = session_model.batch.coach_id if session_model.batch else None
        if session_model.coach_id != coach_profile.id and batch_coach_id != coach_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    try:
        success = PhysicalAssessmentService.delete_session(db, session_id)
        if not success:
             raise HTTPException(status_code=404, detail="Session not found")
        api_logger.info(f"Successfully deleted session {session_id}")
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to delete session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "server_error", "message": str(e)})
    return None



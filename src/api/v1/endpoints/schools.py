from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies.auth import get_current_user
from src.core.logging import api_logger
from src.db.database import get_db
from src.db.models.user import User, UserRole
from src.schemas.school import SchoolCreate, SchoolCreateResponse, SchoolResponse, SchoolUpdate
from src.services.school_service import SchoolService

router = APIRouter(prefix="/schools", tags=["Schools"])

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

@router.post("/", response_model=SchoolCreateResponse, status_code=status.HTTP_201_CREATED)
def create_school(
    payload: SchoolCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SchoolCreateResponse:
    api_logger.info(f"Creating school '{payload.name}' by user {current_user.username} (ID: {current_user.id})")
    try:
        school = SchoolService.create_school(db, payload)
        api_logger.info(f"Successfully created school '{school.name}' (ID: {school.id})")
        return SchoolCreateResponse(school_id=school.id, school_name=school.name)
    except Exception as e:
        api_logger.error(f"Failed to create school '{payload.name}': {str(e)}", exc_info=True)
        raise

@router.get("/", response_model=list[SchoolResponse])
def get_schools(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching schools. User: {current_user.username} (ID: {current_user.id}), Skip: {skip}, Limit: {limit}")
    return SchoolService.get_all_schools(db, skip, limit)

@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching school details. School ID: {school_id}, User: {current_user.username}")
    school = SchoolService.get_school(db, school_id)
    if not school:
        api_logger.warning(f"School not found. School ID: {school_id}")
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.put("/{school_id}", response_model=SchoolResponse)
def update_school(
    school_id: int,
    payload: SchoolUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Updating school {school_id} by user {current_user.username}")
    try:
        school = SchoolService.update_school(db, school_id, payload)
        if not school:
            api_logger.warning(f"School not found for update. School ID: {school_id}")
            raise HTTPException(status_code=404, detail="School not found")
        api_logger.info(f"Successfully updated school {school_id}")
        return school
    except Exception as e:
        api_logger.error(f"Failed to update school {school_id}: {str(e)}", exc_info=True)
        raise

@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Deleting school {school_id} by user {current_user.username}")
    try:
        success = SchoolService.delete_school(db, school_id)
        if not success:
            api_logger.warning(f"School not found for deletion. School ID: {school_id}")
            raise HTTPException(status_code=404, detail="School not found")
        api_logger.info(f"Successfully deleted school {school_id}")
    except Exception as e:
        api_logger.error(f"Failed to delete school {school_id}: {str(e)}", exc_info=True)
        raise
    return None

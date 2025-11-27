from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies.auth import get_current_user
from src.core.logging import api_logger
from src.db.database import get_db
from src.db.models.user import User, UserRole
from src.schemas.batch import (
    BatchCreateRequest,
    BatchCreateResponse,
    BatchDetail,
    BatchUpdateRequest,
)
from src.services.batch_service import BatchService

router = APIRouter(prefix="/batches", tags=["Batches"])

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

@router.post("/", response_model=BatchCreateResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BatchCreateResponse:
    api_logger.info(f"Creating batch '{payload.batch_name}' by user {current_user.username} (ID: {current_user.id})")
    try:
        batch = BatchService.create_batch(db, payload)
        api_logger.info(f"Successfully created batch '{batch.batch_name}' (ID: {batch.batch_id})")
        return batch
    except Exception as e:
        api_logger.error(f"Failed to create batch '{payload.batch_name}': {str(e)}", exc_info=True)
        raise

@router.get("/", response_model=list[BatchDetail])
def get_batches(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching batches. User: {current_user.username} (ID: {current_user.id}), Skip: {skip}, Limit: {limit}")
    return BatchService.get_all_batches(db, skip, limit)

@router.get("/{batch_id}", response_model=BatchDetail)
def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching batch details. Batch ID: {batch_id}, User: {current_user.username}")
    try:
        return BatchService.get_batch(db, batch_id)
    except HTTPException as e:
        api_logger.warning(f"Batch not found or error fetching batch {batch_id}: {e.detail}")
        raise

@router.put("/{batch_id}", response_model=BatchDetail)
def update_batch(
    batch_id: int,
    payload: BatchUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    api_logger.info(f"Updating batch {batch_id} by user {current_user.username}")
    try:
        batch = BatchService.update_batch(db, batch_id, payload)
        api_logger.info(f"Successfully updated batch {batch_id}")
        return batch
    except Exception as e:
        api_logger.error(f"Failed to update batch {batch_id}: {str(e)}", exc_info=True)
        raise

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch(
    batch_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Deleting batch {batch_id} by user {current_user.username}")
    try:
        BatchService.delete_batch(db, batch_id)
        api_logger.info(f"Successfully deleted batch {batch_id}")
    except Exception as e:
        api_logger.error(f"Failed to delete batch {batch_id}: {str(e)}", exc_info=True)
        raise
    return None

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.core.logging import api_logger
from src.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentChangeBatchRequest,
    StudentChangeBatchResponse,
    StudentPreCreateResponse,
)
from src.services.student_service import StudentService
from src.api.v1.dependencies.auth import get_current_user
from src.db.models.user import User, UserRole
from src.utils.input_parsing import parse_request
from pydantic import BaseModel

router = APIRouter(prefix="/students", tags=["Students"])

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, openapi_extra={"requestBody": {"content": {"application/json": {"schema": StudentCreate.model_json_schema()}}, "required": True}})
async def create_student(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Initiating student creation by user {current_user.username} (ID: {current_user.id})")
    try:
        student_data = await parse_request(request, StudentCreate)
        student = StudentService.create_student(db, student_data)
        api_logger.info(f"Successfully created student '{student.name}' (ID: {student.id})")
        return student
    except Exception as e:
        api_logger.error(f"Failed to create student: {str(e)}", exc_info=True)
        raise

@router.get("/pre-create", response_model=StudentPreCreateResponse)
def get_student_pre_create(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching student pre-create data. User: {current_user.username} (ID: {current_user.id})")
    return StudentService.get_pre_create_data(db)

@router.get("/", response_model=list[StudentResponse])
def get_students(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching students. User: {current_user.username} (ID: {current_user.id}), Skip: {skip}, Limit: {limit}")
    return StudentService.get_all_students(db, skip, limit)

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Fetching student details. Student ID: {student_id}, User: {current_user.username}")
    student = StudentService.get_student(db, student_id)
    if not student:
        api_logger.warning(f"Student not found. Student ID: {student_id}")
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/{student_id}", response_model=StudentResponse, openapi_extra={"requestBody": {"content": {"application/json": {"schema": StudentUpdate.model_json_schema()}}, "required": True}})
async def update_student(
    student_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Updating student {student_id} by user {current_user.username}")
    try:
        student_data = await parse_request(request, StudentUpdate)
        student = StudentService.update_student(db, student_id, student_data)
        if not student:
            api_logger.warning(f"Student not found for update. Student ID: {student_id}")
            raise HTTPException(status_code=404, detail="Student not found")
        api_logger.info(f"Successfully updated student {student_id}")
        return student
    except Exception as e:
        api_logger.error(f"Failed to update student {student_id}: {str(e)}", exc_info=True)
        raise

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    api_logger.info(f"Deleting student {student_id} by user {current_user.username}")
    try:
        success = StudentService.delete_student(db, student_id)
        if not success:
            api_logger.warning(f"Student not found for deletion. Student ID: {student_id}")
            raise HTTPException(status_code=404, detail="Student not found")
        api_logger.info(f"Successfully deleted student {student_id}")
    except HTTPException:
        # Let FastAPI propagate 4xx errors cleanly
        raise
    except Exception as e:
        api_logger.error(f"Failed to delete student {student_id}: {str(e)}", exc_info=True)
        raise
    return None

# Removed dedicated change-batch endpoint. Use standard PUT with `batch_id`.

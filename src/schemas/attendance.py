"""
Pydantic schemas for attendance management.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date as date_type, datetime
from enum import Enum


class AttendanceStatusEnum(str, Enum):
    """Attendance status."""
    PRESENT = "present"
    ABSENT = "absent"


class AttendanceMarkedByEnum(str, Enum):
    """Who marked the attendance."""
    COACH = "coach"
    ADMIN = "admin"


# ============= Student Attendance Schemas =============

class StudentAttendanceInput(BaseModel):
    """Input for marking individual student attendance."""
    student_id: int
    status: AttendanceStatusEnum
    notes: Optional[str] = None


class StudentAttendanceResponse(BaseModel):
    """Response for individual student attendance."""
    id: int
    session_id: int
    student_id: int
    student_name: Optional[str] = None
    status: AttendanceStatusEnum
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentAttendanceUpdate(BaseModel):
    """Update for individual student attendance."""
    status: Optional[AttendanceStatusEnum] = None
    notes: Optional[str] = None


# ============= Coach Attendance Schemas =============

class CoachAttendanceInput(BaseModel):
    """Input for marking individual coach attendance."""
    coach_id: int
    status: AttendanceStatusEnum
    notes: Optional[str] = None


class CoachAttendanceResponse(BaseModel):
    """Response for individual coach attendance."""
    id: int
    session_id: int
    coach_id: int
    coach_name: Optional[str] = None
    status: AttendanceStatusEnum
    auto_marked: bool = False
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CoachAttendanceUpdate(BaseModel):
    """Update for individual coach attendance."""
    status: Optional[AttendanceStatusEnum] = None
    notes: Optional[str] = None


# ============= Attendance Session Schemas =============

class AttendanceSessionBase(BaseModel):
    """Base schema for attendance session."""
    batch_id: int
    school_id: Optional[int] = None
    date: date_type
    notes: Optional[str] = None


class AttendanceSessionCreate(AttendanceSessionBase):
    """
    Schema for creating attendance.
    - For coaches: coach_attendances is ignored, coach is auto-marked present
    - For admins: can mark both students and coaches
    """
    student_attendances: List[StudentAttendanceInput] = Field(default_factory=list)
    coach_attendances: List[CoachAttendanceInput] = Field(default_factory=list)


# Keep these for backward compatibility
class AttendanceSessionCreateByCoach(AttendanceSessionBase):
    """
    Schema for a coach creating attendance.
    Coach is automatically marked present.
    """
    student_attendances: List[StudentAttendanceInput] = Field(default_factory=list)


class AttendanceSessionCreateByAdmin(AttendanceSessionBase):
    """
    Schema for an admin creating attendance.
    Admin can mark both students and coaches.
    """
    student_attendances: List[StudentAttendanceInput] = Field(default_factory=list)
    coach_attendances: List[CoachAttendanceInput] = Field(default_factory=list)


class AttendanceSessionUpdate(BaseModel):
    """Schema for updating an attendance session."""
    date: Optional[date_type] = None
    notes: Optional[str] = None
    student_attendances: Optional[List[StudentAttendanceInput]] = None
    coach_attendances: Optional[List[CoachAttendanceInput]] = None


class AttendanceSessionResponse(BaseModel):
    """Full response for an attendance session."""
    id: int
    batch_id: int
    batch_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    date: date_type
    marked_by_type: AttendanceMarkedByEnum
    marked_by_user_id: Optional[int] = None
    marked_by_coach_id: Optional[int] = None
    marked_by_name: Optional[str] = None
    notes: Optional[str] = None
    student_attendances: List[StudentAttendanceResponse] = Field(default_factory=list)
    coach_attendances: List[CoachAttendanceResponse] = Field(default_factory=list)
    present_count: int = 0
    absent_count: int = 0
    total_students: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceSessionSummary(BaseModel):
    """Summary of an attendance session for list views."""
    id: int
    batch_id: int
    batch_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    date: date_type
    marked_by_type: AttendanceMarkedByEnum
    marked_by_name: Optional[str] = None
    present_count: int = 0
    absent_count: int = 0
    total_students: int = 0
    coach_present_count: int = 0
    coach_absent_count: int = 0
    total_coaches: int = 0

    class Config:
        from_attributes = True


class AttendanceSessionListResponse(BaseModel):
    """Response for listing attendance sessions."""
    sessions: List[AttendanceSessionSummary] = Field(default_factory=list)
    total: int = 0


# ============= Bulk Operations =============

class BulkStudentAttendanceUpdate(BaseModel):
    """Bulk update student attendance status."""
    student_ids: List[int]
    status: AttendanceStatusEnum


class BulkCoachAttendanceUpdate(BaseModel):
    """Bulk update coach attendance status."""
    coach_ids: List[int]
    status: AttendanceStatusEnum


# ============= Student Attendance History =============

class StudentAttendanceHistoryItem(BaseModel):
    """Individual attendance record for a student."""
    session_id: int
    date: date_type
    batch_name: Optional[str] = None
    school_name: Optional[str] = None
    status: AttendanceStatusEnum
    marked_by_type: AttendanceMarkedByEnum
    marked_by_name: Optional[str] = None


class StudentAttendanceHistoryResponse(BaseModel):
    """Student attendance history."""
    student_id: int
    student_name: str
    total_sessions: int = 0
    present_count: int = 0
    absent_count: int = 0
    attendance_percentage: float = 0.0
    history: List[StudentAttendanceHistoryItem] = Field(default_factory=list)


# ============= Coach Attendance History =============

class CoachAttendanceHistoryItem(BaseModel):
    """Individual attendance record for a coach."""
    session_id: int
    date: date_type
    batch_name: Optional[str] = None
    school_name: Optional[str] = None
    status: AttendanceStatusEnum
    auto_marked: bool = False


class CoachAttendanceHistoryResponse(BaseModel):
    """Coach attendance history."""
    coach_id: int
    coach_name: str
    total_sessions: int = 0
    present_count: int = 0
    absent_count: int = 0
    attendance_percentage: float = 0.0
    history: List[CoachAttendanceHistoryItem] = Field(default_factory=list)


# ============= Pre-Create Data (similar to other sessions) =============

class AttendancePreCreateBatch(BaseModel):
    """Batch info for pre-create."""
    id: int
    name: str
    school_id: int
    school_name: Optional[str] = None


class AttendancePreCreateStudent(BaseModel):
    """Student info for pre-create."""
    id: int
    name: str
    batch_id: Optional[int] = None


class AttendancePreCreateCoach(BaseModel):
    """Coach info for pre-create."""
    id: int
    name: str


class AttendancePreCreateResponse(BaseModel):
    """Pre-create data for attendance session."""
    batches: List[AttendancePreCreateBatch] = Field(default_factory=list)
    students_by_batch: dict[int, List[AttendancePreCreateStudent]] = Field(default_factory=dict)
    coaches: List[AttendancePreCreateCoach] = Field(default_factory=list)


# ============= Date Range Filter =============

class AttendanceFilterParams(BaseModel):
    """Filter parameters for attendance queries."""
    batch_id: Optional[int] = None
    school_id: Optional[int] = None
    coach_id: Optional[int] = None
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    status: Optional[AttendanceStatusEnum] = None

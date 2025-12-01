from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from src.schemas.student import StudentResponse
from src.schemas.batch import BatchSummary
from src.schemas.school import SchoolResponse

class ArcheryShotInput(BaseModel):
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    score: int
    max_score: int = 10
    distance: float
    arrow_number: int

class ArcheryStudentResultInput(BaseModel):
    student_id: int
    shots: List[ArcheryShotInput]

class ArcheryShotResponse(BaseModel):
    id: int
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    score: int
    max_score: int = 10
    distance: float
    arrow_number: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ArcheryStudentResultResponse(BaseModel):
    student_id: int
    student: Optional[StudentResponse] = None
    shots: List[ArcheryShotResponse]

class ArcherySessionBase(BaseModel):
    coach_id: Optional[int] = None
    school_id: Optional[int] = None
    batch_id: int
    date_of_session: date

class ArcherySessionCreate(ArcherySessionBase):
    results: List[ArcheryStudentResultInput]

class ArcherySessionResponse(ArcherySessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    coach_name: Optional[str] = None
    batch: Optional[BatchSummary] = None
    school: Optional[SchoolResponse] = None
    results: List[ArcheryStudentResultResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ArcherySessionSummary(BaseModel):
    session_id: int
    batch_id: int
    batch_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    coach_id: Optional[int] = None
    coach_name: Optional[str] = None
    date_of_session: date


class ArcherySessionSummaryResponse(BaseModel):
    sessions: List[ArcherySessionSummary] = Field(default_factory=list)


class ArcheryStudentSummary(BaseModel):
    student_id: int
    student_name: str
    batch_id: Optional[int] = None
    batch_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    total_sessions: int = 0
    total_shots: int = 0
    average_score: Optional[float] = None
    last_session_date: Optional[date] = None


class ArcheryStudentSummaryResponse(BaseModel):
    students: List[ArcheryStudentSummary] = Field(default_factory=list)


class ArcheryStudentSessionDetail(BaseModel):
    session_id: int
    date_of_session: date
    coach_id: Optional[int] = None
    coach_name: Optional[str] = None
    shots: List[ArcheryShotResponse] = Field(default_factory=list)


class ArcheryStudentDetailResponse(BaseModel):
    student_id: int
    student_name: str
    batch_id: Optional[int] = None
    batch_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    sessions: List[ArcheryStudentSessionDetail] = Field(default_factory=list)


class ArcheryStudentSessionUpdate(BaseModel):
    session_id: int
    shots: List[ArcheryShotInput] = Field(default_factory=list)


class ArcheryStudentUpdate(BaseModel):
    updates: List[ArcheryStudentSessionUpdate] = Field(..., min_length=1)


class ArcherySessionUpdate(BaseModel):
    coach_id: Optional[int] = None
    school_id: Optional[int] = None
    batch_id: Optional[int] = None
    date_of_session: Optional[date] = None
    results: Optional[List[ArcheryStudentResultInput]] = None


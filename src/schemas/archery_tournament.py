from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.archery import ArcheryStudentRoundInput, ArcheryStudentRoundResponse
from src.schemas.batch import BatchSummary
from src.schemas.physical_assessment import PreCreateBatch
from src.schemas.school import SchoolResponse


class ArcheryTournamentCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=255)


class ArcheryTournamentCategoryCreate(ArcheryTournamentCategoryBase):
    pass


class ArcheryTournamentCategoryResponse(ArcheryTournamentCategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArcheryTournamentSessionBase(BaseModel):
    coach_id: Optional[int] = None
    school_id: Optional[int] = None
    batch_id: int
    category_id: Optional[int] = None
    tournament_name: str = Field(..., min_length=1, max_length=255)
    tournament_location: str = Field(..., min_length=1, max_length=255)
    date_of_session: date
    distance: float


class ArcheryTournamentSessionCreate(ArcheryTournamentSessionBase):
    results: List[ArcheryStudentRoundInput]


class ArcheryTournamentSessionUpdate(BaseModel):
    coach_id: Optional[int] = None
    school_id: Optional[int] = None
    batch_id: Optional[int] = None
    category_id: Optional[int] = None
    tournament_name: Optional[str] = Field(None, min_length=1, max_length=255)
    tournament_location: Optional[str] = Field(None, min_length=1, max_length=255)
    date_of_session: Optional[date] = None
    distance: Optional[float] = None
    results: Optional[List[ArcheryStudentRoundInput]] = None


class ArcheryTournamentSessionResponse(ArcheryTournamentSessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    coach_name: Optional[str] = None
    batch: Optional[BatchSummary] = None
    school: Optional[SchoolResponse] = None
    category: Optional[ArcheryTournamentCategoryResponse] = None
    category_name_snapshot: Optional[str] = None
    results: List[ArcheryStudentRoundResponse] = Field(default_factory=list)
    student_count: int

    class Config:
        from_attributes = True


class ArcheryTournamentSessionSummary(BaseModel):
    session_id: int
    batch_id: int
    batch_name: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    coach_id: Optional[int] = None
    coach_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    tournament_name: str
    tournament_location: str
    date_of_session: date
    distance: float
    student_count: int


class ArcheryTournamentSessionSummaryResponse(BaseModel):
    sessions: List[ArcheryTournamentSessionSummary] = Field(default_factory=list)


class ArcheryTournamentPreCreateResponse(BaseModel):
    batches: List[PreCreateBatch]
    categories: List[ArcheryTournamentCategoryResponse]

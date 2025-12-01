from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Time, func, Float, Boolean
from sqlalchemy.orm import relationship
from src.db.database import Base


class PhysicalAssessmentSession(Base):
    __tablename__ = "physical_assessment_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id", ondelete="SET NULL"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    date_of_session = Column(Date, nullable=False)
    student_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    coach = relationship("Coach", back_populates="sessions")
    school = relationship("School", back_populates="physical_sessions")
    batch = relationship("Batch", back_populates="physical_sessions")
    results = relationship("PhysicalAssessmentDetail", back_populates="session", cascade="all, delete-orphan")

    @property
    def conducted_by(self) -> int | None:
        return self.coach_id


class PhysicalAssessmentDetail(Base):
    __tablename__ = "physical_assessment_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("physical_assessment_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    discipline = Column(String(100), nullable=True)

    curl_up = Column(Integer, nullable=True)
    push_up = Column(Integer, nullable=True)
    sit_and_reach = Column(Float, nullable=True)
    walk_600m = Column(Float, nullable=True)
    dash_50m = Column(Float, nullable=True)
    bow_hold = Column(Float, nullable=True)
    plank = Column(Float, nullable=True)

    is_present = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("PhysicalAssessmentSession", back_populates="results")
    student = relationship("Student", back_populates="physical_results")

    @property
    def one_km_run_min(self) -> int:
        return int(self.walk_600m)

    @one_km_run_min.setter
    def one_km_run_min(self, value: int) -> None:
        self.walk_600m = float(value or 0)

    @property
    def one_km_run_sec(self) -> int:
        return int(round((self.walk_600m - int(self.walk_600m)) * 60)) if self.walk_600m else 0

    @one_km_run_sec.setter
    def one_km_run_sec(self, value: int) -> None:
        # Preserve fractional minutes based on seconds when legacy setters are used.
        minutes_component = int(self.walk_600m)
        fractional = (value or 0) / 60
        self.walk_600m = float(minutes_component + fractional)

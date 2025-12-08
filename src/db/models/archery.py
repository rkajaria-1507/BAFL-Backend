from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, func, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from src.db.database import Base


class ArcherySession(Base):
    __tablename__ = "archery_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id", ondelete="SET NULL"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    date_of_session = Column(Date, nullable=False)
    distance = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    coach = relationship("Coach", back_populates="archery_sessions")
    school = relationship("School", back_populates="archery_sessions")
    batch = relationship("Batch", back_populates="archery_sessions")
    results = relationship("ArcheryResult", back_populates="session", cascade="all, delete-orphan")


class ArcheryResult(Base):
    __tablename__ = "archery_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("archery_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    
    x_coordinate = Column(Float, nullable=True)
    y_coordinate = Column(Float, nullable=True)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, default=10, nullable=False)
    arrow_number = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("ArcherySession", back_populates="results")
    student = relationship("Student", back_populates="archery_results")

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            "round_number",
            "arrow_number",
            name="uq_archery_shot_per_round",
        ),
    )

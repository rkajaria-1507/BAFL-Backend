from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Date,
    Float,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.db.database import Base


class ArcheryTournamentCategory(Base):
    __tablename__ = "archery_tournament_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sessions = relationship(
        "ArcheryTournamentSession",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class ArcheryTournamentSession(Base):
    __tablename__ = "archery_tournament_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id", ondelete="SET NULL"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(Integer, ForeignKey("archery_tournament_categories.id", ondelete="SET NULL"), nullable=True)

    tournament_name = Column(String(255), nullable=False)
    tournament_location = Column(String(255), nullable=False)
    category_name_snapshot = Column(String(150), nullable=True)

    date_of_session = Column(Date, nullable=False)
    distance = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    coach = relationship("Coach", back_populates="archery_tournament_sessions")
    school = relationship("School", back_populates="archery_tournament_sessions")
    batch = relationship("Batch", back_populates="archery_tournament_sessions")
    category = relationship("ArcheryTournamentCategory", back_populates="sessions")
    results = relationship(
        "ArcheryTournamentResult",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ArcheryTournamentResult(Base):
    __tablename__ = "archery_tournament_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("archery_tournament_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)

    x_coordinate = Column(Float, nullable=True)
    y_coordinate = Column(Float, nullable=True)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, default=10, nullable=False)
    arrow_number = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("ArcheryTournamentSession", back_populates="results")
    student = relationship("Student", back_populates="archery_tournament_results")

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            "round_number",
            "arrow_number",
            name="uq_archery_tournament_shot_per_round",
        ),
    )

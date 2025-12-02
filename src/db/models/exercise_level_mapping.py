from sqlalchemy import Column, Integer, String, Float, DateTime, func
from src.db.database import Base


class ExerciseLevelMapping(Base):
    """
    Stores the level mapping criteria for each exercise.
    Each row represents one level for one exercise with its score range.
    """
    __tablename__ = "exercise_level_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exercise_name = Column(String(100), nullable=False, index=True)
    level = Column(Integer, nullable=False)  # 1 to 7
    min_score = Column(Float, nullable=False)  # Minimum score for this level (inclusive)
    max_score = Column(Float, nullable=False)  # Maximum score for this level (inclusive)
    level_score = Column(Integer, nullable=False)  # Points awarded (2, 4, 6, 7, 8, 9, 10)
    level_description = Column(String(50), nullable=False)  # work harder, must improve, etc.
    is_higher_better = Column(Integer, nullable=False, default=1)  # 1 if higher score is better, 0 if lower is better
    unit = Column(String(20), nullable=True)  # count, cm, min, sec
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ExerciseLevelMapping(exercise={self.exercise_name}, level={self.level}, range={self.min_score}-{self.max_score})>"

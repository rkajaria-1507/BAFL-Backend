from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from src.db.database import Base


class StudentExerciseAverage(Base):
    """
    Stores the average score and corresponding level for each exercise 
    for each student in each batch.
    One row per student per batch per exercise.
    """
    __tablename__ = "student_exercise_averages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_name = Column(String(100), nullable=False, index=True)
    
    average_score = Column(Float, nullable=False, default=0.0)
    current_level = Column(Integer, nullable=True)  # 1 to 7, NULL if no level mapping exists
    level_score = Column(Integer, nullable=True)  # Points for current level (2, 4, 6, 7, 8, 9, 10)
    level_description = Column(String(50), nullable=True)  # work harder, must improve, etc.
    
    session_count = Column(Integer, nullable=False, default=0)  # Number of sessions included in average
    last_updated_session_id = Column(Integer, ForeignKey("physical_assessment_sessions.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("Student")
    batch = relationship("Batch")
    school = relationship("School")
    last_session = relationship("PhysicalAssessmentSession")

    # Unique constraint: one row per student per batch per exercise
    __table_args__ = (
        UniqueConstraint('student_id', 'batch_id', 'exercise_name', name='uix_student_batch_exercise'),
    )

    def __repr__(self):
        return f"<StudentExerciseAverage(student_id={self.student_id}, batch_id={self.batch_id}, exercise={self.exercise_name}, avg={self.average_score}, level={self.current_level})>"

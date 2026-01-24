"""
Attendance models for tracking student and coach attendance.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Date,
    Boolean,
    func,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
import enum

from src.db.database import Base


class AttendanceStatus(str, enum.Enum):
    """Attendance status enumeration."""
    PRESENT = "present"
    ABSENT = "absent"


class AttendanceMarkedBy(str, enum.Enum):
    """Who marked the attendance."""
    COACH = "coach"
    ADMIN = "admin"


class AttendanceSession(Base):
    """
    Attendance session for a batch on a specific date.
    Similar to ArcherySession and PhysicalAssessmentSession.
    """
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, nullable=False, index=True)
    
    # Who created/marked this session (admin or coach)
    marked_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    marked_by_coach_id = Column(Integer, ForeignKey("coaches.id", ondelete="SET NULL"), nullable=True)
    marked_by_type = Column(SQLEnum(AttendanceMarkedBy), nullable=False)
    
    notes = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    batch = relationship("Batch", back_populates="attendance_sessions")
    school = relationship("School", back_populates="attendance_sessions")
    marked_by_user = relationship("User", foreign_keys=[marked_by_user_id])
    marked_by_coach = relationship("Coach", foreign_keys=[marked_by_coach_id], back_populates="marked_attendance_sessions")
    
    student_attendances = relationship(
        "StudentAttendance",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    coach_attendances = relationship(
        "CoachAttendance",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        # One session per batch per date
        UniqueConstraint("batch_id", "date", name="uq_attendance_session_batch_date"),
    )

    def __repr__(self) -> str:
        return f"<AttendanceSession(id={self.id}, batch_id={self.batch_id}, date={self.date})>"


class StudentAttendance(Base):
    """
    Individual student attendance record within a session.
    """
    __tablename__ = "student_attendances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.ABSENT)
    notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    session = relationship("AttendanceSession", back_populates="student_attendances")
    student = relationship("Student", back_populates="attendances")

    __table_args__ = (
        # One attendance record per student per session
        UniqueConstraint("session_id", "student_id", name="uq_student_attendance_per_session"),
    )

    def __repr__(self) -> str:
        return f"<StudentAttendance(id={self.id}, student_id={self.student_id}, status={self.status.value})>"


class CoachAttendance(Base):
    """
    Individual coach attendance record within a session.
    When a coach marks attendance for students, they are automatically marked present.
    Admins can manually mark coach attendance.
    """
    __tablename__ = "coach_attendances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.ABSENT)
    auto_marked = Column(Boolean, default=False, nullable=False)  # True if auto-marked because coach created the session
    notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    session = relationship("AttendanceSession", back_populates="coach_attendances")
    coach = relationship("Coach", back_populates="attendances")

    __table_args__ = (
        # One attendance record per coach per session
        UniqueConstraint("session_id", "coach_id", name="uq_coach_attendance_per_session"),
    )

    def __repr__(self) -> str:
        return f"<CoachAttendance(id={self.id}, coach_id={self.coach_id}, status={self.status.value})>"

"""Permission related database models."""
from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from src.db.database import Base


class PermissionType(str, enum.Enum):
    """Comprehensive permission names for the BAFL sports management system."""

    # ===== User Management =====
    CREATE_USER = "create_user"
    CREATE_COACH = "create_coach"
    CREATE_ADMIN = "create_admin"
    DELETE_USER = "delete_user"
    DELETE_COACH = "delete_coach"
    DELETE_ADMIN = "delete_admin"
    VIEW_ALL_USERS = "view_all_users"
    EDIT_ALL_USERS = "edit_all_users"
    VIEW_OWN_PROFILE = "view_own_profile"
    EDIT_OWN_PROFILE = "edit_own_profile"
    
    # ===== Permission Management =====
    ASSIGN_PERMISSIONS = "assign_permissions"
    REVOKE_PERMISSIONS = "revoke_permissions"
    VIEW_PERMISSIONS = "view_permissions"
    
    # ===== School Management =====
    SCHOOL_CREATE = "school_create"
    SCHOOL_VIEW = "school_view"
    SCHOOL_EDIT = "school_edit"
    SCHOOL_DELETE = "school_delete"
    
    # ===== Coach Management =====
    COACH_CREATE = "coach_create"
    COACH_VIEW = "coach_view"
    COACH_VIEW_ALL = "coach_view_all"
    COACH_EDIT = "coach_edit"
    COACH_DELETE = "coach_delete"
    
    # ===== Batch Management =====
    BATCH_CREATE = "batch_create"
    BATCH_VIEW = "batch_view"
    BATCH_VIEW_ALL = "batch_view_all"
    BATCH_EDIT = "batch_edit"
    BATCH_DELETE = "batch_delete"
    
    # ===== Student Management =====
    STUDENT_CREATE = "student_create"
    STUDENT_VIEW = "student_view"
    STUDENT_VIEW_ALL = "student_view_all"
    STUDENT_EDIT = "student_edit"
    STUDENT_DELETE = "student_delete"
    
    # ===== Physical Assessment Management =====
    PHYSICAL_SESSIONS_VIEW = "physical_sessions_view"
    PHYSICAL_SESSIONS_VIEW_ALL = "physical_sessions_view_all"
    PHYSICAL_SESSIONS_EDIT = "physical_sessions_edit"
    PHYSICAL_SESSIONS_ADD = "physical_sessions_add"
    PHYSICAL_SESSIONS_DELETE = "physical_sessions_delete"
    PHYSICAL_ASSESSMENT_DETAIL_VIEW = "physical_assessment_detail_view"
    PHYSICAL_ASSESSMENT_DETAIL_EDIT = "physical_assessment_detail_edit"
    PHYSICAL_ASSESSMENT_DETAIL_DELETE = "physical_assessment_detail_delete"
    PHYSICAL_LEVEL_MAPPING_VIEW = "physical_level_mapping_view"
    PHYSICAL_LEVEL_MAPPING_EDIT = "physical_level_mapping_edit"
    
    # ===== Archery Session Management =====
    ARCHERY_SESSION_CREATE = "archery_session_create"
    ARCHERY_SESSION_VIEW = "archery_session_view"
    ARCHERY_SESSION_VIEW_ALL = "archery_session_view_all"
    ARCHERY_SESSION_EDIT = "archery_session_edit"
    ARCHERY_SESSION_DELETE = "archery_session_delete"
    ARCHERY_RESULT_VIEW = "archery_result_view"
    ARCHERY_RESULT_EDIT = "archery_result_edit"
    ARCHERY_RESULT_DELETE = "archery_result_delete"
    
    # ===== Archery Tournament Management =====
    ARCHERY_TOURNAMENT_CREATE = "archery_tournament_create"
    ARCHERY_TOURNAMENT_VIEW = "archery_tournament_view"
    ARCHERY_TOURNAMENT_VIEW_ALL = "archery_tournament_view_all"
    ARCHERY_TOURNAMENT_EDIT = "archery_tournament_edit"
    ARCHERY_TOURNAMENT_DELETE = "archery_tournament_delete"
    ARCHERY_TOURNAMENT_CATEGORY_CREATE = "archery_tournament_category_create"
    ARCHERY_TOURNAMENT_CATEGORY_VIEW = "archery_tournament_category_view"
    ARCHERY_TOURNAMENT_CATEGORY_EDIT = "archery_tournament_category_edit"
    ARCHERY_TOURNAMENT_CATEGORY_DELETE = "archery_tournament_category_delete"
    ARCHERY_TOURNAMENT_RESULT_VIEW = "archery_tournament_result_view"
    ARCHERY_TOURNAMENT_RESULT_EDIT = "archery_tournament_result_edit"
    ARCHERY_TOURNAMENT_RESULT_DELETE = "archery_tournament_result_delete"
    
    # ===== Reports & Analytics =====
    REPORT_VIEW = "report_view"
    REPORT_EXPORT = "report_export"
    ANALYTICS_VIEW = "analytics_view"


class Permission(Base):
    """Permission model."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    permission_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assignments = relationship("UserPermission", back_populates="permission", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, permission_name='{self.permission_name}')>"

    @property
    def user_permissions(self):
        return self.assignments


class UserPermission(Base):
    """Flexible permission assignment spanning users and coaches."""

    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id", ondelete="CASCADE"), nullable=True, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="permissions")
    coach = relationship("Coach", foreign_keys=[coach_id], back_populates="permissions")
    permission = relationship("Permission", back_populates="assignments")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

    __table_args__ = (
        UniqueConstraint("user_id", "permission_id", name="uq_user_permissions_user"),
        UniqueConstraint("coach_id", "permission_id", name="uq_user_permissions_coach"),
        CheckConstraint(
            "(user_id IS NOT NULL) OR (coach_id IS NOT NULL)",
            name="chk_user_permissions_target",
        ),
    )

    def __repr__(self) -> str:
        target = f"user_id={self.user_id}" if self.user_id is not None else f"coach_id={self.coach_id}"
        return f"<UserPermission({target}, permission_id={self.permission_id})>"

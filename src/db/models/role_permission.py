"""
Role permission mappings stored in database.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship

from src.db.database import Base
from src.db.models.user import UserRole


class RolePermission(Base):
    """Default permissions for each role (stored in database)."""
    
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    permission = relationship("Permission")
    
    __table_args__ = (
        UniqueConstraint("role", "permission_id", name="uq_role_permission"),
    )
    
    def __repr__(self) -> str:
        return f"<RolePermission(role='{self.role.value}', permission_id={self.permission_id})>"

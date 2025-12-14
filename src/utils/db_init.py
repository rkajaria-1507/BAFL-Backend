"""
Database initialization utilities.
"""
from sqlalchemy.orm import Session

from src.db.database import SessionLocal, init_database
from src.db.models.user import User, UserRole
from src.db.models.role_permission import RolePermission
from src.db.repositories.user_repository import UserRepository
from src.db.repositories.permission_repository import PermissionRepository
from src.core.security import PasswordHandler
from src.core.logging import db_logger, api_logger
from src.core.config import settings
from src.db.models.permission import PermissionType
from src.utils.role_permissions_config import ROLE_PERMISSIONS


DEFAULT_PERMISSION_DEFINITIONS = tuple(perm.value for perm in PermissionType)


def create_initial_permissions(db: Session) -> None:
    """Create baseline permissions as plain strings."""
    api_logger.info("Creating initial permissions...")

    for permission_name in DEFAULT_PERMISSION_DEFINITIONS:
        existing = PermissionRepository.get_by_name(db, permission_name)
        if not existing:
            PermissionRepository.create(
                db,
                permission_name,
                f"Permission: {permission_name}",
            )
            api_logger.info(f"Created permission: {permission_name}")

    api_logger.info("Initial permissions created successfully")


def create_initial_admin(db: Session) -> None:
    """Create the initial admin user from environment variables."""
    api_logger.info("Checking for initial admin...")
    
    # Get credentials from environment
    username = settings.INITIAL_ADMIN_USERNAME
    name = settings.INITIAL_ADMIN_NAME
    password = settings.INITIAL_ADMIN_PASSWORD
    
    # Check if admin exists
    existing = UserRepository.get_by_username(db, username)
    
    if existing:
        api_logger.info(f"Initial admin '{username}' already exists")
        return
    
    # Create admin
    user_data = {
        "name": name,
        "username": username,
        "hashed_password": PasswordHandler.hash(password),
        "role": UserRole.ADMIN,
        "is_active": True
    }
    
    admin = UserRepository.create(db, user_data)
    api_logger.info(f"Initial admin created: {admin.username} (ID: {admin.id})")


def create_default_role_permissions(db: Session) -> None:
    """Create default role-permission mappings in the database."""
    api_logger.info("Creating default role-permission mappings...")
    
    # Clear existing role permissions to avoid duplicates
    db.query(RolePermission).delete()
    db.commit()
    
    created_count = 0
    
    for role, permissions in ROLE_PERMISSIONS.items():
        for permission_type in permissions:
            # Get the permission from database
            permission = PermissionRepository.get_by_name(db, permission_type.value)
            
            if permission:
                # Create role-permission mapping
                role_perm = RolePermission(
                    role=role,
                    permission_id=permission.id
                )
                db.add(role_perm)
                created_count += 1
            else:
                api_logger.warning(f"Permission not found: {permission_type.value}")
    
    db.commit()
    api_logger.info(f"Created {created_count} role-permission mappings")


def setup_database() -> None:
    """Initialize database with tables and seed data."""
    api_logger.info("Setting up database...")
    
    try:
        # Create tables
        init_database()
        
        # Create session for seeding
        db = SessionLocal()
        
        try:
            # Create permissions first
            create_initial_permissions(db)
            
            # Create default role-permission mappings
            create_default_role_permissions(db)
            
            # Create initial admin
            create_initial_admin(db)
            
            api_logger.info("Database setup completed successfully")
            
        except Exception as e:
            db_logger.error(f"Error during database seeding: {str(e)}")
            db.rollback()
            raise
        
        finally:
            db.close()
    
    except Exception as e:
        db_logger.error(f"Error during database setup: {str(e)}")
        raise

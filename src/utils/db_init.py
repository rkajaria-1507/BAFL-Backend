"""
Database initialization utilities.
"""
from sqlalchemy.orm import Session

from src.db.database import SessionLocal, init_database
from src.db.models.user import User, UserRole
from src.db.models.role_permission import RolePermission
from src.db.models.school import School
from src.db.models.coach import Coach
from src.db.models.batch import Batch
from src.db.models.student import Student
from src.db.models.coach_school import CoachSchool
from src.db.models.exercise_level_mapping import ExerciseLevelMapping
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


# ============================================================================
# PRODUCTION DATA DEFINITIONS
# ============================================================================

SCHOOLS_DATA = [
    {"name": "Avasara Academy", "address": "Pune, Maharashtra"},
    {"name": "Akanksha - Matoshri School", "address": "Pune, Maharashtra"},
    {"name": "Akanksha - SBP School", "address": "Pune, Maharashtra"},
]

STUDENTS_BY_SCHOOL = {
    "Avasara Academy": [
        "Aditi Bhandari", "Aditi Gupta", "Anaita", "Anam", "Anushka Jadhav",
        "Bandana", "Gayatri S", "Ishanvi", "Ishwari More", "Jaishikha Chauhan",
        "Kalyani Pawar", "Khushi", "Middhat", "Pragati Solapure", "R Srinthya",
        "Riddhi Madane", "Sayali Byelle", "Shalini", "Shifa Naqvi", "Shraddha Dhakane",
        "Shraddha Singh", "Shreya Kumari", "Shruti Suryawanshi", "Siddhi G", "Swarali D",
        "Swaranjali", "Tanishka", "Tripura Jamedar", "Vaibhavi Kawade", "Vishnupriya",
    ],
    "Akanksha - Matoshri School": [
        "Shlok L", "Adhiraj P", "Ankita K", "Radhika C", "Netra P",
        "Prachi S", "Tanishq", "Riya", "ansheta", "Rushikesh",
        "Emraan shaikh", "swaraj", "Gavrav", "Arav", "sonali s",
    ],
    "Akanksha - SBP School": [
        "KASHIFA SHAIKH", "SHRILEKHA GAJENGI", "IFARA KHAN", "ALINA BAGWAN",
        "Mohammad Raza Shaikh", "REHAN SAYYAD", "Salauddin Shaikh", "Atharva Kamble",
        "AFIFA SHARWAN", "Ummul Khair Shaikh", "Ammar Shaikh", "MH. ZAHID SHAIKH",
        "Ansh Gaikwad", "Samiksha Shahapure", "Shima Shaikh", "Maryam Sayyed",
        "Abuzar Shaikh", "Saba", "Sabiya", "mahima",
    ],
}

COACHES_DATA = [
    {"name": "Ashish Shinde", "username": "ashish", "password": "ashish456"},
    {"name": "Neha Chorghe", "username": "neha", "password": "neha7890"},
    {"name": "Shubham Gangurde", "username": "shubham", "password": "shubham123"},
]

ADMIN_USERS_DATA = [
    {"name": "Dawn Johnson", "username": "dawny", "password": "dawnyjohnson"},
    {"name": "Admin Two", "username": "admin2", "password": "admin123"},
]


def seed_schools(db: Session) -> dict:
    """Create schools and return a mapping of name -> School object."""
    api_logger.info("Seeding schools...")
    school_map = {}
    
    for school_data in SCHOOLS_DATA:
        existing = db.query(School).filter(School.name == school_data["name"]).first()
        if existing:
            school_map[school_data["name"]] = existing
        else:
            school = School(**school_data)
            db.add(school)
            db.flush()
            school_map[school.name] = school
            api_logger.info(f"Created school: {school.name}")
    
    db.commit()
    return school_map


def seed_batches(db: Session, school_map: dict) -> dict:
    """Create one batch per school (School_Team_A) and return a mapping."""
    api_logger.info("Seeding batches...")
    batch_map = {}
    
    for school_name, school in school_map.items():
        batch_name = f"{school_name}_Team_A"
        existing = db.query(Batch).filter(
            Batch.school_id == school.id,
            Batch.batch_name == batch_name
        ).first()
        
        if existing:
            batch_map[school_name] = existing
        else:
            batch = Batch(school_id=school.id, batch_name=batch_name)
            db.add(batch)
            db.flush()
            batch_map[school_name] = batch
            api_logger.info(f"Created batch: {batch.batch_name}")
    
    db.commit()
    return batch_map


def seed_students(db: Session, batch_map: dict) -> None:
    """Create students and assign to their school's batch."""
    api_logger.info("Seeding students...")
    created_count = 0
    
    for school_name, student_names in STUDENTS_BY_SCHOOL.items():
        batch = batch_map.get(school_name)
        if not batch:
            continue
        
        for student_name in student_names:
            existing = db.query(Student).filter(
                Student.name == student_name,
                Student.batch_id == batch.id
            ).first()
            
            if not existing:
                student = Student(name=student_name, age=14, batch_id=batch.id)
                db.add(student)
                created_count += 1
    
    db.commit()
    if created_count > 0:
        api_logger.info(f"Created {created_count} students")


def seed_coaches(db: Session, school_map: dict) -> None:
    """Create coaches and assign them to all schools."""
    api_logger.info("Seeding coaches...")
    
    coaches = []
    for coach_data in COACHES_DATA:
        existing = db.query(Coach).filter(Coach.username == coach_data["username"]).first()
        if existing:
            coaches.append(existing)
        else:
            coach = Coach(
                name=coach_data["name"],
                username=coach_data["username"],
                password=PasswordHandler.hash(coach_data["password"]),
                is_active=True
            )
            db.add(coach)
            db.flush()
            coaches.append(coach)
            api_logger.info(f"Created coach: {coach.name}")
    
    db.commit()
    
    # Assign all coaches to all schools
    for coach in coaches:
        for school_name, school in school_map.items():
            existing = db.query(CoachSchool).filter(
                CoachSchool.coach_id == coach.id,
                CoachSchool.school_id == school.id
            ).first()
            if not existing:
                assignment = CoachSchool(coach_id=coach.id, school_id=school.id)
                db.add(assignment)
    
    db.commit()
    api_logger.info("Coaches assigned to all schools")


def seed_admin_users(db: Session) -> None:
    """Create admin user accounts."""
    api_logger.info("Seeding admin users...")
    
    for admin_data in ADMIN_USERS_DATA:
        existing = db.query(User).filter(User.username == admin_data["username"]).first()
        if not existing:
            user = User(
                name=admin_data["name"],
                username=admin_data["username"],
                password=PasswordHandler.hash(admin_data["password"]),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(user)
            api_logger.info(f"Created admin user: {admin_data['username']}")
    
    db.commit()


def seed_exercise_level_mappings(db: Session) -> None:
    """Seed the exercise_level_mappings table with fitness assessment criteria."""
    existing_count = db.query(ExerciseLevelMapping).count()
    if existing_count > 0:
        api_logger.info(f"Exercise level mappings already exist ({existing_count} records)")
        return
    
    api_logger.info("Seeding exercise level mappings...")
    
    level_info = {
        1: {"score": 2, "description": "work harder"},
        2: {"score": 4, "description": "must improve"},
        3: {"score": 6, "description": "can do better"},
        4: {"score": 7, "description": "good"},
        5: {"score": 8, "description": "very good"},
        6: {"score": 9, "description": "athletic"},
        7: {"score": 10, "description": "sport fit"}
    }
    
    mappings = []
    
    # CURL UP (count) - Higher is better
    mappings.extend([
        {"exercise": "curl_up", "level": 1, "min": 0, "max": 14, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 2, "min": 14, "max": 15, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 3, "min": 15, "max": 20, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 4, "min": 20, "max": 21, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 5, "min": 21, "max": 23, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 6, "min": 23, "max": 24, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 7, "min": 24, "max": 999, "higher_better": 1, "unit": "count"},
    ])
    
    # PUSH UP (count) - Higher is better
    mappings.extend([
        {"exercise": "push_up", "level": 1, "min": 0, "max": 7, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 2, "min": 7, "max": 8, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 3, "min": 8, "max": 9, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 4, "min": 9, "max": 10, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 5, "min": 10, "max": 11, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 6, "min": 11, "max": 12, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 7, "min": 12, "max": 999, "higher_better": 1, "unit": "count"},
    ])
    
    # SIT AND REACH (cm) - Higher is better
    mappings.extend([
        {"exercise": "sit_and_reach", "level": 1, "min": 0, "max": 15.8, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 2, "min": 15.8, "max": 19.7, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 3, "min": 19.7, "max": 23.1, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 4, "min": 23.1, "max": 24.9, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 5, "min": 24.9, "max": 27.1, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 6, "min": 27.1, "max": 32.5, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 7, "min": 32.5, "max": 999, "higher_better": 1, "unit": "cm"},
    ])
    
    # 600M WALK (minutes) - Lower is better
    mappings.extend([
        {"exercise": "walk_600m", "level": 1, "min": 3.24, "max": 999, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 2, "min": 3.14, "max": 3.24, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 3, "min": 3.07, "max": 3.14, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 4, "min": 3.04, "max": 3.07, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 5, "min": 3.01, "max": 3.04, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 6, "min": 3.00, "max": 3.01, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 7, "min": 0, "max": 3.00, "higher_better": 0, "unit": "min"},
    ])
    
    # 50M DASH (seconds) - Lower is better
    mappings.extend([
        {"exercise": "dash_50m", "level": 1, "min": 9.5, "max": 999, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 2, "min": 9.0, "max": 9.5, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 3, "min": 8.6, "max": 9.0, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 4, "min": 8.4, "max": 8.6, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 5, "min": 8.2, "max": 8.4, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 6, "min": 8.0, "max": 8.2, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 7, "min": 0, "max": 8.0, "higher_better": 0, "unit": "sec"},
    ])
    
    # BOW HOLD (seconds) - Higher is better
    mappings.extend([
        {"exercise": "bow_hold", "level": 1, "min": 0, "max": 40, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 2, "min": 40, "max": 50, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 3, "min": 50, "max": 60, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 4, "min": 60, "max": 70, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 5, "min": 70, "max": 80, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 6, "min": 80, "max": 90, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 7, "min": 90, "max": 9999, "higher_better": 1, "unit": "sec"},
    ])
    
    # PLANK (minutes) - Higher is better
    mappings.extend([
        {"exercise": "plank", "level": 1, "min": 0, "max": 0.67, "higher_better": 1, "unit": "min"},
        {"exercise": "plank", "level": 2, "min": 0.67, "max": 1.33, "higher_better": 1, "unit": "min"},
        {"exercise": "plank", "level": 3, "min": 1.33, "max": 2.0, "higher_better": 1, "unit": "min"},
        {"exercise": "plank", "level": 4, "min": 2.0, "max": 2.67, "higher_better": 1, "unit": "min"},
        {"exercise": "plank", "level": 5, "min": 2.67, "max": 3.33, "higher_better": 1, "unit": "min"},
        {"exercise": "plank", "level": 6, "min": 3.33, "max": 4.0, "higher_better": 1, "unit": "min"},
        {"exercise": "plank", "level": 7, "min": 4.0, "max": 166.65, "higher_better": 1, "unit": "min"},
    ])
    
    # Create ExerciseLevelMapping objects
    for mapping in mappings:
        level_data = level_info[mapping["level"]]
        db_mapping = ExerciseLevelMapping(
            exercise_name=mapping["exercise"],
            level=mapping["level"],
            min_score=mapping["min"],
            max_score=mapping["max"],
            level_score=level_data["score"],
            level_description=level_data["description"],
            is_higher_better=mapping["higher_better"],
            unit=mapping["unit"]
        )
        db.add(db_mapping)
    
    db.commit()
    api_logger.info(f"Created {len(mappings)} exercise level mappings")


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
            
            # Create initial admin from environment
            create_initial_admin(db)
            
            # Seed production data (schools, batches, students, coaches, admin users)
            school_map = seed_schools(db)
            batch_map = seed_batches(db, school_map)
            seed_students(db, batch_map)
            seed_coaches(db, school_map)
            seed_admin_users(db)
            
            # Seed exercise level mappings
            seed_exercise_level_mappings(db)
            
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

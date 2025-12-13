"""
Root conftest.py - Shared fixtures for all tests
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import Base, get_db
from main import app
from src.db.models.user import User, UserRole
from src.db.models.permission import Permission, PermissionType
from src.db.models.role_permission import RolePermission
from src.db.models.school import School
from src.db.models.batch import Batch
from src.db.models.student import Student
from src.db.models.coach import Coach
from src.db.models.coach_batch import CoachBatch
from src.core.security import PasswordHandler, TokenHandler


# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine with in-memory SQLite"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a FastAPI test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def create_permissions(test_db):
    """Create all permissions in the database"""
    permissions = []
    for perm_type in PermissionType:
        perm = Permission(
            permission_name=perm_type.value,
            description=f"Permission for {perm_type.value}"
        )
        test_db.add(perm)
        permissions.append(perm)
    
    test_db.commit()
    return permissions


@pytest.fixture
def assign_admin_permissions(test_db, create_permissions):
    """Assign all permissions to admin role"""
    permissions = test_db.query(Permission).all()
    
    for perm in permissions:
        role_perm = RolePermission(
            role=UserRole.ADMIN.value,
            permission_id=perm.id
        )
        test_db.add(role_perm)
    
    test_db.commit()


@pytest.fixture
def assign_coach_permissions(test_db, create_permissions):
    """Assign coach-specific permissions"""
    # Get permissions that coaches should have
    coach_permission_types = [
        PermissionType.PHYSICAL_SESSIONS_VIEW,
        PermissionType.PHYSICAL_SESSIONS_ADD,
        PermissionType.PHYSICAL_SESSIONS_EDIT,
    ]
    
    for perm_type in coach_permission_types:
        perm = test_db.query(Permission).filter(
            Permission.permission_name == perm_type.value
        ).first()
        if perm:
            role_perm = RolePermission(
                role=UserRole.COACH.value,
                permission_id=perm.id
            )
            test_db.add(role_perm)
    
    test_db.commit()


@pytest.fixture
def admin_user(test_db, assign_admin_permissions):
    """Create an admin user with permissions"""
    from src.db.models.permission import UserPermission
    
    user = User(
        name="Test Admin",
        username="testadmin",
        hashed_password=PasswordHandler.hash("testpassword123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign PHYSICAL_SESSIONS_VIEW permission directly to the user
    view_perm = test_db.query(Permission).filter(
        Permission.permission_name == PermissionType.PHYSICAL_SESSIONS_VIEW.value
    ).first()
    
    user_perm = UserPermission(
        user_id=user.id,
        permission_id=view_perm.id
    )
    test_db.add(user_perm)
    test_db.commit()
    
    return user


@pytest.fixture
def coach_user(test_db, assign_coach_permissions):
    """Create a coach without user_id (standalone coach model)"""
    from src.db.models.permission import UserPermission
    from src.core.security import PasswordHandler
    
    coach = Coach(
        name="Test Coach",
        username="testcoach",
        password=PasswordHandler.hash("testpassword123"),
        is_active=True
    )
    test_db.add(coach)
    test_db.commit()
    test_db.refresh(coach)
    
    # Assign PHYSICAL_SESSIONS_VIEW permission directly to the coach
    view_perm = test_db.query(Permission).filter(
        Permission.permission_name == PermissionType.PHYSICAL_SESSIONS_VIEW.value
    ).first()
    
    coach_perm = UserPermission(
        coach_id=coach.id,
        permission_id=view_perm.id
    )
    test_db.add(coach_perm)
    test_db.commit()
    
    return coach


@pytest.fixture
def regular_user(test_db, create_permissions):
    """Create a regular user without PHYSICAL_SESSIONS_VIEW permission"""
    from src.db.models.permission import UserPermission
    
    user = User(
        name="Test User",
        username="testuser",
        hashed_password=PasswordHandler.hash("testpassword123"),
        role=UserRole.USER,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Don't give any permissions - will fail permission check with 403
    return user


@pytest.fixture
def admin_token(admin_user):
    """Generate JWT token for admin user"""
    token_data = {
        "sub": admin_user.username,
        "subject_type": "user",
        "user_id": admin_user.id,
        "role": admin_user.role.value
    }
    return TokenHandler.create_access_token(token_data)


@pytest.fixture
def coach_token(coach_user):
    """Generate JWT token for coach"""
    token_data = {
        "sub": coach_user.username,
        "subject_type": "coach",
        "coach_id": coach_user.id,
        "role": "coach"
    }
    return TokenHandler.create_access_token(token_data)


@pytest.fixture
def regular_token(regular_user):
    """Generate JWT token for regular user"""
    token_data = {
        "sub": regular_user.username,
        "subject_type": "user",
        "user_id": regular_user.id,
        "role": regular_user.role.value
    }
    return TokenHandler.create_access_token(token_data)


@pytest.fixture
def auth_headers_admin(admin_token):
    """Create authorization headers for admin"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_coach(coach_token):
    """Create authorization headers for coach"""
    return {"Authorization": f"Bearer {coach_token}"}


@pytest.fixture
def auth_headers_regular(regular_token):
    """Create authorization headers for regular user"""
    return {"Authorization": f"Bearer {regular_token}"}


# Sample Data Fixtures
@pytest.fixture
def sample_school(test_db):
    """Create a sample school"""
    from src.db.models.school import School
    school = School(
        name="Test High School",
        address="123 Test Street"
    )
    test_db.add(school)
    test_db.commit()
    test_db.refresh(school)
    return school


@pytest.fixture
def sample_batch(test_db, sample_school):
    """Create a sample batch"""
    from src.db.models.batch import Batch
    batch = Batch(
        school_id=sample_school.id,
        batch_name="Batch A"
    )
    test_db.add(batch)
    test_db.commit()
    test_db.refresh(batch)
    return batch


@pytest.fixture
def sample_coach(test_db):
    """Create a standalone sample coach"""
    from src.core.security import PasswordHandler
    
    coach = Coach(
        name="Sample Coach",
        username="samplecoach",
        password=PasswordHandler.hash("password123"),
        is_active=True
    )
    test_db.add(coach)
    test_db.commit()
    test_db.refresh(coach)
    return coach


@pytest.fixture
def assign_coach_to_batch(test_db, sample_coach, sample_batch):
    """Assign coach to batch"""
    coach_batch = CoachBatch(
        coach_id=sample_coach.id,
        batch_id=sample_batch.id
    )
    test_db.add(coach_batch)
    test_db.commit()
    return coach_batch


@pytest.fixture
def sample_students(test_db, sample_batch):
    """Create sample students"""
    students = []
    for i in range(3):
        student = Student(
            name=f"Student {i+1}",
            age=15 + i,
            batch_id=sample_batch.id
        )
        test_db.add(student)
        students.append(student)
    
    test_db.commit()
    for student in students:
        test_db.refresh(student)
    return students


@pytest.fixture
def sample_exercise_level_mappings(test_db):
    """Create sample exercise level mappings"""
    from src.db.models.exercise_level_mapping import ExerciseLevelMapping
    
    mappings_data = [
        # curl_up
        {"exercise_name": "curl_up", "level": 1, "min_score": 0, "max_score": 20, "level_score": 2, "level_description": "needs improvement", "is_higher_better": 1, "unit": "count"},
        {"exercise_name": "curl_up", "level": 5, "min_score": 41, "max_score": 60, "level_score": 8, "level_description": "good", "is_higher_better": 1, "unit": "count"},
        {"exercise_name": "curl_up", "level": 7, "min_score": 81, "max_score": 200, "level_score": 10, "level_description": "excellent", "is_higher_better": 1, "unit": "count"},
        # push_up
        {"exercise_name": "push_up", "level": 1, "min_score": 0, "max_score": 10, "level_score": 2, "level_description": "needs improvement", "is_higher_better": 1, "unit": "count"},
        {"exercise_name": "push_up", "level": 5, "min_score": 21, "max_score": 30, "level_score": 8, "level_description": "good", "is_higher_better": 1, "unit": "count"},
        # plank
        {"exercise_name": "plank", "level": 1, "min_score": 0, "max_score": 1.0, "level_score": 2, "level_description": "needs improvement", "is_higher_better": 1, "unit": "min"},
        {"exercise_name": "plank", "level": 5, "min_score": 2.1, "max_score": 3.0, "level_score": 8, "level_description": "good", "is_higher_better": 1, "unit": "min"},
    ]
    
    mappings = []
    for data in mappings_data:
        mapping = ExerciseLevelMapping(**data)
        test_db.add(mapping)
        mappings.append(mapping)
    
    test_db.commit()
    return mappings


@pytest.fixture
def sample_physical_session(test_db, sample_school, sample_batch, sample_coach):
    """Create a sample physical assessment session"""
    from src.db.models.physical_assessment import PhysicalAssessmentSession
    from datetime import date
    
    session = PhysicalAssessmentSession(
        coach_id=sample_coach.id,
        school_id=sample_school.id,
        batch_id=sample_batch.id,
        date_of_session=date(2025, 1, 15),
        student_count=3
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest.fixture
def sample_physical_results(test_db, sample_physical_session, sample_students):
    """Create sample physical assessment results"""
    from src.db.models.physical_assessment import PhysicalAssessmentDetail
    
    results = []
    scores = [
        {"curl_up": 50, "push_up": 25, "plank": 2.5},
        {"curl_up": 45, "push_up": 20, "plank": 2.0},
        {"curl_up": 30, "push_up": 15, "plank": 1.5},
    ]
    
    for student, score_data in zip(sample_students, scores):
        result = PhysicalAssessmentDetail(
            session_id=sample_physical_session.id,
            student_id=student.id,
            curl_up=score_data.get("curl_up"),
            push_up=score_data.get("push_up"),
            sit_and_reach=0.0,
            walk_600m=0.0,
            dash_50m=0.0,
            bow_hold=0.0,
            plank=score_data.get("plank"),
            is_present=True
        )
        test_db.add(result)
        results.append(result)
    
    test_db.commit()
    return results


@pytest.fixture
def sample_student_averages(test_db, sample_school, sample_batch, sample_students, sample_physical_session, sample_exercise_level_mappings):
    """Create sample student exercise averages with levels"""
    from src.db.models.student_exercise_average import StudentExerciseAverage
    
    averages = []
    
    # Student 1: curl_up=50 (level 5), push_up=25 (level 5)
    averages.append(StudentExerciseAverage(
        student_id=sample_students[0].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="curl_up",
        average_score=50.0,
        current_level=5,
        level_score=8,
        level_description="good",
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    averages.append(StudentExerciseAverage(
        student_id=sample_students[0].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="push_up",
        average_score=25.0,
        current_level=5,
        level_score=8,
        level_description="good",
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    # Student 2: curl_up=45 (level 5)
    averages.append(StudentExerciseAverage(
        student_id=sample_students[1].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="curl_up",
        average_score=45.0,
        current_level=5,
        level_score=8,
        level_description="good",
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    # Student 3: curl_up=30 (no level mapping)
    averages.append(StudentExerciseAverage(
        student_id=sample_students[2].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="curl_up",
        average_score=30.0,
        current_level=None,
        level_score=None,
        level_description=None,
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    for avg in averages:
        test_db.add(avg)
    
    test_db.commit()
    return averages


@pytest.fixture
def complete_test_data(
    test_db,
    sample_school,
    sample_batch,
    sample_coach,
    assign_coach_to_batch,
    sample_students,
    sample_exercise_level_mappings,
    sample_physical_session,
    sample_physical_results,
    sample_student_averages
):
    """Complete test data setup for all tests"""
    return {
        "school": sample_school,
        "batch": sample_batch,
        "coach": sample_coach,
        "students": sample_students,
        "session": sample_physical_session,
        "results": sample_physical_results,
        "averages": sample_student_averages,
        "level_mappings": sample_exercise_level_mappings
    }

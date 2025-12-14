"""
Unit tests for SchoolRepository, UserRepository, StudentRepository, and BatchRepository
Tests data access layer with mocked database operations.
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from src.db.repositories.school_repository import SchoolRepository
from src.db.repositories.user_repository import UserRepository
from src.db.repositories.student_repository import StudentRepository
from src.db.repositories.batch_repository import BatchRepository
from src.db.models.school import School
from src.db.models.user import User, UserRole
from src.db.models.student import Student
from src.db.models.batch import Batch


# ==================== SCHOOL REPOSITORY TESTS ====================

@pytest.mark.unit
class TestSchoolRepository:
    """Test school repository operations."""

    def test_create_school(self):
        """Test creating a school."""
        db = Mock(spec=Session)
        school = School(name="Test School", address="123 Test St")
        
        result = SchoolRepository.create(db, school)
        
        assert result == school
        db.add.assert_called_once_with(school)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(school)

    def test_get_by_id_found(self):
        """Test retrieving school by ID."""
        db = Mock(spec=Session)
        mock_school = Mock(spec=School)
        mock_school.id = 1
        db.scalar.return_value = mock_school
        
        result = SchoolRepository.get_by_id(db, 1)
        
        assert result == mock_school

    def test_get_by_id_not_found(self):
        """Test retrieving non-existent school."""
        db = Mock(spec=Session)
        db.scalar.return_value = None
        
        result = SchoolRepository.get_by_id(db, 999)
        
        assert result is None

    def test_get_all_schools(self):
        """Test retrieving all schools."""
        db = Mock(spec=Session)
        mock_schools = [Mock(spec=School) for _ in range(3)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_schools
        db.scalars.return_value = mock_scalars
        
        result = SchoolRepository.get_all(db)
        
        assert len(result) == 3

    def test_update_school(self):
        """Test updating school."""
        db = Mock(spec=Session)
        school = Mock(spec=School)
        school.name = "Old Name"
        
        SchoolRepository.update(db, school, {"name": "New Name"})
        
        assert school.name == "New Name"
        db.commit.assert_called_once()

    def test_delete_school(self):
        """Test deleting school."""
        db = Mock(spec=Session)
        school = Mock(spec=School)
        
        SchoolRepository.delete(db, school)
        
        db.delete.assert_called_once_with(school)
        db.commit.assert_called_once()


# ==================== USER REPOSITORY TESTS ====================

@pytest.mark.unit
class TestUserRepository:
    """Test user repository operations."""

    def test_create_user(self):
        """Test creating a user."""
        db = Mock(spec=Session)
        user_data = {
            "name": "Test User",
            "username": "testuser",
            "hashed_password": "hashed",
            "role": UserRole.ADMIN,
            "is_active": True
        }
        
        result = UserRepository.create(db, user_data)
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_get_by_id_found(self):
        """Test retrieving user by ID."""
        db = Mock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.id = 1
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        db.query.return_value = mock_query
        
        result = UserRepository.get_by_id(db, 1)
        
        assert result == mock_user

    def test_get_by_id_not_found(self):
        """Test retrieving non-existent user."""
        db = Mock(spec=Session)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query
        
        result = UserRepository.get_by_id(db, 999)
        
        assert result is None

    def test_get_by_username_found(self):
        """Test retrieving user by username."""
        db = Mock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        db.query.return_value = mock_query
        
        result = UserRepository.get_by_username(db, "testuser")
        
        assert result == mock_user

    def test_get_all_users(self):
        """Test retrieving all users."""
        db = Mock(spec=Session)
        mock_users = [Mock(spec=User) for _ in range(3)]
        
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_users
        db.query.return_value = mock_query
        
        result = UserRepository.get_all(db)
        
        assert len(result) == 3

    def test_update_user(self):
        """Test updating user."""
        db = Mock(spec=Session)
        user = Mock(spec=User)
        user.name = "Old Name"
        user.username = "olduser"
        
        UserRepository.update(db, user, {"name": "New Name"})
        
        assert user.name == "New Name"
        db.commit.assert_called_once()

    def test_delete_user(self):
        """Test deleting user."""
        db = Mock(spec=Session)
        user = Mock(spec=User)
        user.username = "testuser"
        user.id = 1
        
        UserRepository.delete(db, user)
        
        db.delete.assert_called_once_with(user)
        db.commit.assert_called_once()

    def test_exists_by_username_true(self):
        """Test username exists check returns true."""
        db = Mock(spec=Session)
        mock_user = Mock(spec=User)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        db.query.return_value = mock_query
        
        result = UserRepository.exists_by_username(db, "existinguser")
        
        assert result is True

    def test_exists_by_username_false(self):
        """Test username exists check returns false."""
        db = Mock(spec=Session)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query
        
        result = UserRepository.exists_by_username(db, "nonexistent")
        
        assert result is False


# ==================== STUDENT REPOSITORY TESTS ====================

@pytest.mark.unit
class TestStudentRepository:
    """Test student repository operations."""

    def test_create_student(self):
        """Test creating a student."""
        db = Mock(spec=Session)
        student = Student(name="Test Student", age=15, batch_id=1)
        
        result = StudentRepository.create(db, student)
        
        assert result == student
        db.add.assert_called_once_with(student)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(student)

    def test_get_by_id_found(self):
        """Test retrieving student by ID."""
        db = Mock(spec=Session)
        mock_student = Mock(spec=Student)
        mock_student.id = 1
        db.scalar.return_value = mock_student
        
        result = StudentRepository.get_by_id(db, 1)
        
        assert result == mock_student

    def test_get_by_id_not_found(self):
        """Test retrieving non-existent student."""
        db = Mock(spec=Session)
        db.scalar.return_value = None
        
        result = StudentRepository.get_by_id(db, 999)
        
        assert result is None

    def test_get_all_students(self):
        """Test retrieving all students."""
        db = Mock(spec=Session)
        mock_students = [Mock(spec=Student) for _ in range(5)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_students
        db.scalars.return_value = mock_scalars
        
        result = StudentRepository.get_all(db)
        
        assert len(result) == 5

    def test_get_by_batch(self):
        """Test retrieving students by batch."""
        db = Mock(spec=Session)
        mock_students = [Mock(spec=Student) for _ in range(3)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_students
        db.scalars.return_value = mock_scalars
        
        result = StudentRepository.get_by_batch(db, batch_id=1)
        
        assert len(result) == 3

    def test_get_by_batch_empty(self):
        """Test retrieving students from empty batch."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = StudentRepository.get_by_batch(db, batch_id=999)
        
        assert result == []

    def test_update_student(self):
        """Test updating student."""
        db = Mock(spec=Session)
        student = Mock(spec=Student)
        student.name = "Old Name"
        student.age = 14
        
        StudentRepository.update(db, student, {"name": "New Name", "age": 15})
        
        assert student.name == "New Name"
        assert student.age == 15
        db.commit.assert_called_once()

    def test_delete_student(self):
        """Test deleting student."""
        db = Mock(spec=Session)
        student = Mock(spec=Student)
        
        StudentRepository.delete(db, student)
        
        db.delete.assert_called_once_with(student)
        db.commit.assert_called_once()


# ==================== BATCH REPOSITORY TESTS ====================

@pytest.mark.unit
class TestBatchRepository:
    """Test batch repository operations."""

    def test_create_batch(self):
        """Test creating a batch."""
        db = Mock(spec=Session)
        batch = Batch(school_id=1, batch_name="Batch A")
        
        result = BatchRepository.create(db, batch)
        
        assert result == batch
        db.add.assert_called_once_with(batch)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(batch)

    def test_get_by_id_found(self):
        """Test retrieving batch by ID."""
        db = Mock(spec=Session)
        mock_batch = Mock(spec=Batch)
        mock_batch.id = 1
        db.scalar.return_value = mock_batch
        
        result = BatchRepository.get_by_id(db, 1)
        
        assert result == mock_batch

    def test_get_by_id_not_found(self):
        """Test retrieving non-existent batch."""
        db = Mock(spec=Session)
        db.scalar.return_value = None
        
        result = BatchRepository.get_by_id(db, 999)
        
        assert result is None

    def test_get_all_batches(self):
        """Test retrieving all batches."""
        db = Mock(spec=Session)
        mock_batches = [Mock(spec=Batch) for _ in range(4)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_batches
        db.scalars.return_value = mock_scalars
        
        result = BatchRepository.get_all(db)
        
        assert len(result) == 4

    def test_get_by_school(self):
        """Test retrieving batches by school."""
        db = Mock(spec=Session)
        mock_batches = [Mock(spec=Batch) for _ in range(2)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_batches
        db.scalars.return_value = mock_scalars
        
        result = BatchRepository.get_by_school(db, school_id=1)
        
        assert len(result) == 2

    def test_get_by_school_empty(self):
        """Test retrieving batches from school with no batches."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = BatchRepository.get_by_school(db, school_id=999)
        
        assert result == []

    def test_get_by_coach(self):
        """Test retrieving batches by coach."""
        db = Mock(spec=Session)
        mock_batches = [Mock(spec=Batch) for _ in range(3)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_batches
        db.scalars.return_value = mock_scalars
        
        result = BatchRepository.get_by_coach(db, coach_id=1)
        
        assert len(result) == 3

    def test_get_by_coach_none_assigned(self):
        """Test retrieving batches for coach with no assignments."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = BatchRepository.get_by_coach(db, coach_id=999)
        
        assert result == []

    def test_update_batch(self):
        """Test updating batch."""
        db = Mock(spec=Session)
        batch = Mock(spec=Batch)
        batch.batch_name = "Old Name"
        
        BatchRepository.update(db, batch, {"batch_name": "New Name"})
        
        assert batch.batch_name == "New Name"
        db.commit.assert_called_once()

    def test_delete_batch(self):
        """Test deleting batch."""
        db = Mock(spec=Session)
        batch = Mock(spec=Batch)
        
        BatchRepository.delete(db, batch)
        
        db.delete.assert_called_once_with(batch)
        db.commit.assert_called_once()


# ==================== EDGE CASE AND BOUNDARY TESTS ====================

@pytest.mark.unit
class TestRepositoryEdgeCases:
    """Test repository edge cases and boundary conditions."""

    def test_student_zero_age(self):
        """Test creating student with age 0 (boundary test)."""
        db = Mock(spec=Session)
        student = Student(name="Newborn", age=0)
        
        result = StudentRepository.create(db, student)
        
        assert result == student

    def test_student_negative_age(self):
        """Test student repository handles negative age (edge case)."""
        db = Mock(spec=Session)
        student = Student(name="Test", age=-1)
        
        # Repository should accept it (validation happens at service/API layer)
        result = StudentRepository.create(db, student)
        
        assert result == student

    def test_batch_very_long_name(self):
        """Test batch with maximum length name (boundary test)."""
        db = Mock(spec=Session)
        long_name = "B" * 150
        batch = Batch(school_id=1, batch_name=long_name)
        
        result = BatchRepository.create(db, batch)
        
        assert result == batch

    def test_school_unicode_name(self):
        """Test school with Unicode characters (edge case)."""
        db = Mock(spec=Session)
        school = School(name="École Française", address="Paris")
        
        result = SchoolRepository.create(db, school)
        
        assert result == school

    def test_user_all_roles(self):
        """Test user repository with all role types (boundary test)."""
        db = Mock(spec=Session)
        
        for role in [UserRole.ADMIN, UserRole.USER, UserRole.COACH]:
            user_data = {
                "name": f"Test {role.value}",
                "username": f"test_{role.value}",
                "hashed_password": "hashed",
                "role": role,
                "is_active": True
            }
            
            result = UserRepository.create(db, user_data)
            
            db.add.assert_called()

    def test_get_by_batch_no_students(self):
        """Test retrieving students from batch with no students (edge case)."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = StudentRepository.get_by_batch(db, 1)
        
        assert result == []
        assert isinstance(result, list)

    def test_get_by_school_no_batches(self):
        """Test retrieving batches from school with no batches (edge case)."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = BatchRepository.get_by_school(db, 1)
        
        assert result == []

    def test_update_with_none_values(self):
        """Test updating entity with None values (edge case)."""
        db = Mock(spec=Session)
        student = Mock(spec=Student)
        student.name = "Original Name"
        student.batch_id = 1
        
        update_data = {"batch_id": None}  # Removing batch assignment
        
        StudentRepository.update(db, student, update_data)
        
        assert student.batch_id is None

    def test_pagination_boundary_values(self):
        """Test pagination with boundary values (skip=0, limit=1)."""
        db = Mock(spec=Session)
        mock_students = [Mock(spec=Student)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_students
        db.scalars.return_value = mock_scalars
        
        result = StudentRepository.get_all(db, skip=0, limit=1)
        
        assert len(result) == 1

    def test_pagination_large_skip(self):
        """Test pagination with skip beyond available data (edge case)."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = StudentRepository.get_all(db, skip=1000, limit=10)
        
        assert result == []

    def test_batch_get_by_coach_multiple_batches(self):
        """Test retrieving multiple batches for same coach (boundary test)."""
        db = Mock(spec=Session)
        mock_batches = [Mock(spec=Batch) for _ in range(10)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_batches
        db.scalars.return_value = mock_scalars
        
        result = BatchRepository.get_by_coach(db, 1)
        
        assert len(result) == 10

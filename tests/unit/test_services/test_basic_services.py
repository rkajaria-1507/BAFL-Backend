"""
Unit tests for Service layers (School, User, Student, Batch, Coach)
Tests business logic with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime

from src.services.school_service import SchoolService
from src.services.user_service import UserService
from src.services.student_service import StudentService
from src.services.batch_service import BatchService
from src.services.coach_service import CoachService
from src.db.models.school import School
from src.db.models.user import User, UserRole
from src.db.models.student import Student
from src.db.models.batch import Batch
from src.db.models.coach import Coach


# ==================== SCHOOL SERVICE TESTS ====================

@pytest.mark.unit
class TestSchoolService:
    """Test school service business logic."""

    @patch('src.services.school_service.SchoolRepository')
    def test_create_school_success(self, mock_repo):
        """Test creating a school."""
        db = Mock()
        mock_school_data = Mock()
        mock_school_data.model_dump.return_value = {"name": "Test School", "address": "123 St"}
        mock_school = Mock(spec=School)
        mock_repo.create.return_value = mock_school
        
        result = SchoolService.create_school(db, mock_school_data)
        
        assert result == mock_school
        mock_repo.create.assert_called_once()

    @patch('src.services.school_service.SchoolRepository')
    def test_get_school_found(self, mock_repo):
        """Test retrieving existing school."""
        db = Mock()
        mock_school = Mock(spec=School)
        mock_school.id = 1
        mock_repo.get_by_id.return_value = mock_school
        
        result = SchoolService.get_school(db, 1)
        
        assert result == mock_school

    @patch('src.services.school_service.SchoolRepository')
    def test_get_school_not_found(self, mock_repo):
        """Test retrieving non-existent school returns None."""
        db = Mock()
        mock_repo.get_by_id.return_value = None
        
        result = SchoolService.get_school(db, 999)
        
        assert result is None

    @patch('src.services.school_service.SchoolRepository')
    def test_update_school_success(self, mock_repo):
        """Test updating school."""
        db = Mock()
        mock_school = Mock(spec=School)
        mock_update_data = Mock()
        mock_update_data.model_dump.return_value = {"name": "Updated School"}
        mock_repo.get_by_id.return_value = mock_school
        mock_repo.update.return_value = mock_school
        
        result = SchoolService.update_school(db, 1, mock_update_data)
        
        assert result == mock_school
        mock_repo.update.assert_called_once()

    @patch('src.services.school_service.SchoolRepository')
    def test_update_school_not_found(self, mock_repo):
        """Test updating non-existent school returns None."""
        db = Mock()
        mock_update_data = Mock()
        mock_update_data.model_dump.return_value = {"name": "Updated"}
        mock_repo.get_by_id.return_value = None
        
        result = SchoolService.update_school(db, 999, mock_update_data)
        
        assert result is None

    @patch('src.services.school_service.SchoolRepository')
    def test_delete_school_success(self, mock_repo):
        """Test deleting school."""
        db = Mock()
        mock_school = Mock(spec=School)
        mock_repo.get_by_id.return_value = mock_school
        
        result = SchoolService.delete_school(db, 1)
        
        assert result is True
        mock_repo.delete.assert_called_once()

    @patch('src.services.school_service.SchoolRepository')
    def test_delete_school_not_found(self, mock_repo):
        """Test deleting non-existent school returns False."""
        db = Mock()
        mock_repo.get_by_id.return_value = None
        
        result = SchoolService.delete_school(db, 999)
        
        assert result is False


# ==================== USER SERVICE TESTS ====================

@pytest.mark.unit
class TestUserService:
    """Test user service business logic."""

    @patch('src.services.user_service.CoachRepository')
    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_create_user_success(self, mock_password, mock_user_repo, mock_coach_repo):
        """Test creating a regular user."""
        db = Mock()
        creator = Mock(spec=User)
        creator.username = "admin"
        mock_password.hash.return_value = "hashed_password"
        mock_user_repo.exists_by_username.return_value = False
        mock_user = Mock(spec=User)
        mock_user_repo.create.return_value = mock_user
        
        result = UserService.create_user(db, "John Doe", "johndoe", "password", UserRole.USER, creator)
        
        assert result == mock_user
        mock_user_repo.create.assert_called_once()

    @patch('src.services.user_service.CoachRepository')
    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_create_user_coach_role_creates_coach(self, mock_password, mock_user_repo, mock_coach_repo):
        """Test creating user with COACH role also creates coach profile."""
        db = Mock()
        creator = Mock(spec=User)
        creator.username = "admin"
        mock_password.hash.return_value = "hashed_password"
        mock_user_repo.exists_by_username.return_value = False
        mock_user = Mock(spec=User)
        mock_user_repo.create.return_value = mock_user
        
        UserService.create_user(db, "Coach John", "coachjohn", "password", UserRole.COACH, creator)
        
        mock_coach_repo.create.assert_called_once()

    @patch('src.services.user_service.UserRepository')
    def test_create_user_duplicate_username(self, mock_user_repo):
        """Test creating user with existing username fails."""
        db = Mock()
        creator = Mock(spec=User)
        mock_user_repo.exists_by_username.return_value = True
        
        with pytest.raises(HTTPException) as exc_info:
            UserService.create_user(db, "John", "existinguser", "password", UserRole.USER, creator)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    @patch('src.services.user_service.UserRepository')
    def test_get_user_by_id_found(self, mock_user_repo):
        """Test retrieving existing user."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user_repo.get_by_id.return_value = mock_user
        
        result = UserService.get_user_by_id(db, 1)
        
        assert result == mock_user

    @patch('src.services.user_service.UserRepository')
    def test_get_user_by_id_not_found(self, mock_user_repo):
        """Test retrieving non-existent user raises 404."""
        db = Mock()
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            UserService.get_user_by_id(db, 999)
        
        assert exc_info.value.status_code == 404

    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_update_user_password_hashes(self, mock_password, mock_user_repo):
        """Test updating user password hashes it."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user_repo.get_by_id.return_value = mock_user
        mock_password.hash.return_value = "new_hashed"
        mock_user_repo.update.return_value = mock_user
        
        UserService.update_user(db, 1, password="newpassword")
        
        mock_password.hash.assert_called_once_with("newpassword")
        mock_user_repo.update.assert_called_once()

    @patch('src.services.user_service.UserRepository')
    def test_update_user_duplicate_username(self, mock_user_repo):
        """Test updating username to existing one fails."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user_repo.get_by_id.return_value = mock_user
        
        existing_user = Mock(spec=User)
        existing_user.id = 2
        mock_user_repo.get_by_username.return_value = existing_user
        
        with pytest.raises(HTTPException) as exc_info:
            UserService.update_user(db, 1, username="takenusername")
        
        assert exc_info.value.status_code == 400


# ==================== STUDENT SERVICE TESTS ====================

@pytest.mark.unit
class TestStudentService:
    """Test student service business logic."""

    @patch('src.services.student_service.StudentRepository')
    @patch('src.services.student_service.BatchRepository')
    def test_create_student_with_batch(self, mock_batch_repo, mock_student_repo):
        """Test creating student with batch validation."""
        db = Mock()
        mock_batch = Mock(spec=Batch)
        mock_batch_repo.get_by_id.return_value = mock_batch
        mock_student_data = Mock()
        mock_student_data.model_dump.return_value = {"name": "John", "age": 15, "batch_id": 1}
        mock_student = Mock(spec=Student)
        mock_student_repo.create.return_value = mock_student
        
        result = StudentService.create_student(db, mock_student_data)
        
        assert result == mock_student
        mock_batch_repo.get_by_id.assert_called_once_with(db, 1)

    @patch('src.services.student_service.BatchRepository')
    def test_create_student_invalid_batch(self, mock_batch_repo):
        """Test creating student with non-existent batch fails."""
        db = Mock()
        mock_batch_repo.get_by_id.return_value = None
        mock_student_data = Mock()
        mock_student_data.model_dump.return_value = {"name": "John", "age": 15, "batch_id": 999}
        
        with pytest.raises(HTTPException) as exc_info:
            StudentService.create_student(db, mock_student_data)
        
        assert exc_info.value.status_code == 404
        assert "Batch" in str(exc_info.value.detail)

    @patch('src.services.student_service.StudentRepository')
    def test_get_student_found(self, mock_student_repo):
        """Test retrieving existing student."""
        db = Mock()
        mock_student = Mock(spec=Student)
        mock_student.id = 1
        mock_student_repo.get_by_id.return_value = mock_student
        
        result = StudentService.get_student(db, 1)
        
        assert result == mock_student

    @patch('src.services.student_service.StudentRepository')
    def test_get_student_not_found(self, mock_student_repo):
        """Test retrieving non-existent student raises 404."""
        db = Mock()
        mock_student_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            StudentService.get_student(db, 999)
        
        assert exc_info.value.status_code == 404

    @patch('src.services.student_service.StudentRepository')
    @patch('src.services.student_service.BatchRepository')
    def test_get_students_by_batch(self, mock_batch_repo, mock_student_repo):
        """Test retrieving students by batch."""
        db = Mock()
        mock_batch = Mock(spec=Batch)
        mock_batch_repo.get_by_id.return_value = mock_batch
        mock_students = [Mock(spec=Student) for _ in range(3)]
        mock_student_repo.get_by_batch.return_value = mock_students
        
        result = StudentService.get_students_by_batch(db, 1)
        
        assert len(result) == 3

    @patch('src.services.student_service.BatchRepository')
    def test_get_students_by_batch_invalid_batch(self, mock_batch_repo):
        """Test retrieving students from non-existent batch fails."""
        db = Mock()
        mock_batch_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            StudentService.get_students_by_batch(db, 999)
        
        assert exc_info.value.status_code == 404

    @patch('src.services.student_service.StudentRepository')
    def test_delete_student_success(self, mock_student_repo):
        """Test deleting student."""
        db = Mock()
        mock_student = Mock(spec=Student)
        mock_student_repo.get_by_id.return_value = mock_student
        
        result = StudentService.delete_student(db, 1)
        
        assert result is True
        mock_student_repo.delete.assert_called_once()

    @patch('src.services.student_service.StudentRepository')
    def test_delete_student_not_found(self, mock_student_repo):
        """Test deleting non-existent student returns False."""
        db = Mock()
        mock_student_repo.get_by_id.return_value = None
        
        result = StudentService.delete_student(db, 999)
        
        assert result is False


# ==================== EDGE CASE AND BOUNDARY TESTS ====================

@pytest.mark.unit
class TestSchoolServiceEdgeCases:
    """Test school service edge cases and boundary conditions."""

    @patch('src.services.school_service.SchoolRepository')
    def test_create_school_empty_address(self, mock_repo):
        """Test creating school with empty address (optional field)."""
        db = Mock()
        mock_school_data = Mock()
        mock_school_data.model_dump.return_value = {"name": "School", "address": ""}
        mock_school = Mock(spec=School)
        mock_repo.create.return_value = mock_school
        
        result = SchoolService.create_school(db, mock_school_data)
        
        assert result == mock_school

    @patch('src.services.school_service.SchoolRepository')
    def test_create_school_very_long_name(self, mock_repo):
        """Test creating school with maximum length name (boundary test)."""
        db = Mock()
        long_name = "A" * 150  # Max length typically 150
        mock_school_data = Mock()
        mock_school_data.model_dump.return_value = {"name": long_name}
        mock_school = Mock(spec=School)
        mock_repo.create.return_value = mock_school
        
        result = SchoolService.create_school(db, mock_school_data)
        
        assert result == mock_school

    @patch('src.services.school_service.SchoolRepository')
    def test_create_school_special_characters_name(self, mock_repo):
        """Test creating school with special characters in name."""
        db = Mock()
        mock_school_data = Mock()
        mock_school_data.model_dump.return_value = {"name": "St. Mary's School & Academy"}
        mock_school = Mock(spec=School)
        mock_repo.create.return_value = mock_school
        
        result = SchoolService.create_school(db, mock_school_data)
        
        assert result == mock_school

    @patch('src.services.school_service.SchoolRepository')
    def test_update_school_partial_data(self, mock_repo):
        """Test updating school with partial data (exclude_unset)."""
        db = Mock()
        mock_school = Mock(spec=School)
        mock_update_data = Mock()
        mock_update_data.model_dump.return_value = {"name": "Updated"}  # Only name, no address
        mock_repo.get_by_id.return_value = mock_school
        mock_repo.update.return_value = mock_school
        
        result = SchoolService.update_school(db, 1, mock_update_data)
        
        assert result == mock_school


@pytest.mark.unit
class TestUserServiceEdgeCases:
    """Test user service edge cases and boundary conditions."""

    @patch('src.services.user_service.CoachRepository')
    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_create_user_minimum_length_username(self, mock_password, mock_user_repo, mock_coach_repo):
        """Test creating user with minimum length username (boundary test)."""
        db = Mock()
        creator = Mock(spec=User)
        mock_password.hash.return_value = "hashed"
        mock_user_repo.exists_by_username.return_value = False
        mock_user = Mock(spec=User)
        mock_user_repo.create.return_value = mock_user
        
        result = UserService.create_user(db, "A", "ab", "pass", UserRole.USER, creator)
        
        assert result == mock_user

    @patch('src.services.user_service.CoachRepository')
    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_create_user_maximum_length_username(self, mock_password, mock_user_repo, mock_coach_repo):
        """Test creating user with maximum length username (boundary test)."""
        db = Mock()
        creator = Mock(spec=User)
        long_username = "u" * 150
        mock_password.hash.return_value = "hashed"
        mock_user_repo.exists_by_username.return_value = False
        mock_user = Mock(spec=User)
        mock_user_repo.create.return_value = mock_user
        
        result = UserService.create_user(db, "Long Name", long_username, "pass", UserRole.USER, creator)
        
        assert result == mock_user

    @patch('src.services.user_service.CoachRepository')
    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_create_user_special_chars_username(self, mock_password, mock_user_repo, mock_coach_repo):
        """Test creating user with special characters in username (edge case)."""
        db = Mock()
        creator = Mock(spec=User)
        mock_password.hash.return_value = "hashed"
        mock_user_repo.exists_by_username.return_value = False
        mock_user = Mock(spec=User)
        mock_user_repo.create.return_value = mock_user
        
        result = UserService.create_user(db, "User", "test@user-123", "pass", UserRole.USER, creator)
        
        assert result == mock_user

    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_update_user_same_username(self, mock_password, mock_user_repo):
        """Test updating user with same username (should succeed)."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "sameusername"
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.get_by_username.return_value = mock_user  # Same user
        mock_user_repo.update.return_value = mock_user
        
        result = UserService.update_user(db, 1, username="sameusername")
        
        assert result == mock_user
        mock_user_repo.update.assert_called_once()

    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_update_user_empty_password(self, mock_password, mock_user_repo):
        """Test updating user without password (password=None)."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update.return_value = mock_user
        
        UserService.update_user(db, 1, name="New Name", password=None)
        
        # Password hash should not be called if password is None
        mock_password.hash.assert_not_called()

    @patch('src.services.user_service.UserRepository')
    @patch('src.services.user_service.PasswordHandler')
    def test_update_user_all_fields_none(self, mock_password, mock_user_repo):
        """Test updating user with all optional fields None (edge case)."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update.return_value = mock_user
        
        result = UserService.update_user(db, 1, name=None, username=None, password=None, is_active=None)
        
        # Should still succeed with empty update
        assert result == mock_user


@pytest.mark.unit
class TestStudentServiceEdgeCases:
    """Test student service edge cases and boundary conditions."""

    @patch('src.services.student_service.StudentRepository')
    @patch('src.services.student_service.BatchRepository')
    def test_create_student_no_batch(self, mock_batch_repo, mock_student_repo):
        """Test creating student without batch (batch_id=None)."""
        db = Mock()
        mock_student_data = Mock()
        mock_student_data.model_dump.return_value = {"name": "John", "age": 15}
        mock_student = Mock(spec=Student)
        mock_student_repo.create.return_value = mock_student
        
        result = StudentService.create_student(db, mock_student_data)
        
        assert result == mock_student
        # Batch validation should not be called if batch_id not provided
        mock_batch_repo.get_by_id.assert_not_called()

    @patch('src.services.student_service.StudentRepository')
    @patch('src.services.student_service.BatchRepository')
    def test_create_student_minimum_age(self, mock_batch_repo, mock_student_repo):
        """Test creating student with minimum age (boundary test)."""
        db = Mock()
        mock_student_data = Mock()
        mock_student_data.model_dump.return_value = {"name": "Young Student", "age": 5}
        mock_student = Mock(spec=Student)
        mock_student_repo.create.return_value = mock_student
        
        result = StudentService.create_student(db, mock_student_data)
        
        assert result == mock_student

    @patch('src.services.student_service.StudentRepository')
    @patch('src.services.student_service.BatchRepository')
    def test_create_student_maximum_age(self, mock_batch_repo, mock_student_repo):
        """Test creating student with maximum age (boundary test)."""
        db = Mock()
        mock_student_data = Mock()
        mock_student_data.model_dump.return_value = {"name": "Older Student", "age": 18}
        mock_student = Mock(spec=Student)
        mock_student_repo.create.return_value = mock_student
        
        result = StudentService.create_student(db, mock_student_data)
        
        assert result == mock_student

    @patch('src.services.student_service.StudentRepository')
    @patch('src.services.student_service.BatchRepository')
    def test_create_student_unicode_name(self, mock_batch_repo, mock_student_repo):
        """Test creating student with Unicode characters in name (edge case)."""
        db = Mock()
        mock_student_data = Mock()
        mock_student_data.model_dump.return_value = {"name": "François Müller", "age": 15}
        mock_student = Mock(spec=Student)
        mock_student_repo.create.return_value = mock_student
        
        result = StudentService.create_student(db, mock_student_data)
        
        assert result == mock_student

    @patch('src.services.student_service.StudentRepository')
    @patch('src.services.student_service.BatchRepository')
    def test_get_students_by_batch_empty_result(self, mock_batch_repo, mock_student_repo):
        """Test getting students from batch with no students (edge case)."""
        db = Mock()
        mock_batch = Mock(spec=Batch)
        mock_batch_repo.get_by_id.return_value = mock_batch
        mock_student_repo.get_by_batch.return_value = []
        
        result = StudentService.get_students_by_batch(db, 1)
        
        assert result == []
        assert isinstance(result, list)


# ==================== BATCH SERVICE TESTS ====================

@pytest.mark.unit
class TestBatchService:
    """Test batch service business logic."""

    @patch('src.services.batch_service.BatchRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_create_batch_success(self, mock_school_repo, mock_batch_repo):
        """Test creating a batch successfully."""
        db = Mock()
        
        # Mock the batch object that gets created
        def mock_add(obj):
            obj.id = 1  # Set ID when added to database
        db.add.side_effect = mock_add
        
        mock_payload = Mock()
        mock_payload.school_id = 1
        mock_payload.batch_name = "Morning Batch"
        mock_payload.schedule = None
        
        mock_school = Mock(spec=School)
        mock_school.id = 1
        mock_school.name = "Test School"
        mock_school_repo.get_by_id.return_value = mock_school
        
        result = BatchService.create_batch(db, mock_payload)
        
        assert result.batch_id == 1
        assert result.batch_name == "Morning Batch"
        assert result.school_id == 1
        db.add.assert_called_once()
        db.commit.assert_called_once()

    @patch('src.services.batch_service.BatchRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_create_batch_school_not_found(self, mock_school_repo, mock_batch_repo):
        """Test creating batch with non-existent school raises 404."""
        db = Mock()
        mock_payload = Mock()
        mock_payload.school_id = 999
        mock_school_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            BatchService.create_batch(db, mock_payload)
        
        assert exc_info.value.status_code == 404
        assert "School not found" in exc_info.value.detail

    @patch('src.services.batch_service.BatchRepository')
    def test_get_batch_found(self, mock_batch_repo):
        """Test retrieving existing batch."""
        db = Mock()
        mock_batch = Mock(spec=Batch)
        mock_batch.id = 1
        mock_batch.batch_name = "Test Batch"
        mock_batch.school_id = 1
        mock_batch.schedules = []
        mock_batch.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.updated_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.school = Mock(spec=School)
        mock_batch.school.name = "Test School"
        mock_batch_repo.get_by_id.return_value = mock_batch
        
        result = BatchService.get_batch(db, 1)
        
        assert result.batch_id == 1
        assert result.batch_name == "Test Batch"

    @patch('src.services.batch_service.BatchRepository')
    def test_get_batch_not_found(self, mock_batch_repo):
        """Test retrieving non-existent batch raises 404."""
        db = Mock()
        mock_batch_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            BatchService.get_batch(db, 999)
        
        assert exc_info.value.status_code == 404
        assert "Batch not found" in exc_info.value.detail

    @patch('src.services.batch_service.BatchRepository')
    def test_get_all_batches(self, mock_batch_repo):
        """Test retrieving all batches."""
        db = Mock()
        mock_batch1 = Mock(spec=Batch)
        mock_batch1.id = 1
        mock_batch1.batch_name = "Batch 1"
        mock_batch1.school_id = 1
        mock_batch1.schedules = []
        mock_batch1.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch1.updated_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch1.school = Mock(spec=School)
        mock_batch1.school.name = "School 1"
        
        mock_batch2 = Mock(spec=Batch)
        mock_batch2.id = 2
        mock_batch2.batch_name = "Batch 2"
        mock_batch2.school_id = 1
        mock_batch2.schedules = []
        mock_batch2.created_at = datetime(2024, 1, 2, 10, 0, 0)
        mock_batch2.updated_at = datetime(2024, 1, 2, 10, 0, 0)
        mock_batch2.school = Mock(spec=School)
        mock_batch2.school.name = "School 1"
        
        mock_batch_repo.get_all.return_value = [mock_batch1, mock_batch2]
        
        result = BatchService.get_all_batches(db, skip=0, limit=100)
        
        assert len(result) == 2
        assert result[0].batch_id == 1
        assert result[1].batch_id == 2

    @patch('src.services.batch_service.BatchRepository')
    def test_get_all_batches_empty(self, mock_batch_repo):
        """Test retrieving batches when none exist."""
        db = Mock()
        mock_batch_repo.get_all.return_value = []
        
        result = BatchService.get_all_batches(db)
        
        assert result == []
        assert isinstance(result, list)

    @patch('src.services.batch_service.BatchRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_update_batch_name(self, mock_school_repo, mock_batch_repo):
        """Test updating batch name."""
        db = Mock()
        mock_payload = Mock()
        mock_payload.batch_name = "Updated Batch Name"
        mock_payload.school_id = None
        mock_payload.schedule = None
        
        mock_batch = Mock(spec=Batch)
        mock_batch.id = 1
        mock_batch.batch_name = "Old Name"
        mock_batch.school_id = 1
        mock_batch.schedules = []
        mock_batch.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.updated_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.school = Mock(spec=School)
        mock_batch.school.name = "Test School"
        mock_batch_repo.get_by_id.return_value = mock_batch
        
        result = BatchService.update_batch(db, 1, mock_payload)
        
        assert result.batch_name == "Updated Batch Name"
        db.commit.assert_called_once()

    @patch('src.services.batch_service.BatchRepository')
    def test_update_batch_not_found(self, mock_batch_repo):
        """Test updating non-existent batch raises 404."""
        db = Mock()
        mock_payload = Mock()
        mock_batch_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            BatchService.update_batch(db, 999, mock_payload)
        
        assert exc_info.value.status_code == 404
        assert "Batch not found" in exc_info.value.detail

    @patch('src.services.batch_service.BatchRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_update_batch_change_school(self, mock_school_repo, mock_batch_repo):
        """Test updating batch school."""
        db = Mock()
        mock_payload = Mock()
        mock_payload.batch_name = None
        mock_payload.school_id = 2
        mock_payload.schedule = None
        
        mock_batch = Mock(spec=Batch)
        mock_batch.id = 1
        mock_batch.batch_name = "Test Batch"
        mock_batch.school_id = 1
        mock_batch.schedules = []
        mock_batch.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.updated_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.school = Mock(spec=School)
        mock_batch.school.name = "Old School"
        mock_batch_repo.get_by_id.return_value = mock_batch
        
        mock_new_school = Mock(spec=School)
        mock_new_school.id = 2
        mock_new_school.name = "New School"
        mock_school_repo.get_by_id.return_value = mock_new_school
        
        result = BatchService.update_batch(db, 1, mock_payload)
        
        mock_school_repo.get_by_id.assert_called_once_with(db, 2)
        db.commit.assert_called_once()

    @patch('src.services.batch_service.BatchRepository')
    def test_delete_batch_success(self, mock_batch_repo):
        """Test deleting batch successfully."""
        db = Mock()
        mock_batch = Mock(spec=Batch)
        mock_batch.id = 1
        mock_batch_repo.get_by_id.return_value = mock_batch
        
        BatchService.delete_batch(db, 1)
        
        db.delete.assert_called_once_with(mock_batch)
        db.commit.assert_called_once()

    @patch('src.services.batch_service.BatchRepository')
    def test_delete_batch_not_found(self, mock_batch_repo):
        """Test deleting non-existent batch raises 404."""
        db = Mock()
        mock_batch_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            BatchService.delete_batch(db, 999)
        
        assert exc_info.value.status_code == 404
        assert "Batch not found" in exc_info.value.detail

    @patch('src.services.batch_service.CoachRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_get_batch_pre_create_data(self, mock_school_repo, mock_coach_repo):
        """Test getting pre-create data for batch creation."""
        db = Mock()
        
        mock_school = Mock(spec=School)
        mock_school.id = 1
        mock_school.name = "Test School"
        mock_school_repo.get_all.return_value = [mock_school]
        
        mock_coach = Mock()
        mock_coach.id = 1
        mock_coach.name = "Test Coach"
        mock_assignment = Mock()
        mock_assignment.school_id = 1
        mock_coach.school_assignments = [mock_assignment]
        mock_coach_repo.get_all.return_value = [mock_coach]
        
        result = BatchService.get_batch_pre_create_data(db)
        
        assert len(result.schools) == 1
        assert result.schools[0].school_id == 1
        assert len(result.days_of_week) == 7
        assert "Monday" in result.days_of_week


@pytest.mark.unit
class TestBatchServiceEdgeCases:
    """Test edge cases for BatchService."""

    @patch('src.services.batch_service.BatchRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_create_batch_with_very_long_name(self, mock_school_repo, mock_batch_repo):
        """Test creating batch with maximum length name (boundary test)."""
        db = Mock()
        
        # Mock the batch object that gets created
        def mock_add(obj):
            obj.id = 1  # Set ID when added to database
        db.add.side_effect = mock_add
        
        long_name = "A" * 150
        mock_payload = Mock()
        mock_payload.school_id = 1
        mock_payload.batch_name = long_name
        mock_payload.schedule = None
        
        mock_school = Mock(spec=School)
        mock_school.id = 1
        mock_school.name = "Test School"
        mock_school_repo.get_by_id.return_value = mock_school
        
        result = BatchService.create_batch(db, mock_payload)
        
        assert result.batch_name == long_name
        assert len(result.batch_name) == 150

    @patch('src.services.batch_service.BatchRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_create_batch_with_special_characters(self, mock_school_repo, mock_batch_repo):
        """Test creating batch with special characters in name (edge case)."""
        db = Mock()
        
        # Mock the batch object that gets created
        def mock_add(obj):
            obj.id = 1  # Set ID when added to database
        db.add.side_effect = mock_add
        
        special_name = "Batch-2024@Morning#Group"
        mock_payload = Mock()
        mock_payload.school_id = 1
        mock_payload.batch_name = special_name
        mock_payload.schedule = None
        
        mock_school = Mock(spec=School)
        mock_school.id = 1
        mock_school.name = "Test School"
        mock_school_repo.get_by_id.return_value = mock_school
        
        result = BatchService.create_batch(db, mock_payload)
        
        assert result.batch_name == special_name

    @patch('src.services.batch_service.BatchRepository')
    def test_get_batch_with_no_school(self, mock_batch_repo):
        """Test retrieving batch when school is None (edge case)."""
        db = Mock()
        mock_batch = Mock(spec=Batch)
        mock_batch.id = 1
        mock_batch.batch_name = "Test Batch"
        mock_batch.school_id = 1
        mock_batch.schedules = []
        mock_batch.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.updated_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.school = None
        mock_batch_repo.get_by_id.return_value = mock_batch
        
        result = BatchService.get_batch(db, 1)
        
        assert result.school_name == ""

    @patch('src.services.batch_service.BatchRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_update_batch_with_none_values(self, mock_school_repo, mock_batch_repo):
        """Test updating batch with all None values (edge case)."""
        db = Mock()
        mock_payload = Mock()
        mock_payload.batch_name = None
        mock_payload.school_id = None
        mock_payload.schedule = None
        
        mock_batch = Mock(spec=Batch)
        mock_batch.id = 1
        mock_batch.batch_name = "Original Name"
        mock_batch.school_id = 1
        mock_batch.schedules = []
        mock_batch.created_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.updated_at = datetime(2024, 1, 1, 10, 0, 0)
        mock_batch.school = Mock(spec=School)
        mock_batch.school.name = "Test School"
        mock_batch_repo.get_by_id.return_value = mock_batch
        
        result = BatchService.update_batch(db, 1, mock_payload)
        
        # Should not raise error, just no changes
        assert result.batch_name == "Original Name"

    @patch('src.services.batch_service.CoachRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_get_pre_create_data_with_no_coaches(self, mock_school_repo, mock_coach_repo):
        """Test pre-create data when no coaches exist (edge case)."""
        db = Mock()
        
        mock_school = Mock(spec=School)
        mock_school.id = 1
        mock_school.name = "Test School"
        mock_school_repo.get_all.return_value = [mock_school]
        mock_coach_repo.get_all.return_value = []
        
        result = BatchService.get_batch_pre_create_data(db)
        
        assert len(result.schools) == 1
        assert len(result.schools[0].coaches) == 0

    @patch('src.services.batch_service.CoachRepository')
    @patch('src.services.batch_service.SchoolRepository')
    def test_get_pre_create_data_with_coach_no_assignments(self, mock_school_repo, mock_coach_repo):
        """Test pre-create data with coach that has no school assignments (edge case)."""
        db = Mock()
        
        mock_school = Mock(spec=School)
        mock_school.id = 1
        mock_school.name = "Test School"
        mock_school_repo.get_all.return_value = [mock_school]
        
        mock_coach = Mock()
        mock_coach.id = 1
        mock_coach.name = "Unassigned Coach"
        mock_coach.school_assignments = []
        mock_coach_repo.get_all.return_value = [mock_coach]
        
        result = BatchService.get_batch_pre_create_data(db)
        
        assert len(result.schools) == 1
        assert len(result.schools[0].coaches) == 0

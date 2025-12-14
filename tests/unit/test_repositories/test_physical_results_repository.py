"""
Unit tests for PhysicalResultsRepository
Tests data access layer for physical assessment results with mocked database.
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from src.db.repositories.physical_results_repository import PhysicalResultsRepository
from src.db.models.physical_assessment import PhysicalAssessmentDetail


@pytest.mark.unit
class TestPhysicalResultsRepositoryCreate:
    """Test result creation operations."""

    def test_create_result_success(self):
        """Test creating a physical assessment result."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(
            session_id=1,
            student_id=1,
            curl_up=50,
            push_up=30,
            is_present=True
        )
        
        created = PhysicalResultsRepository.create(mock_db, result)
        
        mock_db.add.assert_called_once_with(result)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(result)
        assert created == result

    def test_create_result_with_all_exercises(self):
        """Test creating result with all 7 exercises."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(
            session_id=1,
            student_id=1,
            curl_up=50,
            push_up=30,
            sit_and_reach=15.5,
            walk_600m=8.2,
            dash_50m=7.1,
            bow_hold=60.0,
            plank=3.5,
            is_present=True
        )
        
        created = PhysicalResultsRepository.create(mock_db, result)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_result_absent_student(self):
        """Test creating result for absent student (all nulls)."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(
            session_id=1,
            student_id=1,
            is_present=False
        )
        
        created = PhysicalResultsRepository.create(mock_db, result)
        
        assert created.is_present is False
        mock_db.commit.assert_called_once()

    def test_create_all_bulk_insert(self):
        """Test bulk creating multiple results."""
        mock_db = Mock(spec=Session)
        results = [
            PhysicalAssessmentDetail(session_id=1, student_id=1, curl_up=50),
            PhysicalAssessmentDetail(session_id=1, student_id=2, curl_up=45),
            PhysicalAssessmentDetail(session_id=1, student_id=3, curl_up=55)
        ]
        
        created = PhysicalResultsRepository.create_all(mock_db, results)
        
        mock_db.add_all.assert_called_once_with(results)
        mock_db.commit.assert_called_once()
        assert len(created) == 3


@pytest.mark.unit
class TestPhysicalResultsRepositoryRead:
    """Test result retrieval operations."""

    def test_get_by_id_found(self):
        """Test retrieving result by ID when it exists."""
        mock_db = Mock(spec=Session)
        expected_result = PhysicalAssessmentDetail(id=1, student_id=1)
        mock_db.scalar.return_value = expected_result
        
        result = PhysicalResultsRepository.get_by_id(mock_db, 1)
        
        assert result == expected_result
        mock_db.scalar.assert_called_once()

    def test_get_by_id_not_found(self):
        """Test retrieving result by ID when it doesn't exist."""
        mock_db = Mock(spec=Session)
        mock_db.scalar.return_value = None
        
        result = PhysicalResultsRepository.get_by_id(mock_db, 999)
        
        assert result is None

    def test_get_by_session(self):
        """Test retrieving all results for a session."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        results = [
            PhysicalAssessmentDetail(id=1, session_id=5, student_id=1),
            PhysicalAssessmentDetail(id=2, session_id=5, student_id=2)
        ]
        mock_scalars.all.return_value = results
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalResultsRepository.get_by_session(mock_db, 5)
        
        assert len(result) == 2
        assert all(r.session_id == 5 for r in result)

    def test_get_by_session_empty(self):
        """Test retrieving results for session with no results."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalResultsRepository.get_by_session(mock_db, 999)
        
        assert result == []

    def test_get_by_student(self):
        """Test retrieving all results for a student."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        results = [
            PhysicalAssessmentDetail(id=1, session_id=1, student_id=10),
            PhysicalAssessmentDetail(id=2, session_id=2, student_id=10)
        ]
        mock_scalars.all.return_value = results
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalResultsRepository.get_by_student(mock_db, 10)
        
        assert len(result) == 2
        assert all(r.student_id == 10 for r in result)

    def test_get_by_session_and_student_found(self):
        """Test retrieving specific result by session and student."""
        mock_db = Mock(spec=Session)
        expected_result = PhysicalAssessmentDetail(
            id=1, 
            session_id=5, 
            student_id=10
        )
        mock_db.scalar.return_value = expected_result
        
        result = PhysicalResultsRepository.get_by_session_and_student(
            mock_db, 5, 10
        )
        
        assert result == expected_result
        assert result.session_id == 5
        assert result.student_id == 10

    def test_get_by_session_and_student_not_found(self):
        """Test retrieving non-existent session-student combination."""
        mock_db = Mock(spec=Session)
        mock_db.scalar.return_value = None
        
        result = PhysicalResultsRepository.get_by_session_and_student(
            mock_db, 999, 888
        )
        
        assert result is None


@pytest.mark.unit
class TestPhysicalResultsRepositoryUpdate:
    """Test result update operations."""

    def test_update_result_single_exercise(self):
        """Test updating single exercise value."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(id=1, curl_up=50)
        update_data = {"curl_up": 60}
        
        updated = PhysicalResultsRepository.update(mock_db, result, update_data)
        
        assert result.curl_up == 60
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(result)

    def test_update_result_multiple_exercises(self):
        """Test updating multiple exercise values."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(
            id=1, 
            curl_up=50, 
            push_up=30,
            plank=2.5
        )
        update_data = {
            "curl_up": 55,
            "push_up": 35,
            "plank": 3.0
        }
        
        updated = PhysicalResultsRepository.update(mock_db, result, update_data)
        
        assert result.curl_up == 55
        assert result.push_up == 35
        assert result.plank == 3.0
        mock_db.commit.assert_called_once()

    def test_update_result_set_null(self):
        """Test updating exercise value to None."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(id=1, curl_up=50)
        update_data = {"curl_up": None}
        
        updated = PhysicalResultsRepository.update(mock_db, result, update_data)
        
        assert result.curl_up is None
        mock_db.commit.assert_called_once()

    def test_update_result_empty_dict(self):
        """Test updating result with empty dictionary."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(id=1, curl_up=50)
        original_curl_up = result.curl_up
        
        updated = PhysicalResultsRepository.update(mock_db, result, {})
        
        assert result.curl_up == original_curl_up
        mock_db.commit.assert_called_once()


@pytest.mark.unit
class TestPhysicalResultsRepositoryDelete:
    """Test result deletion operations."""

    def test_delete_single_result(self):
        """Test deleting a single result."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(id=1)
        
        PhysicalResultsRepository.delete(mock_db, result)
        
        mock_db.delete.assert_called_once_with(result)
        mock_db.commit.assert_called_once()

    def test_delete_by_student_with_results(self):
        """Test bulk deleting all results for a student."""
        mock_db = Mock(spec=Session)
        mock_result = Mock()
        mock_result.rowcount = 5
        mock_db.execute.return_value = mock_result
        
        deleted_count = PhysicalResultsRepository.delete_by_student(mock_db, 10)
        
        assert deleted_count == 5
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_by_student_no_results(self):
        """Test deleting results for student with no results."""
        mock_db = Mock(spec=Session)
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result
        
        deleted_count = PhysicalResultsRepository.delete_by_student(mock_db, 999)
        
        assert deleted_count == 0
        mock_db.commit.assert_called_once()

    def test_delete_by_student_none_rowcount(self):
        """Test handling None rowcount from database."""
        mock_db = Mock(spec=Session)
        mock_result = Mock()
        mock_result.rowcount = None
        mock_db.execute.return_value = mock_result
        
        deleted_count = PhysicalResultsRepository.delete_by_student(mock_db, 10)
        
        assert deleted_count == 0


@pytest.mark.unit
class TestPhysicalResultsRepositoryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_result_with_zero_values(self):
        """Test creating result with zero values (valid for some exercises)."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(
            session_id=1,
            student_id=1,
            curl_up=0,  # Valid: did 0 reps
            push_up=0,
            is_present=True
        )
        
        created = PhysicalResultsRepository.create(mock_db, result)
        
        assert created.curl_up == 0
        mock_db.commit.assert_called_once()

    def test_create_result_with_float_values(self):
        """Test creating result with float exercise values."""
        mock_db = Mock(spec=Session)
        result = PhysicalAssessmentDetail(
            session_id=1,
            student_id=1,
            sit_and_reach=15.75,
            walk_600m=7.33,
            plank=3.14159
        )
        
        created = PhysicalResultsRepository.create(mock_db, result)
        
        assert created.sit_and_reach == 15.75
        assert created.plank == 3.14159
        mock_db.commit.assert_called_once()

    def test_get_by_student_multiple_sessions(self):
        """Test retrieving student results across multiple sessions."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        results = [
            PhysicalAssessmentDetail(session_id=1, student_id=5),
            PhysicalAssessmentDetail(session_id=2, student_id=5),
            PhysicalAssessmentDetail(session_id=3, student_id=5)
        ]
        mock_scalars.all.return_value = results
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalResultsRepository.get_by_student(mock_db, 5)
        
        assert len(result) == 3
        assert all(r.student_id == 5 for r in result)

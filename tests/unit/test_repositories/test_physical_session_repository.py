"""
Unit tests for PhysicalSessionRepository
Tests data access layer with mocked database operations.
"""
import pytest
from unittest.mock import Mock, MagicMock, call
from sqlalchemy.orm import Session

from src.db.repositories.physical_session_repository import PhysicalSessionRepository
from src.db.models.physical_assessment import PhysicalAssessmentSession


@pytest.mark.unit
class TestPhysicalSessionRepositoryCreate:
    """Test session creation operations."""

    def test_create_session_success(self):
        """Test creating a physical assessment session."""
        # Arrange
        mock_db = Mock(spec=Session)
        session = PhysicalAssessmentSession(
            coach_id=1,
            school_id=1,
            batch_id=1,
            date_of_session="2025-01-15",
            student_count=2
        )
        
        # Act
        result = PhysicalSessionRepository.create(mock_db, session)
        
        # Assert
        mock_db.add.assert_called_once_with(session)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(session)
        assert result == session

    def test_create_session_with_none_coach(self):
        """Test creating session with None coach_id (allowed)."""
        mock_db = Mock(spec=Session)
        session = PhysicalAssessmentSession(
            coach_id=None,
            school_id=1,
            batch_id=1,
            date_of_session="2025-01-15",
            student_count=0
        )
        
        result = PhysicalSessionRepository.create(mock_db, session)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.coach_id is None


@pytest.mark.unit
class TestPhysicalSessionRepositoryRead:
    """Test session retrieval operations."""

    def test_get_by_id_found(self):
        """Test retrieving session by ID when it exists."""
        mock_db = Mock(spec=Session)
        expected_session = PhysicalAssessmentSession(id=1, coach_id=1, batch_id=1)
        mock_db.scalar.return_value = expected_session
        
        result = PhysicalSessionRepository.get_by_id(mock_db, 1)
        
        assert result == expected_session
        mock_db.scalar.assert_called_once()

    def test_get_by_id_not_found(self):
        """Test retrieving session by ID when it doesn't exist."""
        mock_db = Mock(spec=Session)
        mock_db.scalar.return_value = None
        
        result = PhysicalSessionRepository.get_by_id(mock_db, 999)
        
        assert result is None

    def test_get_all_with_defaults(self):
        """Test retrieving all sessions with default pagination."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        sessions = [
            PhysicalAssessmentSession(id=1),
            PhysicalAssessmentSession(id=2)
        ]
        mock_scalars.all.return_value = sessions
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalSessionRepository.get_all(mock_db)
        
        assert len(result) == 2
        mock_db.scalars.assert_called_once()

    def test_get_all_with_pagination(self):
        """Test retrieving sessions with custom pagination."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalSessionRepository.get_all(mock_db, skip=10, limit=5)
        
        assert isinstance(result, list)
        mock_db.scalars.assert_called_once()

    def test_get_by_batch(self):
        """Test retrieving sessions by batch ID."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        sessions = [
            PhysicalAssessmentSession(id=1, batch_id=5),
            PhysicalAssessmentSession(id=2, batch_id=5)
        ]
        mock_scalars.all.return_value = sessions
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalSessionRepository.get_by_batch(mock_db, 5)
        
        assert len(result) == 2
        assert all(s.batch_id == 5 for s in result)

    def test_get_by_batch_empty(self):
        """Test retrieving sessions by batch with no results."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalSessionRepository.get_by_batch(mock_db, 999)
        
        assert result == []

    def test_get_by_coach(self):
        """Test retrieving sessions by coach ID."""
        mock_db = Mock(spec=Session)
        mock_scalars = Mock()
        sessions = [PhysicalAssessmentSession(id=1, coach_id=3)]
        mock_scalars.all.return_value = sessions
        mock_db.scalars.return_value = mock_scalars
        
        result = PhysicalSessionRepository.get_by_coach(mock_db, 3)
        
        assert len(result) == 1
        assert result[0].coach_id == 3


@pytest.mark.unit
class TestPhysicalSessionRepositoryUpdate:
    """Test session update operations."""

    def test_update_session_single_field(self):
        """Test updating single field of a session."""
        mock_db = Mock(spec=Session)
        session = PhysicalAssessmentSession(id=1, student_count=2)
        update_data = {"student_count": 5}
        
        result = PhysicalSessionRepository.update(mock_db, session, update_data)
        
        assert session.student_count == 5
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(session)
        assert result == session

    def test_update_session_multiple_fields(self):
        """Test updating multiple fields of a session."""
        mock_db = Mock(spec=Session)
        session = PhysicalAssessmentSession(
            id=1, 
            date_of_session="2025-01-15",
            student_count=2
        )
        update_data = {
            "date_of_session": "2025-02-20",
            "student_count": 3
        }
        
        result = PhysicalSessionRepository.update(mock_db, session, update_data)
        
        assert session.date_of_session == "2025-02-20"
        assert session.student_count == 3
        mock_db.commit.assert_called_once()

    def test_update_session_empty_dict(self):
        """Test updating session with empty dictionary (no changes)."""
        mock_db = Mock(spec=Session)
        session = PhysicalAssessmentSession(id=1, student_count=2)
        original_count = session.student_count
        
        result = PhysicalSessionRepository.update(mock_db, session, {})
        
        assert session.student_count == original_count
        mock_db.commit.assert_called_once()


@pytest.mark.unit
class TestPhysicalSessionRepositoryDelete:
    """Test session deletion operations."""

    def test_delete_session(self):
        """Test deleting a physical assessment session."""
        mock_db = Mock(spec=Session)
        session = PhysicalAssessmentSession(id=1)
        
        PhysicalSessionRepository.delete(mock_db, session)
        
        mock_db.delete.assert_called_once_with(session)
        mock_db.commit.assert_called_once()

    def test_delete_session_with_results(self):
        """Test deleting session (cascade delete of results handled by DB)."""
        mock_db = Mock(spec=Session)
        session = PhysicalAssessmentSession(id=1)
        
        PhysicalSessionRepository.delete(mock_db, session)
        
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

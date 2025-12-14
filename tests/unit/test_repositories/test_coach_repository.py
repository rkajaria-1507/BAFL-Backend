"""
Unit tests for CoachRepository
Tests data access layer with mocked database operations.
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from src.db.repositories.coach_repository import CoachRepository
from src.db.models.coach import Coach


@pytest.mark.unit
class TestCoachRepositoryCreate:
    """Test coach creation operations."""

    def test_create_coach_success(self):
        """Test creating a coach."""
        db = Mock(spec=Session)
        coach = Coach(
            name="John Coach",
            username="johncoach",
            password="hashed_password",
            is_active=True
        )
        
        result = CoachRepository.create(db, coach)
        
        assert result == coach
        db.add.assert_called_once_with(coach)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(coach)


@pytest.mark.unit
class TestCoachRepositoryRead:
    """Test coach read operations."""

    def test_get_by_id_found(self):
        """Test retrieving coach by ID when exists."""
        db = Mock(spec=Session)
        mock_coach = Mock(spec=Coach)
        mock_coach.id = 1
        mock_coach.username = "coach1"
        
        db.scalar.return_value = mock_coach
        
        result = CoachRepository.get_by_id(db, 1)
        
        assert result == mock_coach
        db.scalar.assert_called_once()

    def test_get_by_id_not_found(self):
        """Test retrieving coach by ID when not exists."""
        db = Mock(spec=Session)
        db.scalar.return_value = None
        
        result = CoachRepository.get_by_id(db, 999)
        
        assert result is None

    def test_get_by_username_found(self):
        """Test retrieving coach by username when exists."""
        db = Mock(spec=Session)
        mock_coach = Mock(spec=Coach)
        mock_coach.username = "testcoach"
        
        db.scalar.return_value = mock_coach
        
        result = CoachRepository.get_by_username(db, "testcoach")
        
        assert result == mock_coach
        assert result.username == "testcoach"

    def test_get_by_username_not_found(self):
        """Test retrieving coach by username when not exists."""
        db = Mock(spec=Session)
        db.scalar.return_value = None
        
        result = CoachRepository.get_by_username(db, "nonexistent")
        
        assert result is None

    def test_get_all_coaches(self):
        """Test retrieving all coaches."""
        db = Mock(spec=Session)
        mock_coaches = [Mock(spec=Coach) for _ in range(3)]
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_coaches
        db.scalars.return_value = mock_scalars
        
        result = CoachRepository.get_all(db, skip=0, limit=100)
        
        assert len(result) == 3
        assert result == mock_coaches

    def test_get_all_empty(self):
        """Test retrieving coaches when database is empty."""
        db = Mock(spec=Session)
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = CoachRepository.get_all(db)
        
        assert result == []

    def test_get_all_with_pagination(self):
        """Test retrieving coaches with pagination."""
        db = Mock(spec=Session)
        mock_coaches = [Mock(spec=Coach) for _ in range(2)]
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_coaches
        db.scalars.return_value = mock_scalars
        
        result = CoachRepository.get_all(db, skip=10, limit=2)
        
        assert len(result) == 2


@pytest.mark.unit
class TestCoachRepositoryUpdate:
    """Test coach update operations."""

    def test_update_coach_single_field(self):
        """Test updating single coach field."""
        db = Mock(spec=Session)
        coach = Mock(spec=Coach)
        coach.name = "Old Name"
        
        update_data = {"name": "New Name"}
        
        result = CoachRepository.update(db, coach, update_data)
        
        assert coach.name == "New Name"
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(coach)
        assert result == coach

    def test_update_coach_multiple_fields(self):
        """Test updating multiple coach fields."""
        db = Mock(spec=Session)
        coach = Mock(spec=Coach)
        coach.name = "Old Name"
        coach.is_active = True
        
        update_data = {"name": "Updated Name", "is_active": False}
        
        CoachRepository.update(db, coach, update_data)
        
        assert coach.name == "Updated Name"
        assert coach.is_active is False

    def test_update_coach_empty_data(self):
        """Test updating coach with empty data."""
        db = Mock(spec=Session)
        coach = Mock(spec=Coach)
        coach.name = "Unchanged"
        
        CoachRepository.update(db, coach, {})
        
        assert coach.name == "Unchanged"
        db.commit.assert_called_once()


@pytest.mark.unit
class TestCoachRepositoryDelete:
    """Test coach deletion operations."""

    def test_delete_coach_success(self):
        """Test deleting a coach."""
        db = Mock(spec=Session)
        coach = Mock(spec=Coach)
        
        CoachRepository.delete(db, coach)
        
        db.delete.assert_called_once_with(coach)
        db.commit.assert_called_once()


@pytest.mark.unit
class TestCoachRepositoryEdgeCases:
    """Test coach repository edge cases and boundary conditions."""

    def test_create_coach_inactive(self):
        """Test creating inactive coach (boundary condition)."""
        db = Mock(spec=Session)
        coach = Coach(
            name="Inactive Coach",
            username="inactivecoach",
            password="hashed",
            is_active=False
        )
        
        result = CoachRepository.create(db, coach)
        
        assert result == coach
        assert result.is_active is False

    def test_create_coach_special_chars_username(self):
        """Test creating coach with special characters in username."""
        db = Mock(spec=Session)
        coach = Coach(
            name="Special Coach",
            username="coach@test-123",
            password="hashed",
            is_active=True
        )
        
        result = CoachRepository.create(db, coach)
        
        assert result == coach

    def test_get_by_username_case_sensitivity(self):
        """Test username lookup is case-sensitive (edge case)."""
        db = Mock(spec=Session)
        mock_coach = Mock(spec=Coach)
        mock_coach.username = "CoachName"
        db.scalar.return_value = mock_coach
        
        result = CoachRepository.get_by_username(db, "CoachName")
        
        assert result == mock_coach

    def test_get_all_with_zero_limit(self):
        """Test get all coaches with limit=0 (boundary test)."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = CoachRepository.get_all(db, skip=0, limit=0)
        
        assert result == []

    def test_get_all_large_skip(self):
        """Test get all coaches with very large skip value (boundary test)."""
        db = Mock(spec=Session)
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars
        
        result = CoachRepository.get_all(db, skip=10000, limit=100)
        
        assert result == []

    def test_update_coach_to_inactive(self):
        """Test updating coach to inactive status (edge case)."""
        db = Mock(spec=Session)
        coach = Mock(spec=Coach)
        coach.is_active = True
        
        update_data = {"is_active": False}
        
        CoachRepository.update(db, coach, update_data)
        
        assert coach.is_active is False

    def test_update_coach_password(self):
        """Test updating coach password (edge case)."""
        db = Mock(spec=Session)
        coach = Mock(spec=Coach)
        coach.password = "old_hashed"
        
        update_data = {"password": "new_hashed"}
        
        CoachRepository.update(db, coach, update_data)
        
        assert coach.password == "new_hashed"

    def test_update_coach_username(self):
        """Test updating coach username (edge case)."""
        db = Mock(spec=Session)
        coach = Mock(spec=Coach)
        coach.username = "oldusername"
        
        update_data = {"username": "newusername"}
        
        CoachRepository.update(db, coach, update_data)
        
        assert coach.username == "newusername"

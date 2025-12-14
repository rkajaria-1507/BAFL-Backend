"""
Unit tests for Archery Tournament Repository classes.
Tests ArcheryTournamentCategoryRepository, ArcheryTournamentSessionRepository, and ArcheryTournamentResultRepository with mocked database Session.
"""
from datetime import date, datetime
from unittest.mock import Mock, MagicMock
import pytest

from src.db.repositories.archery_tournament_repository import (
    ArcheryTournamentCategoryRepository,
    ArcheryTournamentSessionRepository,
    ArcheryTournamentResultRepository,
)
from src.db.models.archery_tournament import (
    ArcheryTournamentCategory,
    ArcheryTournamentSession,
    ArcheryTournamentResult,
)


class TestArcheryTournamentCategoryRepository:
    """Test ArcheryTournamentCategoryRepository CRUD operations"""

    def test_create_category_success(self):
        """Test creating tournament category"""
        db = Mock()
        category = ArcheryTournamentCategory(
            name="U12 Boys",
            description="Under 12 Boys Category"
        )

        result = ArcheryTournamentCategoryRepository.create(db, category)

        assert result == category
        db.add.assert_called_once_with(category)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(category)

    def test_create_category_female(self):
        """Test creating category for female participants"""
        db = Mock()
        category = ArcheryTournamentCategory(
            name="U14 Girls",
            description="Under 14 Girls Category"
        )

        result = ArcheryTournamentCategoryRepository.create(db, category)

        assert result == category
        assert result.name == "U14 Girls"
        db.add.assert_called_once()

    def test_get_all_categories_empty(self):
        """Test getting all categories when none exist"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentCategoryRepository.get_all(db)

        assert result == []
        db.scalars.assert_called_once()

    def test_get_all_categories_multiple(self):
        """Test getting all categories when multiple exist"""
        db = Mock()
        mock_categories = [
            Mock(spec=ArcheryTournamentCategory, id=1, name="U12 Boys"),
            Mock(spec=ArcheryTournamentCategory, id=2, name="U14 Boys"),
            Mock(spec=ArcheryTournamentCategory, id=3, name="U16 Girls"),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_categories
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentCategoryRepository.get_all(db)

        assert len(result) == 3
        assert result == mock_categories

    def test_get_by_id_found(self):
        """Test retrieving category by ID when exists"""
        db = Mock()
        mock_category = Mock(spec=ArcheryTournamentCategory)
        mock_category.id = 1
        mock_category.name = "U12 Boys"

        db.scalar.return_value = mock_category

        result = ArcheryTournamentCategoryRepository.get_by_id(db, 1)

        assert result == mock_category
        assert result.id == 1
        db.scalar.assert_called_once()

    def test_get_by_id_not_found(self):
        """Test retrieving category by ID when not exists"""
        db = Mock()
        db.scalar.return_value = None

        result = ArcheryTournamentCategoryRepository.get_by_id(db, 999)

        assert result is None

    def test_get_by_name_found(self):
        """Test retrieving category by name when exists"""
        db = Mock()
        mock_category = Mock(spec=ArcheryTournamentCategory)
        mock_category.name = "U12 Boys"

        db.scalar.return_value = mock_category

        result = ArcheryTournamentCategoryRepository.get_by_name(db, "U12 Boys")

        assert result == mock_category
        assert result.name == "U12 Boys"
        db.scalar.assert_called_once()

    def test_get_by_name_not_found(self):
        """Test retrieving category by name when not exists"""
        db = Mock()
        db.scalar.return_value = None

        result = ArcheryTournamentCategoryRepository.get_by_name(db, "Non-existent Category")

        assert result is None

    def test_get_by_name_case_sensitive(self):
        """Test that name lookup is case-sensitive"""
        db = Mock()
        db.scalar.return_value = None

        result = ArcheryTournamentCategoryRepository.get_by_name(db, "u12 boys")

        assert result is None

    def test_delete_category_success(self):
        """Test deleting tournament category"""
        db = Mock()
        mock_result = Mock()
        mock_result.rowcount = 1
        db.execute.return_value = mock_result

        result = ArcheryTournamentCategoryRepository.delete(db, 1)

        assert result is True
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_category_non_existent(self):
        """Test deleting non-existent category (no-op)"""
        db = Mock()
        mock_result = Mock()
        mock_result.rowcount = 0
        db.execute.return_value = mock_result

        result = ArcheryTournamentCategoryRepository.delete(db, 999)

        assert result is False
        db.execute.assert_called_once()
        db.commit.assert_called_once()


class TestArcheryTournamentSessionRepository:
    """Test ArcheryTournamentSessionRepository CRUD operations"""

    def test_create_tournament_session_success(self):
        """Test creating tournament session"""
        db = Mock()
        session = ArcheryTournamentSession(
            category_id=1,
            coach_id=100,
            school_id=10,
            date_of_session=date(2024, 3, 20),
            distance=30
        )

        result = ArcheryTournamentSessionRepository.create(db, session)

        assert result == session
        db.add.assert_called_once_with(session)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(session)

    def test_create_tournament_session_without_coach(self):
        """Test creating tournament session without coach"""
        db = Mock()
        session = ArcheryTournamentSession(
            category_id=1,
            coach_id=None,
            school_id=10,
            date_of_session=date(2024, 3, 20),
            distance=50
        )

        result = ArcheryTournamentSessionRepository.create(db, session)

        assert result == session
        assert result.coach_id is None
        db.add.assert_called_once()

    def test_create_tournament_session_different_distances(self):
        """Test creating sessions with different distances (18, 30, 50)"""
        db = Mock()
        
        for distance in [18, 30, 50]:
            session = ArcheryTournamentSession(
                category_id=1,
                coach_id=100,
                school_id=10,
                date_of_session=date(2024, 3, 20),
                distance=distance
            )
            
            result = ArcheryTournamentSessionRepository.create(db, session)
            
            assert result.distance == distance

    def test_get_by_id_found(self):
        """Test retrieving tournament session by ID when exists"""
        db = Mock()
        mock_session = Mock(spec=ArcheryTournamentSession)
        mock_session.id = 1
        mock_session.category_id = 1
        mock_session.distance = 30

        db.scalar.return_value = mock_session

        result = ArcheryTournamentSessionRepository.get_by_id(db, 1)

        assert result == mock_session
        assert result.id == 1
        db.scalar.assert_called_once()

    def test_get_by_id_not_found(self):
        """Test retrieving tournament session by ID when not exists"""
        db = Mock()
        db.scalar.return_value = None

        result = ArcheryTournamentSessionRepository.get_by_id(db, 999)

        assert result is None

    def test_get_all_tournament_sessions_empty(self):
        """Test getting all tournament sessions when none exist"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentSessionRepository.get_all(db)

        assert result == []
        db.scalars.assert_called_once()

    def test_get_all_tournament_sessions_multiple(self):
        """Test getting all tournament sessions when multiple exist"""
        db = Mock()
        mock_sessions = [
            Mock(spec=ArcheryTournamentSession, id=1, category_id=1, distance=18),
            Mock(spec=ArcheryTournamentSession, id=2, category_id=2, distance=30),
            Mock(spec=ArcheryTournamentSession, id=3, category_id=1, distance=50),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_sessions
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentSessionRepository.get_all(db)

        assert len(result) == 3
        assert result == mock_sessions


class TestArcheryTournamentResultRepository:
    """Test ArcheryTournamentResultRepository CRUD and bulk operations"""

    def test_create_all_empty_list(self):
        """Test bulk creating tournament results with empty list"""
        db = Mock()
        results = []

        ArcheryTournamentResultRepository.create_all(db, results)

        db.add_all.assert_called_once_with(results)
        db.commit.assert_called_once()

    def test_create_all_single_result(self):
        """Test bulk creating single tournament result"""
        db = Mock()
        result = ArcheryTournamentResult(
            session_id=1,
            student_id=10,
            round_number=1,
            x_coordinate=15.5,
            y_coordinate=20.3,
            score=10,
            max_score=10,
            arrow_number=1
        )
        results = [result]

        ArcheryTournamentResultRepository.create_all(db, results)

        db.add_all.assert_called_once_with(results)
        db.commit.assert_called_once()

    def test_create_all_multiple_results(self):
        """Test bulk creating multiple tournament results"""
        db = Mock()
        results = [
            ArcheryTournamentResult(session_id=1, student_id=10, round_number=1, x_coordinate=10.5, y_coordinate=20.3, score=9, max_score=10, arrow_number=1),
            ArcheryTournamentResult(session_id=1, student_id=10, round_number=1, x_coordinate=15.2, y_coordinate=18.7, score=8, max_score=10, arrow_number=2),
            ArcheryTournamentResult(session_id=1, student_id=10, round_number=1, x_coordinate=5.1, y_coordinate=25.9, score=7, max_score=10, arrow_number=3),
        ]

        ArcheryTournamentResultRepository.create_all(db, results)

        db.add_all.assert_called_once_with(results)
        assert len(results) == 3
        db.commit.assert_called_once()

    def test_create_all_with_zero_score(self):
        """Test creating tournament result with zero score (edge case)"""
        db = Mock()
        result = ArcheryTournamentResult(
            session_id=1,
            student_id=10,
            round_number=1,
            x_coordinate=50.0,
            y_coordinate=50.0,
            score=0,
            max_score=10,
            arrow_number=1
        )
        results = [result]

        ArcheryTournamentResultRepository.create_all(db, results)

        assert results[0].score == 0
        db.add_all.assert_called_once_with(results)

    def test_create_all_with_max_score(self):
        """Test creating tournament result with maximum score (bullseye)"""
        db = Mock()
        result = ArcheryTournamentResult(
            session_id=1,
            student_id=10,
            round_number=1,
            x_coordinate=0.0,
            y_coordinate=0.0,
            score=10,
            max_score=10,
            arrow_number=1
        )
        results = [result]

        ArcheryTournamentResultRepository.create_all(db, results)

        assert results[0].score == 10
        assert results[0].score == results[0].max_score
        db.add_all.assert_called_once_with(results)

    def test_get_by_session_found(self):
        """Test getting tournament results by session ID when exists"""
        db = Mock()
        mock_results = [
            Mock(spec=ArcheryTournamentResult, session_id=1, student_id=10, round_number=1),
            Mock(spec=ArcheryTournamentResult, session_id=1, student_id=11, round_number=1),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_results
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentResultRepository.get_by_session(db, 1)

        assert len(result) == 2
        assert result == mock_results
        db.scalars.assert_called_once()

    def test_get_by_session_not_found(self):
        """Test getting tournament results by session ID when none exist"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentResultRepository.get_by_session(db, 999)

        assert result == []

    def test_get_by_student_found(self):
        """Test getting all tournament results for a student"""
        db = Mock()
        mock_results = [
            Mock(spec=ArcheryTournamentResult, session_id=1, student_id=10, round_number=1),
            Mock(spec=ArcheryTournamentResult, session_id=2, student_id=10, round_number=1),
            Mock(spec=ArcheryTournamentResult, session_id=3, student_id=10, round_number=2),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_results
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentResultRepository.get_by_student(db, 10)

        assert len(result) == 3
        assert all(r.student_id == 10 for r in result)

    def test_get_by_student_not_found(self):
        """Test getting tournament results for student with no results"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcheryTournamentResultRepository.get_by_student(db, 999)

        assert result == []

    def test_delete_by_session_success(self):
        """Test deleting all tournament results for a session"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryTournamentResultRepository.delete_by_session(db, 1)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_by_session_non_existent(self):
        """Test deleting tournament results for non-existent session (no-op)"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryTournamentResultRepository.delete_by_session(db, 999)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_for_student_in_session_success(self):
        """Test deleting specific student's tournament results in a session"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryTournamentResultRepository.delete_for_student_in_session(db, 1, 10)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_for_student_in_session_non_existent(self):
        """Test deleting non-existent student's tournament results (no-op)"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryTournamentResultRepository.delete_for_student_in_session(db, 999, 999)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_by_student_success(self):
        """Test deleting all tournament results for a student across all sessions"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryTournamentResultRepository.delete_by_student(db, 10)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_by_student_non_existent(self):
        """Test deleting tournament results for non-existent student (no-op)"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryTournamentResultRepository.delete_by_student(db, 999)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_create_all_with_negative_coordinates(self):
        """Test creating tournament result with negative coordinates (edge case)"""
        db = Mock()
        result = ArcheryTournamentResult(
            session_id=1,
            student_id=10,
            round_number=1,
            x_coordinate=-5.5,
            y_coordinate=-10.2,
            score=0,
            max_score=10,
            arrow_number=1
        )
        results = [result]

        ArcheryTournamentResultRepository.create_all(db, results)

        assert results[0].x_coordinate == -5.5
        assert results[0].y_coordinate == -10.2
        db.add_all.assert_called_once_with(results)

    def test_create_all_different_rounds(self):
        """Test creating tournament results across multiple rounds"""
        db = Mock()
        results = [
            ArcheryTournamentResult(session_id=1, student_id=10, round_number=1, x_coordinate=10.0, y_coordinate=10.0, score=9, max_score=10, arrow_number=1),
            ArcheryTournamentResult(session_id=1, student_id=10, round_number=2, x_coordinate=12.0, y_coordinate=11.0, score=8, max_score=10, arrow_number=1),
            ArcheryTournamentResult(session_id=1, student_id=10, round_number=3, x_coordinate=9.0, y_coordinate=13.0, score=10, max_score=10, arrow_number=1),
        ]

        ArcheryTournamentResultRepository.create_all(db, results)

        round_numbers = [r.round_number for r in results]
        assert round_numbers == [1, 2, 3]
        db.add_all.assert_called_once_with(results)

    def test_create_all_multiple_students_same_session(self):
        """Test creating tournament results for multiple students in same session"""
        db = Mock()
        results = [
            ArcheryTournamentResult(session_id=1, student_id=10, round_number=1, x_coordinate=10.0, y_coordinate=10.0, score=9, max_score=10, arrow_number=1),
            ArcheryTournamentResult(session_id=1, student_id=11, round_number=1, x_coordinate=12.0, y_coordinate=11.0, score=8, max_score=10, arrow_number=1),
            ArcheryTournamentResult(session_id=1, student_id=12, round_number=1, x_coordinate=9.0, y_coordinate=13.0, score=10, max_score=10, arrow_number=1),
        ]

        ArcheryTournamentResultRepository.create_all(db, results)

        student_ids = [r.student_id for r in results]
        assert student_ids == [10, 11, 12]
        assert all(r.session_id == 1 for r in results)
        db.add_all.assert_called_once_with(results)

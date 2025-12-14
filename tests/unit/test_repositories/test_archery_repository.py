"""
Unit tests for Archery Repository classes.
Tests ArcherySessionRepository and ArcheryResultRepository with mocked database Session.
"""
from datetime import date, datetime
from unittest.mock import Mock, MagicMock
import pytest
from sqlalchemy.orm import Query

from src.db.repositories.archery_repository import ArcherySessionRepository, ArcheryResultRepository
from src.db.models.archery import ArcherySession, ArcheryResult


class TestArcherySessionRepository:
    """Test ArcherySessionRepository CRUD operations"""

    def test_create_session_success(self):
        """Test creating an archery session"""
        db = Mock()
        session = ArcherySession(
            batch_id=1,
            coach_id=100,
            school_id=10,
            date_of_session=date(2024, 1, 15),
            distance=18
        )

        result = ArcherySessionRepository.create(db, session)

        assert result == session
        db.add.assert_called_once_with(session)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(session)

    def test_create_session_without_coach(self):
        """Test creating session without coach (coach_id = None)"""
        db = Mock()
        session = ArcherySession(
            batch_id=1,
            coach_id=None,
            school_id=10,
            date_of_session=date(2024, 1, 15),
            distance=30
        )

        result = ArcherySessionRepository.create(db, session)

        assert result == session
        assert result.coach_id is None
        db.add.assert_called_once_with(session)
        db.commit.assert_called_once()

    def test_get_by_id_found(self):
        """Test retrieving session by ID when exists"""
        db = Mock()
        mock_session = Mock(spec=ArcherySession)
        mock_session.id = 1
        mock_session.batch_id = 1
        mock_session.distance = 18

        db.scalar.return_value = mock_session

        result = ArcherySessionRepository.get_by_id(db, 1)

        assert result == mock_session
        assert result.id == 1
        db.scalar.assert_called_once()

    def test_get_by_id_not_found(self):
        """Test retrieving session by ID when not exists"""
        db = Mock()
        db.scalar.return_value = None

        result = ArcherySessionRepository.get_by_id(db, 999)

        assert result is None

    def test_get_all_sessions_empty(self):
        """Test getting all sessions when database is empty"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcherySessionRepository.get_all(db)

        assert result == []
        db.scalars.assert_called_once()

    def test_get_all_sessions_multiple(self):
        """Test getting all sessions when multiple exist"""
        db = Mock()
        mock_sessions = [
            Mock(spec=ArcherySession, id=1, distance=18),
            Mock(spec=ArcherySession, id=2, distance=30),
            Mock(spec=ArcherySession, id=3, distance=50),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_sessions
        db.scalars.return_value = mock_scalars

        result = ArcherySessionRepository.get_all(db)

        assert len(result) == 3
        assert result == mock_sessions


class TestArcheryResultRepository:
    """Test ArcheryResultRepository CRUD and bulk operations"""

    def test_create_all_empty_list(self):
        """Test bulk creating results with empty list"""
        db = Mock()
        results = []

        ArcheryResultRepository.create_all(db, results)

        db.add_all.assert_called_once_with(results)
        db.commit.assert_called_once()

    def test_create_all_single_result(self):
        """Test bulk creating single result"""
        db = Mock()
        result = ArcheryResult(
            session_id=1,
            student_id=10,
            round_number=1,
            x_coordinate=10.5,
            y_coordinate=20.3,
            score=9,
            max_score=10,
            arrow_number=1
        )
        results = [result]

        ArcheryResultRepository.create_all(db, results)

        db.add_all.assert_called_once_with(results)
        db.commit.assert_called_once()

    def test_create_all_multiple_results(self):
        """Test bulk creating multiple results"""
        db = Mock()
        results = [
            ArcheryResult(session_id=1, student_id=10, round_number=1, x_coordinate=10.5, y_coordinate=20.3, score=9, max_score=10, arrow_number=1),
            ArcheryResult(session_id=1, student_id=10, round_number=1, x_coordinate=15.2, y_coordinate=18.7, score=8, max_score=10, arrow_number=2),
            ArcheryResult(session_id=1, student_id=10, round_number=1, x_coordinate=5.1, y_coordinate=25.9, score=7, max_score=10, arrow_number=3),
        ]

        ArcheryResultRepository.create_all(db, results)

        db.add_all.assert_called_once_with(results)
        assert len(results) == 3
        db.commit.assert_called_once()

    def test_create_all_with_zero_score(self):
        """Test creating result with zero score (edge case)"""
        db = Mock()
        result = ArcheryResult(
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

        ArcheryResultRepository.create_all(db, results)

        assert results[0].score == 0
        db.add_all.assert_called_once_with(results)

    def test_get_by_session_found(self):
        """Test getting results by session ID when exists"""
        db = Mock()
        mock_results = [
            Mock(spec=ArcheryResult, session_id=1, student_id=10, round_number=1),
            Mock(spec=ArcheryResult, session_id=1, student_id=11, round_number=1),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_results
        db.scalars.return_value = mock_scalars

        result = ArcheryResultRepository.get_by_session(db, 1)

        assert len(result) == 2
        assert result == mock_results
        db.scalars.assert_called_once()

    def test_get_by_session_not_found(self):
        """Test getting results by session ID when none exist"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcheryResultRepository.get_by_session(db, 999)

        assert result == []

    def test_get_by_student_found(self):
        """Test getting all results for a student"""
        db = Mock()
        mock_results = [
            Mock(spec=ArcheryResult, session_id=1, student_id=10, round_number=1),
            Mock(spec=ArcheryResult, session_id=2, student_id=10, round_number=1),
            Mock(spec=ArcheryResult, session_id=3, student_id=10, round_number=2),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_results
        db.scalars.return_value = mock_scalars

        result = ArcheryResultRepository.get_by_student(db, 10)

        assert len(result) == 3
        assert all(r.student_id == 10 for r in result)

    def test_get_by_student_not_found(self):
        """Test getting results for student with no results"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcheryResultRepository.get_by_student(db, 999)

        assert result == []

    def test_get_by_session_and_student_found(self):
        """Test getting results by session and student"""
        db = Mock()
        mock_results = [
            Mock(spec=ArcheryResult, session_id=1, student_id=10, round_number=1, arrow_number=1),
            Mock(spec=ArcheryResult, session_id=1, student_id=10, round_number=1, arrow_number=2),
            Mock(spec=ArcheryResult, session_id=1, student_id=10, round_number=2, arrow_number=1),
        ]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_results
        db.scalars.return_value = mock_scalars

        result = ArcheryResultRepository.get_by_session_and_student(db, 1, 10)

        assert len(result) == 3
        assert all(r.session_id == 1 and r.student_id == 10 for r in result)

    def test_get_by_session_and_student_not_found(self):
        """Test getting results by session and student when none exist"""
        db = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        db.scalars.return_value = mock_scalars

        result = ArcheryResultRepository.get_by_session_and_student(db, 1, 999)

        assert result == []

    def test_delete_by_session_success(self):
        """Test deleting all results for a session"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryResultRepository.delete_by_session(db, 1)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_by_session_non_existent(self):
        """Test deleting results for non-existent session (no-op)"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryResultRepository.delete_by_session(db, 999)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_for_student_in_session_success(self):
        """Test deleting specific student's results in a session"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryResultRepository.delete_for_student_in_session(db, 1, 10)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_for_student_in_session_non_existent(self):
        """Test deleting non-existent student's results (no-op)"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryResultRepository.delete_for_student_in_session(db, 999, 999)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_by_student_success(self):
        """Test deleting all results for a student across all sessions"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryResultRepository.delete_by_student(db, 10)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_delete_by_student_non_existent(self):
        """Test deleting results for non-existent student (no-op)"""
        db = Mock()
        mock_result = Mock()
        db.execute.return_value = mock_result

        ArcheryResultRepository.delete_by_student(db, 999)

        db.execute.assert_called_once()
        db.commit.assert_called_once()

    def test_create_all_with_negative_coordinates(self):
        """Test creating result with negative coordinates (edge case)"""
        db = Mock()
        result = ArcheryResult(
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

        ArcheryResultRepository.create_all(db, results)

        assert results[0].x_coordinate == -5.5
        assert results[0].y_coordinate == -10.2
        db.add_all.assert_called_once_with(results)

    def test_create_all_with_max_score(self):
        """Test creating result with maximum score"""
        db = Mock()
        result = ArcheryResult(
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

        ArcheryResultRepository.create_all(db, results)

        assert results[0].score == 10
        assert results[0].score == results[0].max_score
        db.add_all.assert_called_once_with(results)

    def test_create_all_different_rounds(self):
        """Test creating results across multiple rounds"""
        db = Mock()
        results = [
            ArcheryResult(session_id=1, student_id=10, round_number=1, x_coordinate=10.0, y_coordinate=10.0, score=9, max_score=10, arrow_number=1),
            ArcheryResult(session_id=1, student_id=10, round_number=2, x_coordinate=12.0, y_coordinate=11.0, score=8, max_score=10, arrow_number=1),
            ArcheryResult(session_id=1, student_id=10, round_number=3, x_coordinate=9.0, y_coordinate=13.0, score=10, max_score=10, arrow_number=1),
        ]

        ArcheryResultRepository.create_all(db, results)

        round_numbers = [r.round_number for r in results]
        assert round_numbers == [1, 2, 3]
        db.add_all.assert_called_once_with(results)

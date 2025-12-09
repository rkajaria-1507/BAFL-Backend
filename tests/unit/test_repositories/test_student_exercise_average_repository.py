"""
Unit tests for StudentExerciseAverageRepository
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.db.repositories.student_exercise_average_repository import StudentExerciseAverageRepository


@pytest.mark.unit
class TestStudentExerciseAverageRepository:
    """Unit tests for StudentExerciseAverageRepository"""
    
    def test_get_all_level_mappings_with_relations_returns_dict(self, test_db):
        """Test that get_all_level_mappings_with_relations returns correct structure"""
        repo = StudentExerciseAverageRepository(test_db)
        result = repo.get_all_level_mappings_with_relations()
        
        assert isinstance(result, dict)
        assert "exercise_data" in result
        assert "all_students" in result
        assert "coaches" in result
    
    def test_get_all_level_mappings_with_empty_database(self, test_db):
        """Test get_all_level_mappings_with_relations with empty database"""
        repo = StudentExerciseAverageRepository(test_db)
        result = repo.get_all_level_mappings_with_relations()
        
        assert result["exercise_data"] == []
        assert result["all_students"] == []
        assert result["coaches"] == []
    
    def test_get_all_level_mappings_with_data(self, test_db, complete_test_data):
        """Test get_all_level_mappings_with_relations with actual data"""
        repo = StudentExerciseAverageRepository(test_db)
        result = repo.get_all_level_mappings_with_relations()
        
        # Verify exercise data
        assert len(result["exercise_data"]) > 0
        first_exercise = result["exercise_data"][0]
        assert hasattr(first_exercise, "school_name")
        assert hasattr(first_exercise, "batch_name")
        assert hasattr(first_exercise, "student_name")
        assert hasattr(first_exercise, "exercise_name")
        assert hasattr(first_exercise, "average_score")
        
        # Verify all students data
        assert len(result["all_students"]) == 3
        first_student = result["all_students"][0]
        assert hasattr(first_student, "school_name")
        assert hasattr(first_student, "batch_name")
        assert hasattr(first_student, "student_name")
        
        # Verify coaches data
        assert len(result["coaches"]) > 0
        first_coach = result["coaches"][0]
        assert hasattr(first_coach, "batch_id")
        assert hasattr(first_coach, "coach_name")
    
    def test_get_level_for_score_returns_correct_level(self, test_db, sample_exercise_level_mappings):
        """Test get_level_for_score returns correct level information"""
        repo = StudentExerciseAverageRepository(test_db)
        
        # Test curl_up with score 50 (should be level 5)
        level_info = repo.get_level_for_score("curl_up", 50)
        
        assert level_info is not None
        assert level_info["level"] == 5
        assert level_info["level_score"] == 8
        assert level_info["level_description"] == "good"
    
    def test_get_level_for_score_returns_none_when_no_mapping(self, test_db, sample_exercise_level_mappings):
        """Test get_level_for_score returns None when no mapping exists"""
        repo = StudentExerciseAverageRepository(test_db)
        
        # Test curl_up with score 30 (no mapping for this range)
        level_info = repo.get_level_for_score("curl_up", 30)
        
        assert level_info is None
    
    def test_get_level_for_score_with_empty_mapping_table(self, test_db):
        """Test get_level_for_score with empty level mapping table"""
        repo = StudentExerciseAverageRepository(test_db)
        
        level_info = repo.get_level_for_score("curl_up", 50)
        
        assert level_info is None
    
    def test_calculate_average_for_student_batch_exercise(self, test_db, complete_test_data):
        """Test calculate_average_for_student_batch_exercise"""
        repo = StudentExerciseAverageRepository(test_db)
        
        student = complete_test_data["students"][0]
        batch = complete_test_data["batch"]
        
        average = repo.calculate_average_for_student_batch_exercise(
            student_id=student.id,
            batch_id=batch.id,
            exercise_name="curl_up"
        )
        
        assert average == 50.0
    
    def test_calculate_average_returns_none_for_no_data(self, test_db, sample_batch, sample_students):
        """Test calculate_average returns None when no data exists"""
        repo = StudentExerciseAverageRepository(test_db)
        
        average = repo.calculate_average_for_student_batch_exercise(
            student_id=sample_students[0].id,
            batch_id=sample_batch.id,
            exercise_name="curl_up"
        )
        
        assert average is None
    
    def test_get_session_count_for_student_batch_exercise(self, test_db, complete_test_data):
        """Test get_session_count_for_student_batch_exercise"""
        repo = StudentExerciseAverageRepository(test_db)
        
        student = complete_test_data["students"][0]
        batch = complete_test_data["batch"]
        
        count = repo.get_session_count_for_student_batch_exercise(
            student_id=student.id,
            batch_id=batch.id,
            exercise_name="curl_up"
        )
        
        assert count == 1
    
    def test_get_session_count_returns_zero_for_no_data(self, test_db, sample_batch, sample_students):
        """Test get_session_count returns 0 when no data exists"""
        repo = StudentExerciseAverageRepository(test_db)
        
        count = repo.get_session_count_for_student_batch_exercise(
            student_id=sample_students[0].id,
            batch_id=sample_batch.id,
            exercise_name="curl_up"
        )
        
        assert count == 0

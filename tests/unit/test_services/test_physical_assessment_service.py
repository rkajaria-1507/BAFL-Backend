"""
Unit tests for PhysicalAssessmentService
Tests business logic layer with mocked repositories and dependencies.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.services.physical_assessment_service import PhysicalAssessmentService


@pytest.mark.unit
class TestExerciseValidation:
    """Test exercise value validation logic."""

    def test_validate_curl_up_valid_range(self):
        """Test curl_up validation with valid values."""
        # Should not raise
        PhysicalAssessmentService._validate_exercise_value("curl_up", 50, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("curl_up", 0, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("curl_up", 200, student_id=1)

    def test_validate_curl_up_exceeds_maximum(self):
        """Test curl_up validation fails above maximum."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("curl_up", 201, student_id=1)
        
        assert exc_info.value.status_code == 422
        assert "exceeds maximum" in str(exc_info.value.detail)
        assert exc_info.value.detail["exercise"] == "curl_up"
        assert exc_info.value.detail["value"] == 201

    def test_validate_curl_up_negative_value(self):
        """Test curl_up validation fails with negative value."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("curl_up", -5, student_id=1)
        
        assert exc_info.value.status_code == 422
        assert "below minimum" in str(exc_info.value.detail)

    def test_validate_push_up_boundary_values(self):
        """Test push_up validation at boundaries."""
        # Valid boundaries
        PhysicalAssessmentService._validate_exercise_value("push_up", 0, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("push_up", 150, student_id=1)
        
        # Invalid - exceeds max
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("push_up", 151, student_id=1)

    def test_validate_walk_600m_zero_rejected(self):
        """Test walk_600m validation rejects zero (cannot complete in 0 time)."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("walk_600m", 0, student_id=1)
        
        assert exc_info.value.status_code == 422
        assert "cannot be 0 for timed exercises" in str(exc_info.value.detail)
        assert exc_info.value.detail["constraint"] == "non_zero"

    def test_validate_walk_600m_below_minimum(self):
        """Test walk_600m validation rejects values below minimum."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("walk_600m", 1.0, student_id=1)
        
        assert exc_info.value.status_code == 422
        assert "below minimum" in str(exc_info.value.detail)

    def test_validate_walk_600m_valid_values(self):
        """Test walk_600m validation with valid values."""
        PhysicalAssessmentService._validate_exercise_value("walk_600m", 1.5, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("walk_600m", 8.0, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("walk_600m", 15.5, student_id=1)

    def test_validate_dash_50m_zero_rejected(self):
        """Test dash_50m validation rejects zero."""
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("dash_50m", 0, student_id=1)

    def test_validate_dash_50m_below_minimum(self):
        """Test dash_50m validation rejects unrealistic values."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("dash_50m", 4.5, student_id=1)
        
        assert exc_info.value.status_code == 422
        assert "below minimum" in str(exc_info.value.detail)

    def test_validate_dash_50m_valid_values(self):
        """Test dash_50m validation with valid values."""
        PhysicalAssessmentService._validate_exercise_value("dash_50m", 5.0, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("dash_50m", 7.5, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("dash_50m", 12.0, student_id=1)

    def test_validate_sit_and_reach_valid_range(self):
        """Test sit_and_reach validation with valid values."""
        PhysicalAssessmentService._validate_exercise_value("sit_and_reach", 0, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("sit_and_reach", 50.5, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("sit_and_reach", 100, student_id=1)

    def test_validate_sit_and_reach_exceeds_maximum(self):
        """Test sit_and_reach validation fails above maximum."""
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("sit_and_reach", 101, student_id=1)

    def test_validate_bow_hold_valid_range(self):
        """Test bow_hold validation with valid values."""
        PhysicalAssessmentService._validate_exercise_value("bow_hold", 0, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("bow_hold", 300.5, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("bow_hold", 600, student_id=1)

    def test_validate_bow_hold_exceeds_maximum(self):
        """Test bow_hold validation fails above maximum."""
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("bow_hold", 601, student_id=1)

    def test_validate_plank_valid_range(self):
        """Test plank validation with valid values."""
        PhysicalAssessmentService._validate_exercise_value("plank", 0, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("plank", 5.5, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("plank", 10, student_id=1)

    def test_validate_plank_exceeds_maximum(self):
        """Test plank validation fails above maximum (10 minutes)."""
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("plank", 10.1, student_id=1)

    def test_validate_none_value_allowed(self):
        """Test that None values are allowed (student didn't perform exercise)."""
        # Should not raise for any exercise
        PhysicalAssessmentService._validate_exercise_value("curl_up", None, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("walk_600m", None, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("plank", None, student_id=1)

    def test_validate_unknown_exercise_ignored(self):
        """Test that unknown exercises are not validated."""
        # Should not raise
        PhysicalAssessmentService._validate_exercise_value("unknown_exercise", 999, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("invalid", -999, student_id=1)

    def test_validate_float_values_accepted(self):
        """Test that float values are accepted for exercises."""
        PhysicalAssessmentService._validate_exercise_value("sit_and_reach", 15.75, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("walk_600m", 7.33, student_id=1)
        PhysicalAssessmentService._validate_exercise_value("plank", 3.14, student_id=1)

    def test_validate_error_includes_student_id(self):
        """Test that validation errors include student ID for tracking."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("curl_up", -5, student_id=42)
        
        assert exc_info.value.detail["student_id"] == 42


@pytest.mark.unit
class TestExerciseConstraints:
    """Test EXERCISE_CONSTRAINTS configuration."""

    def test_exercise_constraints_has_all_exercises(self):
        """Test that all 7 exercises have constraints defined."""
        constraints = PhysicalAssessmentService.EXERCISE_CONSTRAINTS
        
        required_exercises = [
            "curl_up", "push_up", "sit_and_reach", 
            "walk_600m", "dash_50m", "bow_hold", "plank"
        ]
        
        for exercise in required_exercises:
            assert exercise in constraints
            assert "min" in constraints[exercise]
            assert "max" in constraints[exercise]
            assert "type" in constraints[exercise]

    def test_exercise_constraints_types(self):
        """Test that exercise types are correctly classified."""
        constraints = PhysicalAssessmentService.EXERCISE_CONSTRAINTS
        
        # Higher is better
        assert constraints["curl_up"]["type"] == "higher_better"
        assert constraints["push_up"]["type"] == "higher_better"
        assert constraints["sit_and_reach"]["type"] == "higher_better"
        assert constraints["bow_hold"]["type"] == "higher_better"
        assert constraints["plank"]["type"] == "higher_better"
        
        # Lower is better (timed exercises)
        assert constraints["walk_600m"]["type"] == "lower_better"
        assert constraints["dash_50m"]["type"] == "lower_better"

    def test_timed_exercises_have_minimum_threshold(self):
        """Test that timed exercises have realistic minimum thresholds."""
        constraints = PhysicalAssessmentService.EXERCISE_CONSTRAINTS
        
        assert constraints["walk_600m"]["min"] == 1.5  # 1.5 minutes minimum
        assert constraints["dash_50m"]["min"] == 5.0   # 5.0 seconds minimum

    def test_count_exercises_start_at_zero(self):
        """Test that count-based exercises can start at 0."""
        constraints = PhysicalAssessmentService.EXERCISE_CONSTRAINTS
        
        assert constraints["curl_up"]["min"] == 0
        assert constraints["push_up"]["min"] == 0
        assert constraints["sit_and_reach"]["min"] == 0
        assert constraints["bow_hold"]["min"] == 0
        assert constraints["plank"]["min"] == 0


@pytest.mark.unit
class TestValidationBoundaries:
    """Test boundary value validation."""

    def test_curl_up_at_boundaries(self):
        """Test curl_up at exact boundary values."""
        # Minimum boundary
        PhysicalAssessmentService._validate_exercise_value("curl_up", 0, student_id=1)
        
        # Maximum boundary
        PhysicalAssessmentService._validate_exercise_value("curl_up", 200, student_id=1)
        
        # Just over maximum - should fail
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("curl_up", 200.1, student_id=1)

    def test_walk_600m_at_boundaries(self):
        """Test walk_600m at exact boundary values."""
        # Minimum boundary
        PhysicalAssessmentService._validate_exercise_value("walk_600m", 1.5, student_id=1)
        
        # Just below minimum - should fail
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("walk_600m", 1.49, student_id=1)

    def test_plank_at_boundaries(self):
        """Test plank at exact boundary values."""
        # Minimum boundary
        PhysicalAssessmentService._validate_exercise_value("plank", 0, student_id=1)
        
        # Maximum boundary
        PhysicalAssessmentService._validate_exercise_value("plank", 10, student_id=1)
        
        # Just over maximum - should fail
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value("plank", 10.01, student_id=1)


@pytest.mark.unit
class TestValidationErrorDetails:
    """Test validation error detail structure."""

    def test_error_detail_structure_for_maximum_exceeded(self):
        """Test error detail structure when maximum is exceeded."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("curl_up", 250, student_id=10)
        
        detail = exc_info.value.detail
        assert detail["code"] == "validation_error"
        assert "message" in detail
        assert detail["exercise"] == "curl_up"
        assert detail["student_id"] == 10
        assert detail["value"] == 250
        assert "constraint" in detail

    def test_error_detail_structure_for_minimum_below(self):
        """Test error detail structure when below minimum."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("walk_600m", 1.0, student_id=5)
        
        detail = exc_info.value.detail
        assert detail["code"] == "validation_error"
        assert detail["exercise"] == "walk_600m"
        assert detail["student_id"] == 5
        assert detail["value"] == 1.0

    def test_error_detail_structure_for_zero_timed(self):
        """Test error detail structure for zero on timed exercise."""
        with pytest.raises(HTTPException) as exc_info:
            PhysicalAssessmentService._validate_exercise_value("dash_50m", 0, student_id=7)
        
        detail = exc_info.value.detail
        assert detail["code"] == "validation_error"
        assert detail["constraint"] == "non_zero"
        assert detail["student_id"] == 7


@pytest.mark.unit
class TestMultipleExerciseValidation:
    """Test validating multiple exercises together."""

    def test_validate_all_valid_exercises(self):
        """Test validating a complete set of valid exercise values."""
        exercises = {
            "curl_up": 50,
            "push_up": 30,
            "sit_and_reach": 15.5,
            "walk_600m": 8.0,
            "dash_50m": 7.2,
            "bow_hold": 60.0,
            "plank": 3.5
        }
        
        # Should not raise
        for name, value in exercises.items():
            PhysicalAssessmentService._validate_exercise_value(name, value, student_id=1)

    def test_validate_mixed_valid_and_none(self):
        """Test validating mix of valid values and None."""
        exercises = {
            "curl_up": 50,
            "push_up": None,
            "sit_and_reach": 15.5,
            "walk_600m": None,
            "dash_50m": 7.2,
            "bow_hold": None,
            "plank": 3.5
        }
        
        # Should not raise
        for name, value in exercises.items():
            PhysicalAssessmentService._validate_exercise_value(name, value, student_id=1)

    def test_validate_stops_at_first_invalid(self):
        """Test that validation raises on first invalid value."""
        exercises = [
            ("curl_up", 250),  # Invalid - too high
            ("push_up", 30),   # Valid but won't be reached
        ]
        
        with pytest.raises(HTTPException):
            PhysicalAssessmentService._validate_exercise_value(
                exercises[0][0], exercises[0][1], student_id=1
            )

"""
Unit tests for PhysicalAssessmentService.get_level_mappings
"""
import pytest
from src.services.physical_assessment_service import PhysicalAssessmentService
from src.schemas.physical_assessment import PhysicalAssessmentLevelMappingResponse


@pytest.mark.unit
class TestPhysicalAssessmentServiceLevelMappings:
    """Unit tests for PhysicalAssessmentService level mappings functionality"""
    
    def test_get_level_mappings_returns_correct_type(self, test_db, complete_test_data):
        """Test that get_level_mappings returns PhysicalAssessmentLevelMappingResponse"""
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        assert isinstance(result, PhysicalAssessmentLevelMappingResponse)
        assert hasattr(result, "schools")
    
    def test_get_level_mappings_with_empty_database(self, test_db):
        """Test get_level_mappings with empty database"""
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        assert len(result.schools) == 0
    
    def test_get_level_mappings_structures_data_correctly(self, test_db, complete_test_data):
        """Test that get_level_mappings structures data correctly"""
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        assert len(result.schools) == 1
        
        school = result.schools[0]
        assert school.school_name == "Test High School"
        assert len(school.batches) == 1
        
        batch = school.batches[0]
        assert batch.batch_name == "Batch A"
        assert batch.coach_names is not None
        assert "Sample Coach" in batch.coach_names
        assert len(batch.students) == 3
        
        student = batch.students[0]
        assert student.student_name == "Student 1"
        assert len(student.exercises) == 7
    
    def test_all_exercises_present_in_correct_order(self, test_db, complete_test_data):
        """Test that all 7 exercises are present in correct order"""
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        student = result.schools[0].batches[0].students[0]
        exercise_names = [ex.exercise_name for ex in student.exercises]
        
        expected_order = ["curl_up", "push_up", "sit_and_reach", "walk_600m", "dash_50m", "bow_hold", "plank"]
        assert exercise_names == expected_order
    
    def test_exercises_with_data_have_correct_values(self, test_db, complete_test_data):
        """Test that exercises with data have correct values"""
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        student = result.schools[0].batches[0].students[0]
        
        # Find curl_up exercise
        curl_up = next(ex for ex in student.exercises if ex.exercise_name == "curl_up")
        assert curl_up.average_score == 50.0
        assert curl_up.level == 5
        assert curl_up.level_description == "good"
    
    def test_exercises_without_data_have_null_values(self, test_db, complete_test_data):
        """Test that exercises without data have null values"""
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        student = result.schools[0].batches[0].students[0]
        
        # Find sit_and_reach exercise (no data)
        sit_and_reach = next(ex for ex in student.exercises if ex.exercise_name == "sit_and_reach")
        assert sit_and_reach.average_score is None
        assert sit_and_reach.level is None
        assert sit_and_reach.level_description is None
    
    def test_student_without_exercise_data_has_all_nulls(self, test_db, sample_batch):
        """Test that student without any exercise data has all null values"""
        from src.db.models.student import Student
        
        # Create a student without exercise data
        student = Student(name="No Data Student", age=16, batch_id=sample_batch.id)
        test_db.add(student)
        test_db.commit()
        
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        # Find the student
        students = result.schools[0].batches[0].students
        no_data_student = next(s for s in students if s.student_name == "No Data Student")
        
        # All exercises should have null values
        for exercise in no_data_student.exercises:
            assert exercise.average_score is None
            assert exercise.level is None
            assert exercise.level_description is None
    
    def test_batch_with_no_coaches_returns_null(self, test_db, sample_school):
        """Test that batch with no coaches returns null for coach_names"""
        from src.db.models.batch import Batch
        from src.db.models.student import Student
        from src.db.models.student_exercise_average import StudentExerciseAverage
        
        # Create batch without coaches
        batch = Batch(school_id=sample_school.id, batch_name="No Coach Batch")
        test_db.add(batch)
        test_db.flush()
        
        # Add student to batch so it appears in results
        student = Student(batch_id=batch.id, name="Test Student", age=10)
        test_db.add(student)
        test_db.flush()
        
        # Add exercise data so student appears
        avg = StudentExerciseAverage(
            student_id=student.id,
            batch_id=batch.id,
            school_id=sample_school.id,
            exercise_name="curl_up",
            average_score=20.0
        )
        test_db.add(avg)
        test_db.commit()
        
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        # Should have one school with one batch
        assert len(result.schools) == 1
        assert len(result.schools[0].batches) == 1
        
        # Coach names should be None for batch without coaches
        assert result.schools[0].batches[0].coach_names is None
    
    def test_batch_with_multiple_coaches(self, test_db, sample_batch, sample_coach, assign_coach_to_batch, complete_test_data):
        """Test that batch with multiple coaches returns all coach names"""
        from src.db.models.coach import Coach
        from src.db.models.coach_batch import CoachBatch
        
        # Add second coach
        from src.core.security import PasswordHandler
        coach2 = Coach(
            name="Second Coach",
            username="coach2",
            password=PasswordHandler.hash("password123"),
            is_active=True
        )
        test_db.add(coach2)
        test_db.flush()
        
        coach_batch = CoachBatch(coach_id=coach2.id, batch_id=sample_batch.id)
        test_db.add(coach_batch)
        test_db.commit()
        
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        batch = result.schools[0].batches[0]
        assert len(batch.coach_names) == 2
        assert "Sample Coach" in batch.coach_names
        assert "Second Coach" in batch.coach_names
    
    def test_multiple_schools_structured_correctly(self, test_db, complete_test_data):
        """Test that multiple schools are structured correctly"""
        from src.db.models.school import School
        from src.db.models.batch import Batch
        
        # Add second school
        school2 = School(name="Second School", address="456 Test Ave")
        test_db.add(school2)
        test_db.flush()
        
        batch2 = Batch(school_id=school2.id, batch_name="Batch B")
        test_db.add(batch2)
        test_db.flush()
        
        # Add student to batch2 so it appears in results
        from src.db.models.student import Student
        from src.db.models.student_exercise_average import StudentExerciseAverage
        student2 = Student(batch_id=batch2.id, name="Student in School 2", age=12)
        test_db.add(student2)
        test_db.flush()
        
        # Add exercise data so student appears
        avg2 = StudentExerciseAverage(
            student_id=student2.id,
            batch_id=batch2.id,
            school_id=school2.id,
            exercise_name="curl_up",
            average_score=40.0
        )
        test_db.add(avg2)
        test_db.commit()
        
        result = PhysicalAssessmentService.get_level_mappings(test_db)
        
        assert len(result.schools) == 2
        school_names = [s.school_name for s in result.schools]
        assert "Test High School" in school_names
        assert "Second School" in school_names

"""
Integration test fixtures for API endpoints
"""
import pytest
from src.db.models.school import School
from src.db.models.batch import Batch
from src.db.models.student import Student
from src.db.models.coach import Coach
from src.db.models.coach_batch import CoachBatch
from src.db.models.physical_assessment import PhysicalAssessmentSession, PhysicalAssessmentDetail
from src.db.models.student_exercise_average import StudentExerciseAverage
from src.db.models.exercise_level_mapping import ExerciseLevelMapping
from datetime import date


@pytest.fixture
def sample_school(test_db):
    """Create a sample school"""
    school = School(
        name="Test High School",
        address="123 Test Street"
    )
    test_db.add(school)
    test_db.commit()
    test_db.refresh(school)
    return school


@pytest.fixture
def sample_batch(test_db, sample_school):
    """Create a sample batch"""
    batch = Batch(
        school_id=sample_school.id,
        batch_name="Batch A"
    )
    test_db.add(batch)
    test_db.commit()
    test_db.refresh(batch)
    return batch


@pytest.fixture
def sample_coach(test_db):
    """Create a standalone coach for integration tests"""
    from src.core.security import PasswordHandler
    from src.db.models.coach import Coach
    
    coach = Coach(
        name="Sample Coach",
        username="samplecoach_integration",
        password=PasswordHandler.hash("password123"),
        is_active=True
    )
    test_db.add(coach)
    test_db.commit()
    test_db.refresh(coach)
    return coach


@pytest.fixture
def assign_coach_to_batch(test_db, sample_coach, sample_batch):
    """Assign coach to batch"""
    coach_batch = CoachBatch(
        coach_id=sample_coach.id,
        batch_id=sample_batch.id
    )
    test_db.add(coach_batch)
    test_db.commit()
    return coach_batch


@pytest.fixture
def sample_students(test_db, sample_batch):
    """Create sample students"""
    students = []
    for i in range(3):
        student = Student(
            name=f"Student {i+1}",
            age=15 + i,
            batch_id=sample_batch.id
        )
        test_db.add(student)
        students.append(student)
    
    test_db.commit()
    for student in students:
        test_db.refresh(student)
    return students


@pytest.fixture
def sample_exercise_level_mappings(test_db):
    """Create sample exercise level mappings"""
    mappings_data = [
        # curl_up (count - higher is better)
        {"exercise_name": "curl_up", "level": 1, "min_score": 0, "max_score": 20, "level_score": 2, "level_description": "needs improvement", "is_higher_better": 1, "unit": "count"},
        {"exercise_name": "curl_up", "level": 5, "min_score": 41, "max_score": 60, "level_score": 8, "level_description": "good", "is_higher_better": 1, "unit": "count"},
        {"exercise_name": "curl_up", "level": 7, "min_score": 81, "max_score": 200, "level_score": 10, "level_description": "excellent", "is_higher_better": 1, "unit": "count"},
        
        # push_up (count - higher is better)
        {"exercise_name": "push_up", "level": 1, "min_score": 0, "max_score": 10, "level_score": 2, "level_description": "needs improvement", "is_higher_better": 1, "unit": "count"},
        {"exercise_name": "push_up", "level": 5, "min_score": 21, "max_score": 30, "level_score": 8, "level_description": "good", "is_higher_better": 1, "unit": "count"},
        
        # plank (minutes - higher is better)
        {"exercise_name": "plank", "level": 1, "min_score": 0, "max_score": 1.0, "level_score": 2, "level_description": "needs improvement", "is_higher_better": 1, "unit": "min"},
        {"exercise_name": "plank", "level": 5, "min_score": 2.1, "max_score": 3.0, "level_score": 8, "level_description": "good", "is_higher_better": 1, "unit": "min"},
    ]
    
    mappings = []
    for data in mappings_data:
        mapping = ExerciseLevelMapping(**data)
        test_db.add(mapping)
        mappings.append(mapping)
    
    test_db.commit()
    return mappings


@pytest.fixture
def sample_physical_session(test_db, sample_school, sample_batch, sample_coach):
    """Create a sample physical assessment session"""
    session = PhysicalAssessmentSession(
        coach_id=sample_coach.id,
        school_id=sample_school.id,
        batch_id=sample_batch.id,
        date_of_session=date(2025, 1, 15),
        student_count=3
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest.fixture
def sample_physical_results(test_db, sample_physical_session, sample_students):
    """Create sample physical assessment results"""
    results = []
    scores = [
        {"curl_up": 50, "push_up": 25, "plank": 2.5},
        {"curl_up": 45, "push_up": 20, "plank": 2.0},
        {"curl_up": 30, "push_up": 15, "plank": 1.5},
    ]
    
    for student, score_data in zip(sample_students, scores):
        result = PhysicalAssessmentDetail(
            session_id=sample_physical_session.id,
            student_id=student.id,
            curl_up=score_data.get("curl_up"),
            push_up=score_data.get("push_up"),
            sit_and_reach=0.0,
            walk_600m=0.0,
            dash_50m=0.0,
            bow_hold=0.0,
            plank=score_data.get("plank"),
            is_present=True
        )
        test_db.add(result)
        results.append(result)
    
    test_db.commit()
    return results


@pytest.fixture
def sample_student_averages(test_db, sample_school, sample_batch, sample_students, sample_physical_session, sample_exercise_level_mappings):
    """Create sample student exercise averages with levels"""
    averages = []
    
    # Student 1: curl_up=50 (level 5), push_up=25 (level 5), plank=2.5 (level 5)
    averages.append(StudentExerciseAverage(
        student_id=sample_students[0].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="curl_up",
        average_score=50.0,
        current_level=5,
        level_score=8,
        level_description="good",
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    averages.append(StudentExerciseAverage(
        student_id=sample_students[0].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="push_up",
        average_score=25.0,
        current_level=5,
        level_score=8,
        level_description="good",
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    # Student 2: curl_up=45 (level 5)
    averages.append(StudentExerciseAverage(
        student_id=sample_students[1].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="curl_up",
        average_score=45.0,
        current_level=5,
        level_score=8,
        level_description="good",
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    # Student 3: curl_up=30 (no level mapping for this score)
    averages.append(StudentExerciseAverage(
        student_id=sample_students[2].id,
        batch_id=sample_batch.id,
        school_id=sample_school.id,
        exercise_name="curl_up",
        average_score=30.0,
        current_level=None,
        level_score=None,
        level_description=None,
        session_count=1,
        last_updated_session_id=sample_physical_session.id
    ))
    
    for avg in averages:
        test_db.add(avg)
    
    test_db.commit()
    return averages


@pytest.fixture
def complete_test_data(
    test_db,
    sample_school,
    sample_batch,
    sample_coach,
    assign_coach_to_batch,
    sample_students,
    sample_exercise_level_mappings,
    sample_physical_session,
    sample_physical_results,
    sample_student_averages
):
    """Complete test data setup for integration tests"""
    return {
        "school": sample_school,
        "batch": sample_batch,
        "coach": sample_coach,
        "students": sample_students,
        "session": sample_physical_session,
        "results": sample_physical_results,
        "averages": sample_student_averages,
        "level_mappings": sample_exercise_level_mappings
    }

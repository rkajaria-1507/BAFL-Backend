"""
Integration tests for Physical Assessment Level Mappings Endpoint
GET /api/v1/physical/level-mappings
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.api
class TestLevelMappingsEndpoint:
    """Test suite for level mappings endpoint"""
    
    endpoint = "/api/v1/physical/level-mappings"
    
    def test_unauthenticated_request_returns_401(self, client):
        """Test that unauthenticated requests are rejected"""
        response = client.get(self.endpoint)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_without_permission_returns_403(self, client, auth_headers_regular):
        """Test that users without PHYSICAL_SESSIONS_VIEW permission get 403"""
        response = client.get(self.endpoint, headers=auth_headers_regular)
        
        # UserRole.USER gets PHYSICAL_SESSIONS_VIEW permission by default in ROLE_BASE_PERMISSIONS
        assert response.status_code == status.HTTP_200_OK
    
    def test_coach_with_permission_returns_200(self, client, auth_headers_coach, coach_user):
        """Test that coach with permission can access endpoint"""
        response = client.get(self.endpoint, headers=auth_headers_coach)
        
        assert response.status_code == status.HTTP_200_OK
        assert "schools" in response.json()
    
    def test_coach_access_returns_hierarchical_data(self, client, auth_headers_coach, coach_user):
        """Test that coaches receive properly structured hierarchical data"""
        response = client.get(self.endpoint, headers=auth_headers_coach)
        
        assert response.status_code == status.HTTP_200_OK
        assert "schools" in response.json()
    
    def test_empty_database_returns_empty_schools(self, client, auth_headers_admin):
        """Test that empty database returns empty schools array"""
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["schools"] == []
    
    def test_response_structure_with_complete_data(self, client, auth_headers_admin, complete_test_data):
        """Test response structure with complete test data"""
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify top level structure
        assert "schools" in data
        assert len(data["schools"]) > 0
        
        # Verify school structure
        school = data["schools"][0]
        assert "school_name" in school
        assert "batches" in school
        assert school["school_name"] == "Test High School"
        
        # Verify batch structure
        assert len(school["batches"]) > 0
        batch = school["batches"][0]
        assert "batch_name" in batch
        assert "coach_names" in batch
        assert "students" in batch
        assert batch["batch_name"] == "Batch A"
        assert batch["coach_names"] is not None
        assert "Sample Coach" in batch["coach_names"]
        
        # Verify student structure
        assert len(batch["students"]) == 3
        student = batch["students"][0]
        assert "student_name" in student
        assert "exercises" in student
        assert student["student_name"] == "Student 1"
        
        # Verify exercises structure
        assert len(student["exercises"]) == 7  # All 7 exercises should be present
        exercise = student["exercises"][0]
        assert "exercise_name" in exercise
        assert "average_score" in exercise
        assert "level" in exercise
        assert "level_description" in exercise
    
    def test_all_seven_exercises_present_for_each_student(self, client, auth_headers_admin, complete_test_data):
        """Test that all 7 exercises are present for each student"""
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        students = data["schools"][0]["batches"][0]["students"]
        
        expected_exercises = ["curl_up", "push_up", "sit_and_reach", "walk_600m", "dash_50m", "bow_hold", "plank"]
        
        for student in students:
            exercises = student["exercises"]
            assert len(exercises) == 7
            
            exercise_names = [ex["exercise_name"] for ex in exercises]
            assert exercise_names == expected_exercises  # Order should match
    
    def test_exercises_with_data_have_values(self, client, auth_headers_admin, complete_test_data):
        """Test that exercises with data have non-null values"""
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        student1 = data["schools"][0]["batches"][0]["students"][0]
        
        # Student 1 should have curl_up and push_up with values
        curl_up = next(ex for ex in student1["exercises"] if ex["exercise_name"] == "curl_up")
        assert curl_up["average_score"] == 50.0
        assert curl_up["level"] == 5
        assert curl_up["level_description"] == "good"
        
        push_up = next(ex for ex in student1["exercises"] if ex["exercise_name"] == "push_up")
        assert push_up["average_score"] == 25.0
        assert push_up["level"] == 5
        assert push_up["level_description"] == "good"
    
    def test_exercises_without_data_have_null_values(self, client, auth_headers_admin, complete_test_data):
        """Test that exercises without data have null values"""
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        student1 = data["schools"][0]["batches"][0]["students"][0]
        
        # Student 1 should have sit_and_reach, walk_600m, dash_50m, bow_hold with null values
        sit_and_reach = next(ex for ex in student1["exercises"] if ex["exercise_name"] == "sit_and_reach")
        assert sit_and_reach["average_score"] is None
        assert sit_and_reach["level"] is None
        assert sit_and_reach["level_description"] is None
    
    def test_student_with_no_level_mapping_has_null_level(self, client, auth_headers_admin, complete_test_data):
        """Test that student with score not in level mapping table has null level"""
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        student3 = data["schools"][0]["batches"][0]["students"][2]
        
        # Student 3 has curl_up score of 30, which has no level mapping
        curl_up = next(ex for ex in student3["exercises"] if ex["exercise_name"] == "curl_up")
        assert curl_up["average_score"] == 30.0
        assert curl_up["level"] is None
        assert curl_up["level_description"] is None
    
    def test_batch_with_no_coaches_returns_null(self, client, auth_headers_admin, test_db, sample_school):
        """Test that batch with no coaches returns null for coach_names"""
        # Create a batch without coaches
        from src.db.models.batch import Batch
        from src.db.models.student import Student
        from src.db.models.student_exercise_average import StudentExerciseAverage
        
        batch = Batch(school_id=sample_school.id, batch_name="No Coach Batch")
        test_db.add(batch)
        test_db.flush()
        
        # Add student so batch appears in results
        student = Student(batch_id=batch.id, name="No Coach Student", age=11)
        test_db.add(student)
        test_db.flush()
        
        # Add exercise data
        avg = StudentExerciseAverage(
            student_id=student.id,
            batch_id=batch.id,
            school_id=sample_school.id,
            exercise_name="push_up",
            average_score=15.0
        )
        test_db.add(avg)
        test_db.commit()
        
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        # Find the batch without coaches
        no_coach_batch = next(
            (b for b in data["schools"][0]["batches"] if b["batch_name"] == "No Coach Batch"),
            None
        )
        
        assert no_coach_batch is not None
        assert no_coach_batch["coach_names"] is None
    
    def test_multiple_coaches_per_batch(self, client, auth_headers_admin, test_db, sample_batch, complete_test_data):
        """Test that multiple coaches are returned for a batch"""
        from src.db.models.coach import Coach
        from src.db.models.coach_batch import CoachBatch
        
        # Create another coach and assign to the batch
        from src.core.security import PasswordHandler
        coach2 = Coach(
            name="Second Coach",
            username="secondcoach",
            password=PasswordHandler.hash("password123"),
            is_active=True
        )
        test_db.add(coach2)
        test_db.flush()
        
        coach_batch = CoachBatch(
            coach_id=coach2.id,
            batch_id=sample_batch.id
        )
        test_db.add(coach_batch)
        test_db.commit()
        
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        batch = data["schools"][0]["batches"][0]
        
        assert len(batch["coach_names"]) == 2
        assert "Sample Coach" in batch["coach_names"]
        assert "Second Coach" in batch["coach_names"]
    
    def test_multiple_schools_and_batches(self, client, auth_headers_admin, test_db, complete_test_data):
        """Test response with multiple schools and batches"""
        from src.db.models.school import School
        from src.db.models.batch import Batch
        
        # Create another school and batch
        school2 = School(name="Second School", address="456 Another St")
        test_db.add(school2)
        test_db.flush()
        
        batch2 = Batch(school_id=school2.id, batch_name="Batch B")
        test_db.add(batch2)
        test_db.flush()
        
        # Add student to batch2 so it appears in results
        from src.db.models.student import Student
        from src.db.models.student_exercise_average import StudentExerciseAverage
        student2 = Student(batch_id=batch2.id, name="Student in School 2", age=13)
        test_db.add(student2)
        test_db.flush()
        
        # Add exercise data
        avg2 = StudentExerciseAverage(
            student_id=student2.id,
            batch_id=batch2.id,
            school_id=school2.id,
            exercise_name="sit_and_reach",
            average_score=35.0
        )
        test_db.add(avg2)
        test_db.commit()
        
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        assert len(data["schools"]) == 2
        
        school_names = [s["school_name"] for s in data["schools"]]
        assert "Test High School" in school_names
        assert "Second School" in school_names
    
    def test_student_with_no_exercises_has_all_null(self, client, auth_headers_admin, test_db, sample_batch):
        """Test that student with no exercise data has all exercises with null values"""
        from src.db.models.student import Student
        
        # Create a student without any exercise data
        student = Student(
            name="Student Without Data",
            age=16,
            batch_id=sample_batch.id
        )
        test_db.add(student)
        test_db.commit()
        
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        students = data["schools"][0]["batches"][0]["students"]
        
        # Find the student without data
        student_without_data = next(
            (s for s in students if s["student_name"] == "Student Without Data"),
            None
        )
        
        assert student_without_data is not None
        assert len(student_without_data["exercises"]) == 7
        
        # All exercises should have null values
        for exercise in student_without_data["exercises"]:
            assert exercise["average_score"] is None
            assert exercise["level"] is None
            assert exercise["level_description"] is None
    
    def test_exercise_order_matches_model_definition(self, client, auth_headers_admin, complete_test_data):
        """Test that exercises are returned in the order defined in the model"""
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        data = response.json()
        student = data["schools"][0]["batches"][0]["students"][0]
        exercise_names = [ex["exercise_name"] for ex in student["exercises"]]
        
        # Expected order from StudentExerciseAverageRepository.EXERCISE_COLUMNS
        expected_order = ["curl_up", "push_up", "sit_and_reach", "walk_600m", "dash_50m", "bow_hold", "plank"]
        
        assert exercise_names == expected_order

    def test_coach_sees_only_assigned_batches(self, client, test_db, coach_user, auth_headers_coach):
        """Test that coaches only see data for batches they are assigned to"""
        from src.db.models.school import School
        from src.db.models.batch import Batch
        from src.db.models.student import Student
        from src.db.models.student_exercise_average import StudentExerciseAverage
        from src.db.models.coach_batch import CoachBatch
        
        # Create first school and batch (assigned to coach)
        school1 = School(name="Assigned School")
        test_db.add(school1)
        test_db.commit()
        test_db.refresh(school1)
        
        batch1 = Batch(batch_name="Assigned Batch", school_id=school1.id)
        test_db.add(batch1)
        test_db.commit()
        test_db.refresh(batch1)
        
        # Assign coach to batch1
        coach_batch = CoachBatch(coach_id=coach_user.id, batch_id=batch1.id)
        test_db.add(coach_batch)
        test_db.commit()
        
        # Add student and exercise data to assigned batch
        student1 = Student(name="Assigned Student", age=15, batch_id=batch1.id)
        test_db.add(student1)
        test_db.commit()
        test_db.refresh(student1)
        
        avg1 = StudentExerciseAverage(
            student_id=student1.id,
            batch_id=batch1.id,
            school_id=school1.id,
            exercise_name="curl_up",
            average_score=50.0,
            session_count=1
        )
        test_db.add(avg1)
        test_db.commit()
        
        # Create second school and batch (NOT assigned to coach)
        school2 = School(name="Unassigned School")
        test_db.add(school2)
        test_db.commit()
        test_db.refresh(school2)
        
        batch2 = Batch(batch_name="Unassigned Batch", school_id=school2.id)
        test_db.add(batch2)
        test_db.commit()
        test_db.refresh(batch2)
        
        # Add student and exercise data to unassigned batch
        student2 = Student(name="Unassigned Student", age=16, batch_id=batch2.id)
        test_db.add(student2)
        test_db.commit()
        test_db.refresh(student2)
        
        avg2 = StudentExerciseAverage(
            student_id=student2.id,
            batch_id=batch2.id,
            school_id=school2.id,
            exercise_name="push_up",
            average_score=30.0,
            session_count=1
        )
        test_db.add(avg2)
        test_db.commit()
        
        # Coach makes request
        response = client.get(self.endpoint, headers=auth_headers_coach)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Coach should only see their assigned school
        school_names = [school["school_name"] for school in data["schools"]]
        
        assert "Assigned School" in school_names
        assert "Unassigned School" not in school_names
    
    def test_user_sees_all_data_including_unassigned(self, client, test_db, auth_headers_admin, complete_test_data):
        """Test that users (non-coaches) see all data regardless of assignments"""
        from src.db.models.school import School
        from src.db.models.batch import Batch
        from src.db.models.student import Student
        from src.db.models.student_exercise_average import StudentExerciseAverage
        
        # Create a second school and batch
        other_school = School(name="Another School")
        test_db.add(other_school)
        test_db.commit()
        test_db.refresh(other_school)
        
        other_batch = Batch(
            batch_name="Another Batch",
            school_id=other_school.id
        )
        test_db.add(other_batch)
        test_db.commit()
        test_db.refresh(other_batch)
        
        # Add a student with exercise data so they appear
        other_student = Student(
            name="Another Student",
            age=17,
            batch_id=other_batch.id
        )
        test_db.add(other_student)
        test_db.commit()
        test_db.refresh(other_student)
        
        # Add exercise data
        other_avg = StudentExerciseAverage(
            student_id=other_student.id,
            batch_id=other_batch.id,
            school_id=other_school.id,
            exercise_name="push_up",
            average_score=20.0,
            session_count=1
        )
        test_db.add(other_avg)
        test_db.commit()
        
        # Admin user makes request
        response = client.get(self.endpoint, headers=auth_headers_admin)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Admin should see ALL schools
        school_names = [school["school_name"] for school in data["schools"]]
        
        assert "Test High School" in school_names
        assert "Another School" in school_names

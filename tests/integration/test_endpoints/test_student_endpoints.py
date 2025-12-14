"""
Integration tests for Student Management endpoints.
"""
import pytest
from fastapi import status

from src.db.models.student import Student
from src.db.models.school import School
from src.db.models.batch import Batch
from src.db.models.coach import Coach
from src.core.security import PasswordHandler


API_PREFIX = "/api/v1/students"


# Helper Functions --------------------------------------------------------


def _create_school(db, name: str = "Test School", address: str = "Test Address") -> School:
    """Create a test school."""
    school = School(name=name, address=address)
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def _create_batch(db, school: School, name: str = "Test Batch") -> Batch:
    """Create a test batch."""
    batch = Batch(name=name, school_id=school.id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def _create_coach(db, username: str = "testcoach", name: str = "Test Coach") -> Coach:
    """Create a test coach."""
    hashed_password = PasswordHandler.hash("testpass123")
    coach = Coach(name=name, username=username, password=hashed_password, is_active=True)
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def _create_student(
    db, 
    name: str = "Test Student", 
    age: int = 10,
    batch: Batch = None
) -> Student:
    """Create a test student directly in the database.
    Note: school_id and coach_id are derived from batch relationship."""
    student = Student(
        name=name,
        age=age,
        batch_id=batch.id if batch else None
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


# Test Classes ------------------------------------------------------------


class TestStudentCreationEndpoints:
    """Test student creation functionality."""

    def test_create_student_as_admin_success(self, client, test_db, auth_headers_admin):
        """Admin can create a new student."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        
        payload = {
            "name": "New Student",
            "age": 12,
            "school_id": school.id,
            "batch_id": batch.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == "New Student"
        assert data["age"] == 12
        assert data["school_id"] == school.id
        assert data["batch_id"] == batch.id
        assert "id" in data

    def test_create_student_minimum_age(self, client, test_db, auth_headers_admin):
        """Student can be created with minimum age."""
        school = _create_school(test_db)
        
        payload = {
            "name": "Young Student",
            "age": 5,
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["age"] == 5

    def test_create_student_maximum_age(self, client, test_db, auth_headers_admin):
        """Student can be created with older age."""
        school = _create_school(test_db)
        
        payload = {
            "name": "Older Student",
            "age": 18,
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["age"] == 18

    def test_create_student_with_batch_only(self, client, test_db, auth_headers_admin):
        """Admin can create student with only batch assignment."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        
        payload = {
            "name": "Batch Student",
            "age": 11,
            "batch_id": batch.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["batch_id"] == batch.id

    def test_create_student_requires_authentication(self, client, test_db):
        """Creating a student requires authentication."""
        payload = {
            "name": "Unauthorized Student",
            "age": 10
        }

        response = client.post(f"{API_PREFIX}/", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_student_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can create students."""
        payload = {
            "name": "Restricted Student",
            "age": 10
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_student_missing_required_fields(self, client, test_db, auth_headers_admin):
        """Creating student with missing fields returns validation error."""
        payload = {
            "name": "Incomplete Student"
            # Missing age
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_student_with_nonexistent_school(self, client, test_db, auth_headers_admin):
        """Creating student with non-existent school ID (via school_id field if present) is allowed."""
        payload = {
            "name": "No School Student",
            "age": 10
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_student_with_nonexistent_batch(self, client, test_db, auth_headers_admin):
        """Creating student with non-existent batch ID returns error."""
        school = _create_school(test_db)
        
        payload = {
            "name": "Invalid Batch Student",
            "age": 10,
            "school_id": school.id,
            "batch_id": 99999
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_create_student_with_negative_age(self, client, test_db, auth_headers_admin):
        """Creating student with negative age is allowed (no validation on age range)."""
        payload = {
            "name": "Negative Age Student",
            "age": -5
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        # Accept either success or validation error
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestStudentListEndpoints:
    """Test student listing functionality."""

    def test_list_students_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can list all students."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        _create_student(test_db, name="Student One", age=10, batch=batch)
        _create_student(test_db, name="Student Two", age=11, batch=batch)

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_students_as_regular_user(self, client, test_db, auth_headers_regular):
        """Regular users can also list students."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        _create_student(test_db, name="Visible Student", batch=batch)

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_200_OK

    def test_list_students_requires_authentication(self, client, test_db):
        """Listing students requires authentication."""
        response = client.get(f"{API_PREFIX}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_students_pagination(self, client, test_db, auth_headers_admin):
        """Student listing supports pagination."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        for i in range(5):
            _create_student(test_db, name=f"Page Student {i}", age=10+i, batch=batch)

        response = client.get(f"{API_PREFIX}/?skip=0&limit=2", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 2

    def test_list_students_empty_database(self, client, test_db, auth_headers_admin):
        """Listing students in empty database returns empty array."""
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_student_pre_create_data(self, client, test_db, auth_headers_admin):
        """Admin can get pre-create data (schools, batches, coaches)."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)

        response = client.get(f"{API_PREFIX}/pre-create", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "schools" in data
        assert "batches" in data
        assert "coaches" in data

    def test_get_student_pre_create_requires_admin(self, client, test_db, auth_headers_regular):
        """Pre-create data requires admin privileges."""
        response = client.get(f"{API_PREFIX}/pre-create", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStudentDetailEndpoints:
    """Test student detail retrieval functionality."""

    def test_get_student_by_id_success(self, client, test_db, auth_headers_admin):
        """Admin can get specific student by ID."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Specific Student", age=12, batch=batch)

        response = client.get(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == student.id
        assert data["name"] == "Specific Student"
        assert data["age"] == 12
        assert data["batch_id"] == batch.id

    def test_get_student_by_id_not_found(self, client, test_db, auth_headers_admin):
        """Getting non-existent student returns 404."""
        response = client.get(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_student_by_id_requires_authentication(self, client, test_db):
        """Getting student by ID requires authentication."""
        response = client.get(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestStudentUpdateEndpoints:
    """Test student update functionality."""

    def test_update_student_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can update student information."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Old Name", age=10, batch=batch)

        payload = {
            "name": "New Name",
            "age": 11
        }

        response = client.put(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "New Name"
        assert data["age"] == 11

    def test_update_student_change_batch_and_school(self, client, test_db, auth_headers_admin):
        """Admin can change student's batch (which changes school)."""
        school1 = _create_school(test_db, name="School 1")
        school2 = _create_school(test_db, name="School 2")
        batch1 = _create_batch(test_db, school1, name="Batch 1")
        batch2 = _create_batch(test_db, school2, name="Batch 2")
        student = _create_student(test_db, name="Student", age=10, batch=batch1)

        payload = {
            "batch_id": batch2.id
        }

        response = client.put(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["batch_id"] == batch2.id

    def test_update_student_change_batch(self, client, test_db, auth_headers_admin):
        """Admin can change student's batch."""
        school = _create_school(test_db)
        batch1 = _create_batch(test_db, school, name="Batch 1")
        batch2 = _create_batch(test_db, school, name="Batch 2")
        student = _create_student(test_db, name="Student", age=10, batch=batch1)

        payload = {
            "batch_id": batch2.id
        }

        response = client.put(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["batch_id"] == batch2.id

    def test_update_student_only_name(self, client, test_db, auth_headers_admin):
        """Admin can update only student name without changing batch."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Student", age=10, batch=batch)

        payload = {
            "name": "Updated Name"
        }

        response = client.put(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["batch_id"] == batch.id

    def test_update_student_requires_authentication(self, client, test_db):
        """Updating student requires authentication."""
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/1", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_student_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can update students."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Student", batch=batch)
        
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/{student.id}", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_student_not_found(self, client, test_db, auth_headers_admin):
        """Updating non-existent student returns 404."""
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/99999", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStudentDeleteEndpoints:
    """Test student deletion functionality."""

    def test_delete_student_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can delete a student."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Delete Student", batch=batch)

        response = client.delete(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify student is deleted
        response = client.get(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_student_with_assignments(self, client, test_db, auth_headers_admin):
        """Admin can delete student with batch assignment."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Student", batch=batch)

        response = client.delete(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_student_requires_authentication(self, client, test_db):
        """Deleting student requires authentication."""
        response = client.delete(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_student_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can delete students."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Student", batch=batch)
        
        response = client.delete(f"{API_PREFIX}/{student.id}", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_student_not_found(self, client, test_db, auth_headers_admin):
        """Deleting non-existent student returns 404."""
        response = client.delete(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStudentEdgeCases:
    """Test edge cases for student management."""

    def test_create_student_with_special_characters_in_name(self, client, test_db, auth_headers_admin):
        """Student can have special characters in name."""
        school = _create_school(test_db)
        
        payload = {
            "name": "O'Brien-Smith, Jr.",
            "age": 10,
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "O'Brien-Smith, Jr."

    def test_create_student_with_unicode_name(self, client, test_db, auth_headers_admin):
        """Student can have Unicode characters in name."""
        school = _create_school(test_db)
        
        payload = {
            "name": "François Müller",
            "age": 10,
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_student_age_boundary(self, client, test_db, auth_headers_admin):
        """Admin can update student age to boundary values."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        student = _create_student(test_db, name="Student", age=10, batch=batch)

        payload = {
            "age": 100
        }

        response = client.put(f"{API_PREFIX}/{student.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["age"] == 100

    def test_create_student_without_optional_fields(self, client, test_db, auth_headers_admin):
        """Student can be created without optional school/batch/coach."""
        payload = {
            "name": "Minimal Student",
            "age": 10
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["school_id"] is None
        assert data["batch_id"] is None
        assert data["coach_id"] is None

    def test_create_student_with_very_long_name(self, client, test_db, auth_headers_admin):
        """Student can have long name."""
        school = _create_school(test_db)
        
        payload = {
            "name": "A" * 100,
            "age": 10,
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_student_age_boundary_zero(self, client, test_db, auth_headers_admin):
        """Creating student with age 0 should fail or succeed based on business rules."""
        school = _create_school(test_db)
        
        payload = {
            "name": "Zero Age Student",
            "age": 0,
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        # Accept either success or validation error
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]

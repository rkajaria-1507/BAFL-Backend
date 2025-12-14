"""
Integration tests for Coach Management endpoints.
"""
import pytest
from fastapi import status

from src.core.security import PasswordHandler
from src.db.models.coach import Coach
from src.db.models.school import School
from src.db.models.batch import Batch
from src.db.models.coach_school import CoachSchool
from src.db.models.coach_batch import CoachBatch


API_PREFIX = "/api/v1/coaches"


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
    """Create a test coach directly in the database."""
    hashed_password = PasswordHandler.hash("testpass123")
    
    coach = Coach(
        name=name,
        username=username,
        password=hashed_password,
        is_active=True
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def _assign_coach_to_school(db, coach: Coach, school: School):
    """Assign a coach to a school."""
    coach_school = CoachSchool(coach_id=coach.id, school_id=school.id)
    db.add(coach_school)
    db.commit()


def _assign_coach_to_batch(db, coach: Coach, batch: Batch):
    """Assign a coach to a batch."""
    coach_batch = CoachBatch(coach_id=coach.id, batch_id=batch.id)
    db.add(coach_batch)
    db.commit()


# Test Classes ------------------------------------------------------------


class TestCoachCreationEndpoints:
    """Test coach creation functionality."""

    def test_create_coach_as_admin_success(self, client, test_db, auth_headers_admin):
        """Admin can create a new coach."""
        payload = {
            "name": "New Coach",
            "username": "newcoach",
            "password": "securepass123"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["message"] == "Coach created successfully"
        assert data["coach"]["name"] == "New Coach"
        assert "coach_id" in data["coach"]
        assert "schools" in data["coach"]
        assert "batches" in data["coach"]

    def test_create_coach_with_schools_and_batches(self, client, test_db, auth_headers_admin):
        """Admin can create coach with school and batch assignments."""
        school = _create_school(test_db, name="School A")
        batch = _create_batch(test_db, school, name="Batch A")

        payload = {
            "name": "Assigned Coach",
            "username": "assignedcoach",
            "password": "pass123456",
            "schools": [school.id],
            "batches": [batch.id]
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert len(data["coach"]["schools"]) == 1
        assert data["coach"]["schools"][0]["school_id"] == school.id
        assert len(data["coach"]["batches"]) == 1
        assert data["coach"]["batches"][0]["batch_id"] == batch.id

    def test_create_coach_requires_authentication(self, client, test_db):
        """Creating a coach requires authentication."""
        payload = {
            "name": "Unauthorized Coach",
            "username": "unauth",
            "password": "pass123"
        }

        response = client.post(f"{API_PREFIX}/", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_coach_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can create coaches."""
        payload = {
            "name": "Restricted Coach",
            "username": "restricted",
            "password": "pass123"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_coach_duplicate_username(self, client, test_db, auth_headers_admin):
        """Cannot create coach with duplicate username."""
        # Create first coach
        _create_coach(test_db, username="duplicate", name="First Coach")

        # Try to create second coach with same username
        payload = {
            "name": "Second Coach",
            "username": "duplicate",
            "password": "pass123"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_coach_missing_required_fields(self, client, test_db, auth_headers_admin):
        """Creating coach with missing fields returns validation error."""
        payload = {
            "name": "Incomplete Coach"
            # Missing username and password
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_coach_with_nonexistent_school(self, client, test_db, auth_headers_admin):
        """Creating coach with non-existent school ID returns error."""
        payload = {
            "name": "Invalid School Coach",
            "username": "invalidschool",
            "password": "pass123",
            "schools": [99999]
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_create_coach_with_nonexistent_batch(self, client, test_db, auth_headers_admin):
        """Creating coach with non-existent batch ID returns error."""
        payload = {
            "name": "Invalid Batch Coach",
            "username": "invalidbatch",
            "password": "pass123",
            "batches": [99999]
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


class TestCoachListEndpoints:
    """Test coach listing functionality."""

    def test_list_coaches_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can list all coaches."""
        # Create multiple coaches
        _create_coach(test_db, username="coach1", name="Coach One")
        _create_coach(test_db, username="coach2", name="Coach Two")

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_coaches_as_regular_user(self, client, test_db, auth_headers_regular):
        """Regular users can also list coaches."""
        _create_coach(test_db, username="visiblecoach", name="Visible Coach")

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_200_OK

    def test_list_coaches_requires_authentication(self, client, test_db):
        """Listing coaches requires authentication."""
        response = client.get(f"{API_PREFIX}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_coaches_pagination(self, client, test_db, auth_headers_admin):
        """Coach listing supports pagination."""
        # Create several coaches
        for i in range(5):
            _create_coach(test_db, username=f"pagcoach{i}", name=f"Page Coach {i}")

        # Get with limit
        response = client.get(f"{API_PREFIX}/?skip=0&limit=2", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 2

    def test_list_coaches_empty_database(self, client, test_db, auth_headers_admin):
        """Listing coaches in empty database returns empty array."""
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_coach_pre_create_data(self, client, test_db, auth_headers_admin):
        """Admin can get pre-create data (schools and batches)."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)

        response = client.get(f"{API_PREFIX}/pre-create", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "schools" in data
        assert "batches" in data

    def test_get_coach_pre_create_requires_admin(self, client, test_db, auth_headers_regular):
        """Pre-create data requires admin privileges."""
        response = client.get(f"{API_PREFIX}/pre-create", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCoachDetailEndpoints:
    """Test coach detail retrieval functionality."""

    def test_get_coach_by_id_success(self, client, test_db, auth_headers_admin):
        """Admin can get specific coach by ID."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db, username="specificcoach", name="Specific Coach")
        _assign_coach_to_school(test_db, coach, school)
        _assign_coach_to_batch(test_db, coach, batch)

        response = client.get(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["coach_id"] == coach.id
        assert data["name"] == "Specific Coach"
        assert len(data["schools"]) == 1
        assert len(data["batches"]) == 1

    def test_get_coach_by_id_not_found(self, client, test_db, auth_headers_admin):
        """Getting non-existent coach returns 404."""
        response = client.get(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_coach_by_id_requires_authentication(self, client, test_db):
        """Getting coach by ID requires authentication."""
        response = client.get(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCoachUpdateEndpoints:
    """Test coach update functionality."""

    def test_update_coach_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can update coach information."""
        coach = _create_coach(test_db, username="updateme", name="Old Name")

        payload = {
            "name": "New Name"
        }

        response = client.put(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Coach updated successfully"
        assert data["coach"]["name"] == "New Name"

    def test_update_coach_add_school_assignment(self, client, test_db, auth_headers_admin):
        """Admin can add school assignments to coach."""
        coach = _create_coach(test_db, username="addschool", name="Coach")
        school = _create_school(test_db, name="New School")

        payload = {
            "schools": [school.id]
        }

        response = client.put(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["coach"]["schools"]) == 1
        assert data["coach"]["schools"][0]["school_id"] == school.id

    def test_update_coach_add_batch_assignment(self, client, test_db, auth_headers_admin):
        """Admin can add batch assignments to coach."""
        coach = _create_coach(test_db, username="addbatch", name="Coach")
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="New Batch")

        payload = {
            "batches": [batch.id]
        }

        response = client.put(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["coach"]["batches"]) == 1

    def test_update_coach_password(self, client, test_db, auth_headers_admin):
        """Admin can update coach password."""
        coach = _create_coach(test_db, username="changepass", name="Coach")

        payload = {
            "password": "newsecurepassword123"
        }

        response = client.put(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK

    def test_update_coach_requires_authentication(self, client, test_db):
        """Updating coach requires authentication."""
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/1", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_coach_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can update coaches."""
        coach = _create_coach(test_db, username="restrictupdate", name="Coach")
        
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/{coach.id}", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_coach_not_found(self, client, test_db, auth_headers_admin):
        """Updating non-existent coach returns 404."""
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/99999", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCoachDeleteEndpoints:
    """Test coach deletion functionality."""

    def test_delete_coach_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can delete a coach."""
        coach = _create_coach(test_db, username="deleteme", name="Delete Coach")

        response = client.delete(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify coach is deleted
        response = client.get(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_coach_with_assignments(self, client, test_db, auth_headers_admin):
        """Admin can delete coach with school/batch assignments."""
        coach = _create_coach(test_db, username="deletewithassign", name="Coach")
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        _assign_coach_to_school(test_db, coach, school)
        _assign_coach_to_batch(test_db, coach, batch)

        response = client.delete(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_coach_requires_authentication(self, client, test_db):
        """Deleting coach requires authentication."""
        response = client.delete(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_coach_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can delete coaches."""
        coach = _create_coach(test_db, username="restrictdelete", name="Coach")
        
        response = client.delete(f"{API_PREFIX}/{coach.id}", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_coach_not_found(self, client, test_db, auth_headers_admin):
        """Deleting non-existent coach returns 404."""
        response = client.delete(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCoachEdgeCases:
    """Test edge cases for coach management."""

    def test_create_coach_with_special_characters_in_name(self, client, test_db, auth_headers_admin):
        """Coach can have special characters in name."""
        payload = {
            "name": "O'Brien-Smith, Jr.",
            "username": "obrien",
            "password": "pass123"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["coach"]["name"] == "O'Brien-Smith, Jr."

    def test_create_coach_with_unicode_name(self, client, test_db, auth_headers_admin):
        """Coach can have Unicode characters in name."""
        payload = {
            "name": "François Müller",
            "username": "francois",
            "password": "pass123"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_coach_clear_assignments(self, client, test_db, auth_headers_admin):
        """Admin can clear coach assignments by passing empty arrays."""
        coach = _create_coach(test_db, username="clearassign", name="Coach")
        school = _create_school(test_db)
        _assign_coach_to_school(test_db, coach, school)

        payload = {
            "schools": [],
            "batches": []
        }

        response = client.put(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["coach"]["schools"]) == 0
        assert len(data["coach"]["batches"]) == 0

    def test_get_coach_with_multiple_assignments(self, client, test_db, auth_headers_admin):
        """Coach with multiple school and batch assignments."""
        coach = _create_coach(test_db, username="multiassign", name="Multi Coach")
        
        school1 = _create_school(test_db, name="School 1")
        school2 = _create_school(test_db, name="School 2")
        batch1 = _create_batch(test_db, school1, name="Batch 1")
        batch2 = _create_batch(test_db, school2, name="Batch 2")
        
        _assign_coach_to_school(test_db, coach, school1)
        _assign_coach_to_school(test_db, coach, school2)
        _assign_coach_to_batch(test_db, coach, batch1)
        _assign_coach_to_batch(test_db, coach, batch2)

        response = client.get(f"{API_PREFIX}/{coach.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["schools"]) == 2
        assert len(data["batches"]) == 2

    def test_create_coach_with_long_username(self, client, test_db, auth_headers_admin):
        """Coach can have long username."""
        payload = {
            "name": "Long Username Coach",
            "username": "a" * 50,
            "password": "password123"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

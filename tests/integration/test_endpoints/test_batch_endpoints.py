"""
Integration tests for Batch Management endpoints.
"""
import pytest
from fastapi import status

from src.db.models.batch import Batch
from src.db.models.school import School


API_PREFIX = "/api/v1/batches"


# Helper Functions --------------------------------------------------------


def _create_school(db, name: str = "Test School") -> School:
    """Create a test school."""
    school = School(name=name, address="Test Address")
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


# Test Classes ------------------------------------------------------------


class TestBatchCreationEndpoints:
    """Test batch creation functionality."""

    def test_create_batch_as_admin_success(self, client, test_db, auth_headers_admin):
        """Admin can create a new batch."""
        school = _create_school(test_db, name="Test School")
        
        payload = {
            "batch_name": "Morning Batch",
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["batch_name"] == "Morning Batch"
        assert data["school_id"] == school.id
        assert "batch_id" in data

    def test_create_batch_with_schedule(self, client, test_db, auth_headers_admin):
        """Admin can create batch with schedule."""
        school = _create_school(test_db)
        
        payload = {
            "batch_name": "Scheduled Batch",
            "school_id": school.id,
            "schedule": [
                {
                    "day_of_week": "Monday",
                    "start_time": "04:00 PM",
                    "end_time": "05:00 PM"
                },
                {
                    "day_of_week": "Wednesday",
                    "start_time": "04:00 PM",
                    "end_time": "05:00 PM"
                }
            ]
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_batch_requires_authentication(self, client, test_db):
        """Creating a batch requires authentication."""
        payload = {
            "batch_name": "Unauthorized Batch",
            "school_id": 1
        }

        response = client.post(f"{API_PREFIX}/", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_batch_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can create batches."""
        school = _create_school(test_db)
        
        payload = {
            "batch_name": "Restricted Batch",
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_batch_missing_required_fields(self, client, test_db, auth_headers_admin):
        """Creating batch with missing fields returns validation error."""
        payload = {
            "batch_name": "Incomplete Batch"
            # Missing school_id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_batch_with_nonexistent_school(self, client, test_db, auth_headers_admin):
        """Creating batch with non-existent school ID returns error."""
        payload = {
            "batch_name": "Invalid School Batch",
            "school_id": 99999
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_create_batch_with_invalid_schedule_time(self, client, test_db, auth_headers_admin):
        """Creating batch with invalid time format returns validation error."""
        school = _create_school(test_db)
        
        payload = {
            "batch_name": "Invalid Time Batch",
            "school_id": school.id,
            "schedule": [
                {
                    "day_of_week": "Monday",
                    "start_time": "25:00 PM",  # Invalid time
                    "end_time": "05:00 PM"
                }
            ]
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestBatchListEndpoints:
    """Test batch listing functionality."""

    def test_list_batches_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can list all batches."""
        school = _create_school(test_db)
        _create_batch(test_db, school, name="Batch One")
        _create_batch(test_db, school, name="Batch Two")

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_batches_as_regular_user(self, client, test_db, auth_headers_regular):
        """Regular users can also list batches."""
        school = _create_school(test_db)
        _create_batch(test_db, school, name="Visible Batch")

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_200_OK

    def test_list_batches_requires_authentication(self, client, test_db):
        """Listing batches requires authentication."""
        response = client.get(f"{API_PREFIX}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_batches_pagination(self, client, test_db, auth_headers_admin):
        """Batch listing supports pagination."""
        school = _create_school(test_db)
        for i in range(5):
            _create_batch(test_db, school, name=f"Page Batch {i}")

        response = client.get(f"{API_PREFIX}/?skip=0&limit=2", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 2

    def test_list_batches_empty_database(self, client, test_db, auth_headers_admin):
        """Listing batches in empty database returns empty array."""
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_batch_pre_create_data(self, client, test_db, auth_headers_admin):
        """Admin can get pre-create data (schools)."""
        school = _create_school(test_db)

        response = client.get(f"{API_PREFIX}/pre-create", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "schools" in data

    def test_get_batch_pre_create_requires_admin(self, client, test_db, auth_headers_regular):
        """Pre-create data requires admin privileges."""
        response = client.get(f"{API_PREFIX}/pre-create", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBatchDetailEndpoints:
    """Test batch detail retrieval functionality."""

    def test_get_batch_by_id_success(self, client, test_db, auth_headers_admin):
        """Admin can get specific batch by ID."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="Specific Batch")

        response = client.get(f"{API_PREFIX}/{batch.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["batch_id"] == batch.id
        assert data["batch_name"] == "Specific Batch"
        assert data["school_id"] == school.id

    def test_get_batch_by_id_not_found(self, client, test_db, auth_headers_admin):
        """Getting non-existent batch returns 404."""
        response = client.get(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_batch_by_id_requires_authentication(self, client, test_db):
        """Getting batch by ID requires authentication."""
        response = client.get(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBatchUpdateEndpoints:
    """Test batch update functionality."""

    def test_update_batch_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can update batch information."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="Old Name")

        payload = {
            "batch_name": "New Name"
        }

        response = client.put(f"{API_PREFIX}/{batch.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["batch_name"] == "New Name"

    def test_update_batch_change_school(self, client, test_db, auth_headers_admin):
        """Admin can change batch's school."""
        school1 = _create_school(test_db, name="School 1")
        school2 = _create_school(test_db, name="School 2")
        batch = _create_batch(test_db, school1, name="Batch")

        payload = {
            "school_id": school2.id
        }

        response = client.put(f"{API_PREFIX}/{batch.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["school_id"] == school2.id

    def test_update_batch_schedule(self, client, test_db, auth_headers_admin):
        """Admin can update batch schedule."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="Batch")

        payload = {
            "schedule": [
                {
                    "day_of_week": "Tuesday",
                    "start_time": "03:00 PM",
                    "end_time": "04:00 PM"
                }
            ]
        }

        response = client.put(f"{API_PREFIX}/{batch.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK

    def test_update_batch_requires_authentication(self, client, test_db):
        """Updating batch requires authentication."""
        payload = {"batch_name": "New Name"}
        response = client.put(f"{API_PREFIX}/1", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_batch_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can update batches."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="Batch")
        
        payload = {"batch_name": "New Name"}
        response = client.put(f"{API_PREFIX}/{batch.id}", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_batch_not_found(self, client, test_db, auth_headers_admin):
        """Updating non-existent batch returns 404."""
        payload = {"batch_name": "New Name"}
        response = client.put(f"{API_PREFIX}/99999", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBatchDeleteEndpoints:
    """Test batch deletion functionality."""

    def test_delete_batch_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can delete a batch."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="Delete Batch")

        response = client.delete(f"{API_PREFIX}/{batch.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify batch is deleted
        response = client.get(f"{API_PREFIX}/{batch.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_batch_requires_authentication(self, client, test_db):
        """Deleting batch requires authentication."""
        response = client.delete(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_batch_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can delete batches."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="Batch")
        
        response = client.delete(f"{API_PREFIX}/{batch.id}", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_batch_not_found(self, client, test_db, auth_headers_admin):
        """Deleting non-existent batch returns 404."""
        response = client.delete(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBatchEdgeCases:
    """Test edge cases for batch management."""

    def test_create_batch_with_special_characters_in_name(self, client, test_db, auth_headers_admin):
        """Batch can have special characters in name."""
        school = _create_school(test_db)
        
        payload = {
            "batch_name": "Morning Batch - Grade 5 & 6",
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["batch_name"] == "Morning Batch - Grade 5 & 6"

    def test_create_batch_with_unicode_name(self, client, test_db, auth_headers_admin):
        """Batch can have Unicode characters in name."""
        school = _create_school(test_db)
        
        payload = {
            "batch_name": "Année Première",
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_batch_with_very_long_name(self, client, test_db, auth_headers_admin):
        """Batch can have very long name."""
        school = _create_school(test_db)
        
        payload = {
            "batch_name": "A" * 100,
            "school_id": school.id
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_batch_with_multiple_schedule_entries(self, client, test_db, auth_headers_admin):
        """Batch can have multiple schedule entries."""
        school = _create_school(test_db)
        
        payload = {
            "batch_name": "Full Week Batch",
            "school_id": school.id,
            "schedule": [
                {"day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM"},
                {"day_of_week": "Tuesday", "start_time": "04:00 PM", "end_time": "05:00 PM"},
                {"day_of_week": "Wednesday", "start_time": "04:00 PM", "end_time": "05:00 PM"},
                {"day_of_week": "Thursday", "start_time": "04:00 PM", "end_time": "05:00 PM"},
                {"day_of_week": "Friday", "start_time": "04:00 PM", "end_time": "05:00 PM"}
            ]
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_multiple_batches_same_school(self, client, test_db, auth_headers_admin):
        """Multiple batches can belong to the same school."""
        school = _create_school(test_db)
        
        payload1 = {"batch_name": "Morning Batch", "school_id": school.id}
        response1 = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload1)
        assert response1.status_code == status.HTTP_201_CREATED

        payload2 = {"batch_name": "Evening Batch", "school_id": school.id}
        response2 = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload2)
        assert response2.status_code == status.HTTP_201_CREATED

    def test_update_batch_clear_schedule(self, client, test_db, auth_headers_admin):
        """Admin can clear batch schedule."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school, name="Batch")

        payload = {
            "schedule": []
        }

        response = client.put(f"{API_PREFIX}/{batch.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK

"""
Integration tests for School Management endpoints.
"""
import pytest
from fastapi import status

from src.db.models.school import School


API_PREFIX = "/api/v1/schools"


# Helper Functions --------------------------------------------------------


def _create_school(db, name: str = "Test School", address: str = "Test Address") -> School:
    """Create a test school."""
    school = School(name=name, address=address)
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


# Test Classes ------------------------------------------------------------


class TestSchoolCreationEndpoints:
    """Test school creation functionality."""

    def test_create_school_as_admin_success(self, client, test_db, auth_headers_admin):
        """Admin can create a new school."""
        payload = {
            "name": "New School"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["school_name"] == "New School"
        assert "school_id" in data

    def test_create_school_requires_authentication(self, client, test_db):
        """Creating a school requires authentication."""
        payload = {
            "name": "Unauthorized School",
            "address": "Test Address"
        }

        response = client.post(f"{API_PREFIX}/", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_school_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can create schools."""
        payload = {
            "name": "Restricted School",
            "address": "Test Address"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_school_missing_required_fields(self, client, test_db, auth_headers_admin):
        """Creating school with missing name returns validation error."""
        payload = {}

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_school_with_special_characters(self, client, test_db, auth_headers_admin):
        """School can have special characters in name."""
        payload = {
            "name": "St. Mary's School & College"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_school_with_unicode(self, client, test_db, auth_headers_admin):
        """School can have Unicode characters."""
        payload = {
            "name": "École François"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED


class TestSchoolListEndpoints:
    """Test school listing functionality."""

    def test_list_schools_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can list all schools."""
        _create_school(test_db, name="School One")
        _create_school(test_db, name="School Two")

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_schools_as_regular_user(self, client, test_db, auth_headers_regular):
        """Regular users can also list schools."""
        _create_school(test_db, name="Visible School")

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_200_OK

    def test_list_schools_requires_authentication(self, client, test_db):
        """Listing schools requires authentication."""
        response = client.get(f"{API_PREFIX}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_schools_pagination(self, client, test_db, auth_headers_admin):
        """School listing supports pagination."""
        for i in range(5):
            _create_school(test_db, name=f"Page School {i}")

        response = client.get(f"{API_PREFIX}/?skip=0&limit=2", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 2

    def test_list_schools_empty_database(self, client, test_db, auth_headers_admin):
        """Listing schools in empty database returns empty array."""
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestSchoolDetailEndpoints:
    """Test school detail retrieval functionality."""

    def test_get_school_by_id_success(self, client, test_db, auth_headers_admin):
        """Admin can get specific school by ID."""
        school = _create_school(test_db, name="Specific School", address="Specific Address")

        response = client.get(f"{API_PREFIX}/{school.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == school.id
        assert data["name"] == "Specific School"

    def test_get_school_by_id_not_found(self, client, test_db, auth_headers_admin):
        """Getting non-existent school returns 404."""
        response = client.get(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_school_by_id_requires_authentication(self, client, test_db):
        """Getting school by ID requires authentication."""
        response = client.get(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSchoolUpdateEndpoints:
    """Test school update functionality."""

    def test_update_school_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can update school information."""
        school = _create_school(test_db, name="Old Name")

        payload = {
            "name": "New Name"
        }

        response = client.put(f"{API_PREFIX}/{school.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "New Name"

    def test_update_school_empty_payload(self, client, test_db, auth_headers_admin):
        """Admin can send empty update payload."""
        school = _create_school(test_db, name="School")

        payload = {}

        response = client.put(f"{API_PREFIX}/{school.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "School"

    def test_update_school_requires_authentication(self, client, test_db):
        """Updating school requires authentication."""
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/1", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_school_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can update schools."""
        school = _create_school(test_db, name="School")
        
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/{school.id}", headers=auth_headers_regular, json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_school_not_found(self, client, test_db, auth_headers_admin):
        """Updating non-existent school returns 404."""
        payload = {"name": "New Name"}
        response = client.put(f"{API_PREFIX}/99999", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSchoolDeleteEndpoints:
    """Test school deletion functionality."""

    def test_delete_school_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can delete a school."""
        school = _create_school(test_db, name="Delete School")

        response = client.delete(f"{API_PREFIX}/{school.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify school is deleted
        response = client.get(f"{API_PREFIX}/{school.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_school_requires_authentication(self, client, test_db):
        """Deleting school requires authentication."""
        response = client.delete(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_school_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can delete schools."""
        school = _create_school(test_db, name="School")
        
        response = client.delete(f"{API_PREFIX}/{school.id}", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_school_not_found(self, client, test_db, auth_headers_admin):
        """Deleting non-existent school returns 404."""
        response = client.delete(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSchoolEdgeCases:
    """Test edge cases for school management."""

    def test_create_school_with_very_long_name(self, client, test_db, auth_headers_admin):
        """School can have very long name."""
        payload = {
            "name": "A" * 200
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_school_with_short_name(self, client, test_db, auth_headers_admin):
        """School can have short name."""
        payload = {
            "name": "A"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_school_minimum_name_length(self, client, test_db, auth_headers_admin):
        """School can be created with single character name."""
        payload = {
            "name": "X"
        }
        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

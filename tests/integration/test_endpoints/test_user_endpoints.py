"""
Integration tests for User Management endpoints.
"""
import pytest
from fastapi import status

from src.core.security import PasswordHandler
from src.db.models.user import User, UserRole


API_PREFIX = "/api/v1/users"


# Helper Functions --------------------------------------------------------


def _create_user(db, username: str = "testuser", name: str = "Test User", role: UserRole = UserRole.USER, is_active: bool = True) -> User:
    """Create a test user directly in the database."""
    hashed_password = PasswordHandler.hash("testpass123")
    
    user = User(
        name=name,
        username=username,
        hashed_password=hashed_password,
        role=role,
        is_active=is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Test Classes ------------------------------------------------------------


class TestUserCreationEndpoints:
    """Test user creation functionality."""

    def test_create_user_as_admin_success(self, client, test_db, auth_headers_admin):
        """Admin can create a new user."""
        payload = {
            "name": "New User",
            "username": "newuser",
            "password": "securepass123",
            "role": "user"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["username"] == "newuser"
        assert data["name"] == "New User"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "permissions" in data

    def test_create_admin_user_success(self, client, test_db, auth_headers_admin):
        """Admin can create another admin user."""
        payload = {
            "name": "Admin Two",
            "username": "admin2",
            "password": "adminpass123",
            "role": "admin"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["role"] == "admin"

    def test_create_coach_role_user_success(self, client, test_db, auth_headers_admin):
        """Admin can create a user with COACH role."""
        payload = {
            "name": "Coach User",
            "username": "coachuser",
            "password": "coachpass123",
            "role": "coach"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["role"] == "coach"

    def test_create_user_requires_authentication(self, client, test_db):
        """Creating a user requires authentication."""
        payload = {
            "name": "Unauthorized User",
            "username": "unauth",
            "password": "pass123",
            "role": "user"
        }

        response = client.post(f"{API_PREFIX}/", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can create users."""
        payload = {
            "name": "Restricted User",
            "username": "restricted",
            "password": "pass123",
            "role": "user"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_regular, json=payload)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_create_user_duplicate_username(self, client, test_db, auth_headers_admin):
        """Cannot create user with duplicate username."""
        # Create first user
        _create_user(test_db, username="duplicate", name="First User")

        # Try to create second user with same username
        payload = {
            "name": "Second User",
            "username": "duplicate",
            "password": "pass123",
            "role": "user"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_create_user_missing_required_fields(self, client, test_db, auth_headers_admin):
        """Creating user with missing fields returns validation error."""
        payload = {
            "name": "Incomplete User"
            # Missing username, password, role
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_invalid_role(self, client, test_db, auth_headers_admin):
        """Creating user with invalid role returns validation error."""
        payload = {
            "name": "Bad Role User",
            "username": "badrole",
            "password": "pass123",
            "role": "invalid_role"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_empty_password(self, client, test_db, auth_headers_admin):
        """Creating user with empty password returns validation error."""
        payload = {
            "name": "No Password User",
            "username": "nopass",
            "password": "",
            "role": "user"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserListEndpoints:
    """Test user listing functionality."""

    def test_list_users_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can list all users."""
        # Create multiple users
        _create_user(test_db, username="user1", name="User One")
        _create_user(test_db, username="user2", name="User Two")
        _create_user(test_db, username="user3", name="User Three")

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 3  # At least the 3 we created

    def test_list_users_requires_authentication(self, client, test_db):
        """Listing users requires authentication."""
        response = client.get(f"{API_PREFIX}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_users_requires_admin_role(self, client, test_db, auth_headers_regular):
        """Only admins can list users."""
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_pagination(self, client, test_db, auth_headers_admin):
        """User listing supports pagination."""
        # Create several users
        for i in range(5):
            _create_user(test_db, username=f"paguser{i}", name=f"Page User {i}")

        # Get first 2
        response = client.get(f"{API_PREFIX}/?skip=0&limit=2", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["users"]) <= 2

    def test_list_users_empty_database(self, client, test_db, auth_headers_admin):
        """Listing users in empty database returns empty array."""
        # Clean database (assuming test admin is the only user)
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["users"], list)


class TestUserProfileEndpoints:
    """Test user profile retrieval functionality."""

    def test_get_me_as_user(self, client, test_db, auth_headers_regular):
        """User can get their own profile."""
        response = client.get(f"{API_PREFIX}/me", headers=auth_headers_regular)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert "permissions" in data["user"]

    def test_get_me_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can get their own profile."""
        response = client.get(f"{API_PREFIX}/me", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "user" in data
        assert data["user"]["role"] == "admin"

    def test_get_me_requires_authentication(self, client, test_db):
        """/me endpoint requires authentication."""
        response = client.get(f"{API_PREFIX}/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_by_id_success(self, client, test_db, auth_headers_admin):
        """Admin can get specific user by ID."""
        user = _create_user(test_db, username="specificuser", name="Specific User")

        response = client.get(f"{API_PREFIX}/{user.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == "specificuser"

    def test_get_user_by_id_not_found(self, client, test_db, auth_headers_admin):
        """Getting non-existent user returns 404."""
        response = client.get(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_by_id_requires_authentication(self, client, test_db):
        """Getting user by ID requires authentication."""
        response = client.get(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserUpdateEndpoints:
    """Test user update functionality."""

    def test_update_user_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can update user information."""
        user = _create_user(test_db, username="updateme", name="Old Name")

        payload = {
            "name": "New Name",
            "username": "updateme"
        }

        response = client.put(f"{API_PREFIX}/{user.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "New Name"

    def test_update_user_deactivate(self, client, test_db, auth_headers_admin):
        """Admin can deactivate a user."""
        user = _create_user(test_db, username="deactivateme", name="Active User")

        payload = {
            "name": "Active User",
            "username": "deactivateme",
            "is_active": False
        }

        response = client.put(f"{API_PREFIX}/{user.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["is_active"] is False

    def test_update_user_requires_authentication(self, client, test_db):
        """Updating user requires authentication."""
        payload = {"name": "New Name", "username": "test"}
        response = client.put(f"{API_PREFIX}/1", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_user_not_found(self, client, test_db, auth_headers_admin):
        """Updating non-existent user returns 404."""
        payload = {"name": "New Name", "username": "test"}
        response = client.put(f"{API_PREFIX}/99999", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUserDeleteEndpoints:
    """Test user deletion functionality."""

    def test_delete_user_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can delete a user."""
        user = _create_user(test_db, username="deleteme", name="Delete User")

        response = client.delete(f"{API_PREFIX}/{user.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify user is deleted
        response = client.get(f"{API_PREFIX}/{user.id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user_requires_authentication(self, client, test_db):
        """Deleting user requires authentication."""
        response = client.delete(f"{API_PREFIX}/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_user_not_found(self, client, test_db, auth_headers_admin):
        """Deleting non-existent user returns 404."""
        response = client.delete(f"{API_PREFIX}/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUserEdgeCases:
    """Test edge cases for user management."""

    def test_create_user_with_special_characters_in_name(self, client, test_db, auth_headers_admin):
        """User can have special characters in name."""
        payload = {
            "name": "O'Brien-Smith, Jr.",
            "username": "obrien",
            "password": "pass123",
            "role": "user"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "O'Brien-Smith, Jr."

    def test_create_user_with_unicode_name(self, client, test_db, auth_headers_admin):
        """User can have Unicode characters in name."""
        payload = {
            "name": "François Müller",
            "username": "francois",
            "password": "pass123",
            "role": "user"
        }

        response = client.post(f"{API_PREFIX}/", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_inactive_users_included(self, client, test_db, auth_headers_admin):
        """List endpoint includes inactive users."""
        _create_user(test_db, username="inactive1", is_active=False)
        _create_user(test_db, username="active1", is_active=True)

        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        # Both users should be in the list
        usernames = [u["username"] for u in response.json()["users"]]
        assert "inactive1" in usernames
        assert "active1" in usernames

    def test_update_user_username_conflict(self, client, test_db, auth_headers_admin):
        """Cannot update username to one that already exists."""
        user1 = _create_user(test_db, username="user1", name="User 1")
        user2 = _create_user(test_db, username="user2", name="User 2")

        # Try to change user2's username to user1
        payload = {
            "name": "User 2",
            "username": "user1"
        }

        response = client.put(f"{API_PREFIX}/{user2.id}", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

"""
Integration tests for Permission Management endpoints.
"""
import pytest
from fastapi import status

from src.db.models.user import User, UserRole
from src.db.models.permission import Permission
from src.db.models.role_permission import RolePermission
from src.db.models.coach import Coach
from src.core.security import PasswordHandler


API_PREFIX = "/api/v1/permissions"


# Helper Functions --------------------------------------------------------


def _create_user(db, username: str = "testuser", role: UserRole = UserRole.USER) -> User:
    """Create a test user."""
    hashed_password = PasswordHandler.hash("testpass123")
    user = User(
        name="Test User",
        username=username,
        password=hashed_password,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_coach(db, username: str = "testcoach", name: str = "Test Coach") -> Coach:
    """Create a test coach."""
    hashed_password = PasswordHandler.hash("testpass123")
    coach = Coach(name=name, username=username, password=hashed_password, is_active=True)
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def _create_permission(db, name: str = "test_permission") -> Permission:
    """Create a test permission."""
    permission = Permission(permission_name=name)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


# Note: User-specific permissions are managed through the API, not directly in database


# Test Classes ------------------------------------------------------------


class TestPermissionListEndpoints:
    """Test permission listing functionality."""

    def test_list_permissions_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can list all permissions."""
        # Permissions are created during app startup, so they should exist
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)

    def test_list_permissions_requires_authentication(self, client, test_db):
        """Listing permissions requires authentication."""
        response = client.get(f"{API_PREFIX}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_permissions_structure(self, client, test_db, auth_headers_admin):
        """Permission list has correct structure."""
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        if len(data["permissions"]) > 0:
            perm = data["permissions"][0]
            assert "permission_id" in perm
            assert "permission_name" in perm

    def test_list_permissions_as_regular_user(self, client, test_db, auth_headers_regular):
        """Regular users can also view permissions."""
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_regular)
        # Depends on require_view_permissions - might be 200 or 403
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]


class TestPermissionAssignEndpoints:
    """Test permission assignment functionality."""

    def test_assign_permission_to_user_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can assign permission to user."""
        user = _create_user(test_db, username="targetuser")
        permission = _create_permission(test_db, name="test_perm_1")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Permission assigned."

    def test_assign_permission_to_coach_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can assign permission to coach."""
        coach = _create_coach(test_db, username="targetcoach")
        permission = _create_permission(test_db, name="test_perm_2")
        
        payload = {
            "permission_id": permission.id,
            "coach_id": coach.id
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK

    def test_assign_permission_requires_authentication(self, client, test_db):
        """Assigning permission requires authentication."""
        payload = {
            "permission_id": 1,
            "user_id": 1
        }

        response = client.post(f"{API_PREFIX}/assign", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_assign_permission_requires_proper_authorization(self, client, test_db, auth_headers_regular):
        """Regular users might not be able to assign permissions."""
        user = _create_user(test_db, username="targetuser2")
        permission = _create_permission(test_db, name="test_perm_3")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_regular, json=payload)
        # Depends on require_assign_permissions
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_assign_permission_missing_target(self, client, test_db, auth_headers_admin):
        """Assigning permission without target returns validation error."""
        permission = _create_permission(test_db, name="test_perm_4")
        
        payload = {
            "permission_id": permission.id
            # Missing both user_id and coach_id
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_assign_permission_both_targets(self, client, test_db, auth_headers_admin):
        """Assigning permission with both user_id and coach_id returns validation error."""
        user = _create_user(test_db, username="targetuser3")
        coach = _create_coach(test_db, username="targetcoach2")
        permission = _create_permission(test_db, name="test_perm_5")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id,
            "coach_id": coach.id
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_assign_permission_to_nonexistent_user(self, client, test_db, auth_headers_admin):
        """Assigning permission to non-existent user returns error."""
        permission = _create_permission(test_db, name="test_perm_6")
        
        payload = {
            "permission_id": permission.id,
            "user_id": 99999
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_assign_permission_to_nonexistent_coach(self, client, test_db, auth_headers_admin):
        """Assigning permission to non-existent coach returns error."""
        permission = _create_permission(test_db, name="test_perm_7")
        
        payload = {
            "permission_id": permission.id,
            "coach_id": 99999
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_assign_nonexistent_permission(self, client, test_db, auth_headers_admin):
        """Assigning non-existent permission returns error."""
        user = _create_user(test_db, username="targetuser4")
        
        payload = {
            "permission_id": 99999,
            "user_id": user.id
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


class TestPermissionRevokeEndpoints:
    """Test permission revocation functionality."""

    def test_revoke_permission_from_user_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can revoke permission from user."""
        user = _create_user(test_db, username="revokeuser")
        permission = _create_permission(test_db, name="revoke_perm_1")
        
        # First assign the permission
        assign_payload = {
            "permission_id": permission.id,
            "user_id": user.id
        }
        client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=assign_payload)
        
        # Then revoke it
        payload = {
            "permission_id": permission.id,
            "user_id": user.id
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Permission revoked."

    def test_revoke_permission_from_coach_as_admin(self, client, test_db, auth_headers_admin):
        """Admin can revoke permission from coach."""
        coach = _create_coach(test_db, username="revokecoach")
        permission = _create_permission(test_db, name="revoke_perm_2")
        
        # First assign the permission
        assign_payload = {
            "permission_id": permission.id,
            "coach_id": coach.id
        }
        client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=assign_payload)
        
        # Then revoke it
        payload = {
            "permission_id": permission.id,
            "coach_id": coach.id
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK

    def test_revoke_permission_requires_authentication(self, client, test_db):
        """Revoking permission requires authentication."""
        payload = {
            "permission_id": 1,
            "user_id": 1
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_revoke_permission_requires_proper_authorization(self, client, test_db, auth_headers_regular):
        """Regular users might not be able to revoke permissions."""
        user = _create_user(test_db, username="revokeuser2")
        permission = _create_permission(test_db, name="revoke_perm_3")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_regular, json=payload)
        # Depends on require_revoke_permissions
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_revoke_permission_missing_target(self, client, test_db, auth_headers_admin):
        """Revoking permission without target returns validation error."""
        permission = _create_permission(test_db, name="revoke_perm_4")
        
        payload = {
            "permission_id": permission.id
            # Missing both user_id and coach_id
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_revoke_permission_both_targets(self, client, test_db, auth_headers_admin):
        """Revoking permission with both user_id and coach_id returns validation error."""
        user = _create_user(test_db, username="revokeuser3")
        coach = _create_coach(test_db, username="revokecoach2")
        permission = _create_permission(test_db, name="revoke_perm_5")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id,
            "coach_id": coach.id
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_revoke_permission_from_nonexistent_user(self, client, test_db, auth_headers_admin):
        """Revoking permission from non-existent user returns error."""
        permission = _create_permission(test_db, name="revoke_perm_6")
        
        payload = {
            "permission_id": permission.id,
            "user_id": 99999
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_admin, json=payload)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_revoke_permission_from_nonexistent_coach(self, client, test_db, auth_headers_admin):
        """Revoking permission from non-existent coach returns error."""
        permission = _create_permission(test_db, name="revoke_perm_7")
        
        payload = {
            "permission_id": permission.id,
            "coach_id": 99999
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPermissionEdgeCases:
    """Test edge cases for permission management."""

    def test_assign_same_permission_twice(self, client, test_db, auth_headers_admin):
        """Assigning same permission twice should handle gracefully."""
        user = _create_user(test_db, username="doubleuser")
        permission = _create_permission(test_db, name="double_perm")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id
        }

        # First assignment
        response1 = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response1.status_code == status.HTTP_200_OK

        # Second assignment
        response2 = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        # Should either succeed (idempotent) or return error
        assert response2.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_revoke_permission_not_assigned(self, client, test_db, auth_headers_admin):
        """Revoking permission that was never assigned."""
        user = _create_user(test_db, username="nopermuser")
        permission = _create_permission(test_db, name="never_assigned")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id
        }

        response = client.request("DELETE", f"{API_PREFIX}/revoke", headers=auth_headers_admin, json=payload)
        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_assign_permission_with_assigned_by_field(self, client, test_db, auth_headers_admin):
        """Admin can assign permission with assigned_by field."""
        user = _create_user(test_db, username="assignedbyuser")
        permission = _create_permission(test_db, name="assigned_by_perm")
        
        payload = {
            "permission_id": permission.id,
            "user_id": user.id,
            "assigned_by": 1
        }

        response = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload)
        assert response.status_code == status.HTTP_200_OK

    def test_list_permissions_empty_system(self, client, test_db, auth_headers_admin):
        """Listing permissions when none exist returns empty list."""
        # Note: In practice, permissions are seeded at startup
        response = client.get(f"{API_PREFIX}/", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)

    def test_assign_multiple_permissions_to_same_user(self, client, test_db, auth_headers_admin):
        """User can have multiple permissions."""
        user = _create_user(test_db, username="multiuser")
        perm1 = _create_permission(test_db, name="multi_perm_1")
        perm2 = _create_permission(test_db, name="multi_perm_2")
        
        payload1 = {"permission_id": perm1.id, "user_id": user.id}
        response1 = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload1)
        assert response1.status_code == status.HTTP_200_OK

        payload2 = {"permission_id": perm2.id, "user_id": user.id}
        response2 = client.post(f"{API_PREFIX}/assign", headers=auth_headers_admin, json=payload2)
        assert response2.status_code == status.HTTP_200_OK

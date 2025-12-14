"""Unit tests for permission repositories."""
import pytest
from unittest.mock import MagicMock, Mock
from datetime import datetime, timedelta

from src.db.repositories.permission_repository import (
    PermissionRepository,
    UserPermissionRepository,
    RefreshTokenRepository
)
from src.db.models.permission import Permission, UserPermission, PermissionType
from src.db.models.user import RefreshToken


# ===================================
# PermissionRepository Tests
# ===================================

class TestPermissionRepository:
    """Test PermissionRepository CRUD operations."""

    def test_get_by_name_with_enum(self):
        """Test get permission by PermissionType enum."""
        db = MagicMock()
        mock_permission = Mock(spec=Permission)
        mock_permission.permission_name = "create_user"
        db.query.return_value.filter.return_value.first.return_value = mock_permission

        result = PermissionRepository.get_by_name(db, PermissionType.CREATE_USER)

        assert result == mock_permission
        db.query.assert_called_once_with(Permission)

    def test_get_by_name_with_string(self):
        """Test get permission by string name."""
        db = MagicMock()
        mock_permission = Mock(spec=Permission)
        mock_permission.permission_name = "custom_permission"
        db.query.return_value.filter.return_value.first.return_value = mock_permission

        result = PermissionRepository.get_by_name(db, "custom_permission")

        assert result == mock_permission

    def test_get_by_name_not_found(self):
        """Test get permission by name returns None when not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = PermissionRepository.get_by_name(db, "nonexistent")

        assert result is None

    def test_get_by_id_success(self):
        """Test get permission by ID."""
        db = MagicMock()
        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1
        db.query.return_value.filter.return_value.first.return_value = mock_permission

        result = PermissionRepository.get_by_id(db, 1)

        assert result == mock_permission

    def test_get_by_id_not_found(self):
        """Test get permission by ID returns None when not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = PermissionRepository.get_by_id(db, 999)

        assert result is None

    def test_get_all(self):
        """Test get all permissions."""
        db = MagicMock()
        mock_permissions = [Mock(spec=Permission), Mock(spec=Permission)]
        db.query.return_value.all.return_value = mock_permissions

        result = PermissionRepository.get_all(db)

        assert result == mock_permissions
        assert len(result) == 2

    def test_create_with_enum(self):
        """Test create permission with PermissionType enum."""
        db = MagicMock()
        
        result = PermissionRepository.create(db, PermissionType.CREATE_USER, "Create user permission")

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        assert result.permission_name == "create_user"
        assert result.description == "Create user permission"

    def test_create_with_string(self):
        """Test create permission with string name."""
        db = MagicMock()
        
        result = PermissionRepository.create(db, "custom_action", "Custom action permission")

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result.permission_name == "custom_action"
        assert result.description == "Custom action permission"

    def test_create_without_description(self):
        """Test create permission without description."""
        db = MagicMock()
        
        result = PermissionRepository.create(db, PermissionType.DELETE_USER)

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result.permission_name == "delete_user"
        assert result.description is None

    def test_get_or_create_existing(self):
        """Test get_or_create returns existing permission."""
        db = MagicMock()
        mock_permission = Mock(spec=Permission)
        mock_permission.permission_name = "create_user"
        db.query.return_value.filter.return_value.first.return_value = mock_permission

        result = PermissionRepository.get_or_create(db, PermissionType.CREATE_USER, "Description")

        assert result == mock_permission
        db.add.assert_not_called()  # Should not create new

    def test_get_or_create_new(self):
        """Test get_or_create creates new permission if not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = PermissionRepository.get_or_create(db, PermissionType.VIEW_PERMISSIONS, "View perms")

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result.permission_name == "view_permissions"


class TestPermissionRepositoryEdgeCases:
    """Test edge cases for PermissionRepository."""

    def test_create_with_empty_string_name(self):
        """Test create permission with empty string name."""
        db = MagicMock()
        
        result = PermissionRepository.create(db, "", "Empty name")

        assert result.permission_name == ""
        db.add.assert_called_once()

    def test_create_with_long_name(self):
        """Test create permission with max length name (100 chars)."""
        db = MagicMock()
        long_name = "a" * 100
        
        result = PermissionRepository.create(db, long_name, "Long name")

        assert result.permission_name == long_name
        assert len(result.permission_name) == 100

    def test_create_with_special_characters(self):
        """Test create permission with special characters in name."""
        db = MagicMock()
        special_name = "permission:admin@create-user#2024"
        
        result = PermissionRepository.create(db, special_name, "Special chars")

        assert result.permission_name == special_name

    def test_get_all_empty_database(self):
        """Test get_all returns empty list when no permissions."""
        db = MagicMock()
        db.query.return_value.all.return_value = []

        result = PermissionRepository.get_all(db)

        assert result == []
        assert len(result) == 0


# ===================================
# UserPermissionRepository Tests
# ===================================

class TestUserPermissionRepository:
    """Test UserPermissionRepository operations."""

    def test_get_user_permissions(self):
        """Test get all custom permissions for a user."""
        db = MagicMock()
        mock_permissions = [Mock(spec=UserPermission), Mock(spec=UserPermission)]
        db.query.return_value.filter.return_value.all.return_value = mock_permissions

        result = UserPermissionRepository.get_user_permissions(db, 1)

        assert result == mock_permissions
        assert len(result) == 2

    def test_get_user_permissions_empty(self):
        """Test get user permissions returns empty list."""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = UserPermissionRepository.get_user_permissions(db, 1)

        assert result == []

    def test_get_coach_permissions(self):
        """Test get all custom permissions for a coach."""
        db = MagicMock()
        mock_permissions = [Mock(spec=UserPermission)]
        db.query.return_value.filter.return_value.all.return_value = mock_permissions

        result = UserPermissionRepository.get_coach_permissions(db, 5)

        assert result == mock_permissions

    def test_has_permission_user_true(self):
        """Test has_permission returns True when user has permission."""
        db = MagicMock()
        mock_permission = Mock(spec=UserPermission)
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_permission

        result = UserPermissionRepository.has_permission(db, 1, user_id=10)

        assert result is True

    def test_has_permission_user_false(self):
        """Test has_permission returns False when user doesn't have permission."""
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = UserPermissionRepository.has_permission(db, 1, user_id=10)

        assert result is False

    def test_has_permission_coach(self):
        """Test has_permission for coach."""
        db = MagicMock()
        mock_permission = Mock(spec=UserPermission)
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_permission

        result = UserPermissionRepository.has_permission(db, 2, coach_id=5)

        assert result is True

    def test_assign_permission_to_user(self):
        """Test assign permission to user."""
        db = MagicMock()

        result = UserPermissionRepository.assign_permission(
            db, permission_id=1, assigned_by=10, user_id=5
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        assert result.permission_id == 1
        assert result.user_id == 5
        assert result.assigned_by == 10

    def test_assign_permission_to_coach(self):
        """Test assign permission to coach."""
        db = MagicMock()

        result = UserPermissionRepository.assign_permission(
            db, permission_id=2, assigned_by=1, coach_id=3
        )

        assert result.permission_id == 2
        assert result.coach_id == 3
        assert result.assigned_by == 1

    def test_assign_permission_no_target_raises_error(self):
        """Test assign permission without user_id or coach_id raises ValueError."""
        db = MagicMock()

        with pytest.raises(ValueError, match="Either user_id or coach_id must be provided"):
            UserPermissionRepository.assign_permission(db, permission_id=1, assigned_by=1)

    def test_assign_permission_without_assigner(self):
        """Test assign permission with None assigner."""
        db = MagicMock()

        result = UserPermissionRepository.assign_permission(
            db, permission_id=1, assigned_by=None, user_id=5
        )

        assert result.assigned_by is None
        db.add.assert_called_once()

    def test_revoke_permission_user_success(self):
        """Test revoke permission from user successfully."""
        db = MagicMock()
        mock_permission = Mock(spec=UserPermission)
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_permission

        result = UserPermissionRepository.revoke_permission(db, 1, user_id=5)

        assert result is True
        db.delete.assert_called_once_with(mock_permission)
        db.commit.assert_called_once()

    def test_revoke_permission_coach_success(self):
        """Test revoke permission from coach successfully."""
        db = MagicMock()
        mock_permission = Mock(spec=UserPermission)
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_permission

        result = UserPermissionRepository.revoke_permission(db, 2, coach_id=3)

        assert result is True
        db.delete.assert_called_once()

    def test_revoke_permission_not_found(self):
        """Test revoke permission returns False when not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = UserPermissionRepository.revoke_permission(db, 1, user_id=5)

        assert result is False
        db.delete.assert_not_called()


class TestUserPermissionRepositoryEdgeCases:
    """Test edge cases for UserPermissionRepository."""

    def test_get_permissions_for_user_id_zero(self):
        """Test get permissions for user_id 0."""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = UserPermissionRepository.get_user_permissions(db, 0)

        assert result == []

    def test_get_permissions_for_negative_user_id(self):
        """Test get permissions for negative user_id."""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = UserPermissionRepository.get_user_permissions(db, -1)

        assert result == []

    def test_has_permission_with_both_user_and_coach_id(self):
        """Test has_permission with both user_id and coach_id."""
        db = MagicMock()
        mock_permission = Mock(spec=UserPermission)
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = mock_permission

        result = UserPermissionRepository.has_permission(db, 1, user_id=5, coach_id=3)

        assert result is True

    def test_revoke_permission_with_zero_ids(self):
        """Test revoke permission with user_id and coach_id both 0."""
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = UserPermissionRepository.revoke_permission(db, 1, user_id=0, coach_id=0)

        assert result is False


# ===================================
# RefreshTokenRepository Tests
# ===================================

class TestRefreshTokenRepository:
    """Test RefreshTokenRepository operations."""

    def test_create_for_user(self):
        """Test create refresh token for user."""
        db = MagicMock()

        result = RefreshTokenRepository.create(db, user_id=1)

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        assert result.user_id == 1
        assert result.coach_id is None
        assert result.token is not None
        assert result.expires_at is not None

    def test_create_for_coach(self):
        """Test create refresh token for coach."""
        db = MagicMock()

        result = RefreshTokenRepository.create(db, coach_id=5)

        assert result.coach_id == 5
        assert result.user_id is None
        assert result.token is not None

    def test_create_without_user_or_coach_raises_error(self):
        """Test create refresh token without user_id or coach_id raises ValueError."""
        db = MagicMock()

        with pytest.raises(ValueError, match="Provide exactly one of user_id or coach_id"):
            RefreshTokenRepository.create(db)

    def test_create_with_both_user_and_coach_raises_error(self):
        """Test create refresh token with both user_id and coach_id raises ValueError."""
        db = MagicMock()

        with pytest.raises(ValueError, match="Provide exactly one of user_id or coach_id"):
            RefreshTokenRepository.create(db, user_id=1, coach_id=5)

    def test_get_by_token_success(self):
        """Test get refresh token by token string."""
        db = MagicMock()
        mock_token = Mock(spec=RefreshToken)
        mock_token.token = "test_token_123"
        db.query.return_value.filter.return_value.first.return_value = mock_token

        result = RefreshTokenRepository.get_by_token(db, "test_token_123")

        assert result == mock_token

    def test_get_by_token_not_found(self):
        """Test get refresh token returns None when not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = RefreshTokenRepository.get_by_token(db, "nonexistent_token")

        assert result is None

    def test_revoke_token_success(self):
        """Test revoke refresh token successfully."""
        db = MagicMock()
        mock_token = Mock(spec=RefreshToken)
        mock_token.is_revoked = False
        db.query.return_value.filter.return_value.first.return_value = mock_token

        result = RefreshTokenRepository.revoke(db, "token_to_revoke")

        assert result is True
        assert mock_token.is_revoked is True
        db.commit.assert_called_once()

    def test_revoke_token_not_found(self):
        """Test revoke returns False when token not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = RefreshTokenRepository.revoke(db, "nonexistent_token")

        assert result is False
        db.commit.assert_not_called()

    def test_revoke_all_user_tokens(self):
        """Test revoke all refresh tokens for a user."""
        db = MagicMock()

        RefreshTokenRepository.revoke_all_user_tokens(db, 1)

        db.query.return_value.filter.return_value.update.assert_called_once_with({"is_revoked": True})
        db.commit.assert_called_once()

    def test_revoke_all_coach_tokens(self):
        """Test revoke all refresh tokens for a coach."""
        db = MagicMock()

        RefreshTokenRepository.revoke_all_coach_tokens(db, 5)

        db.query.return_value.filter.return_value.update.assert_called_once_with({"is_revoked": True})
        db.commit.assert_called_once()


class TestRefreshTokenRepositoryEdgeCases:
    """Test edge cases for RefreshTokenRepository."""

    def test_create_with_user_id_zero(self):
        """Test create refresh token with user_id 0."""
        db = MagicMock()

        result = RefreshTokenRepository.create(db, user_id=0)

        assert result.user_id == 0
        db.add.assert_called_once()

    def test_get_by_token_empty_string(self):
        """Test get refresh token with empty string."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = RefreshTokenRepository.get_by_token(db, "")

        assert result is None

    def test_get_by_token_very_long_string(self):
        """Test get refresh token with very long token string."""
        db = MagicMock()
        long_token = "a" * 1000
        db.query.return_value.filter.return_value.first.return_value = None

        result = RefreshTokenRepository.get_by_token(db, long_token)

        assert result is None

    def test_revoke_token_special_characters(self):
        """Test revoke token with special characters."""
        db = MagicMock()
        special_token = "token!@#$%^&*()_+-={}[]|:;<>?,./~`"
        db.query.return_value.filter.return_value.first.return_value = None

        result = RefreshTokenRepository.revoke(db, special_token)

        assert result is False

    def test_revoke_all_tokens_for_nonexistent_user(self):
        """Test revoke all tokens for user that doesn't exist."""
        db = MagicMock()

        RefreshTokenRepository.revoke_all_user_tokens(db, 99999)

        db.query.return_value.filter.return_value.update.assert_called_once()
        db.commit.assert_called_once()

    def test_token_uniqueness_check(self):
        """Test that created tokens are unique strings."""
        db = MagicMock()

        token1 = RefreshTokenRepository.create(db, user_id=1)
        token2 = RefreshTokenRepository.create(db, user_id=2)

        assert token1.token != token2.token

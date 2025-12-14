"""Unit tests for permission service."""
import pytest
from unittest.mock import MagicMock, Mock, patch
from fastapi import HTTPException

from src.services.permission_service import PermissionService
from src.db.models.permission import Permission, UserPermission, PermissionType
from src.db.models.user import User, UserRole


# ===================================
# PermissionService Tests
# ===================================

class TestPermissionServiceGetUserPermissions:
    """Test get_user_permissions method."""

    def test_get_admin_permissions(self):
        """Test get permissions for ADMIN role."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.ADMIN

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.get_user_permissions(db, user)

            # ADMIN should have many base permissions
            assert len(result) > 0
            permission_values = [p.value for p in result]
            assert PermissionType.CREATE_USER.value in permission_values
            assert PermissionType.DELETE_USER.value in permission_values
            assert PermissionType.ASSIGN_PERMISSIONS.value in permission_values

    def test_get_user_permissions_regular(self):
        """Test get permissions for USER role."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 2
        user.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.get_user_permissions(db, user)

            permission_values = [p.value for p in result]
            assert PermissionType.VIEW_OWN_PROFILE.value in permission_values
            assert PermissionType.EDIT_OWN_PROFILE.value in permission_values
            assert PermissionType.CREATE_USER.value not in permission_values

    def test_get_coach_permissions(self):
        """Test get permissions for COACH role."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 3
        user.role = UserRole.COACH

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.get_user_permissions(db, user)

            permission_values = [p.value for p in result]
            assert PermissionType.VIEW_OWN_PROFILE.value in permission_values
            assert PermissionType.PHYSICAL_SESSIONS_VIEW.value in permission_values

    def test_get_permissions_with_custom_permissions(self):
        """Test get permissions includes custom assigned permissions."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        mock_custom_permission = Mock(spec=UserPermission)
        mock_custom_permission.permission = Mock(spec=Permission)
        mock_custom_permission.permission.permission_name = "custom_action"

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = [mock_custom_permission]

            result = PermissionService.get_user_permissions(db, user)

            permission_values = [p.value for p in result]
            assert "custom_action" in permission_values

    def test_get_permissions_filters_duplicates(self):
        """Test that duplicate permissions are filtered."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        # Create custom permission that duplicates a base permission
        mock_custom_permission = Mock(spec=UserPermission)
        mock_custom_permission.permission = Mock(spec=Permission)
        mock_custom_permission.permission.permission_name = PermissionType.VIEW_OWN_PROFILE.value

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = [mock_custom_permission]

            result = PermissionService.get_user_permissions(db, user)

            permission_values = [p.value for p in result]
            # Should appear only once
            assert permission_values.count(PermissionType.VIEW_OWN_PROFILE.value) == 1

    def test_get_permissions_sorted(self):
        """Test that permissions are returned sorted."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.get_user_permissions(db, user)

            permission_values = [p.value for p in result]
            assert permission_values == sorted(permission_values)


class TestPermissionServiceHasPermission:
    """Test has_permission method."""

    def test_has_permission_with_enum_true(self):
        """Test has_permission with PermissionType enum returns True."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.ADMIN

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.has_permission(db, user, PermissionType.CREATE_USER)

            assert result is True

    def test_has_permission_with_string_true(self):
        """Test has_permission with string returns True."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.has_permission(db, user, "view_own_profile")

            assert result is True

    def test_has_permission_false(self):
        """Test has_permission returns False when user doesn't have permission."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.has_permission(db, user, PermissionType.DELETE_ADMIN)

            assert result is False

    def test_has_custom_permission(self):
        """Test has_permission with custom permission."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        mock_custom = Mock(spec=UserPermission)
        mock_custom.permission = Mock(spec=Permission)
        mock_custom.permission.permission_name = "manage_tournaments"

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = [mock_custom]

            result = PermissionService.has_permission(db, user, "manage_tournaments")

            assert result is True


class TestPermissionServiceCanCreateRole:
    """Test can_create_role method."""

    def test_admin_can_create_user(self):
        """Test ADMIN can create USER role."""
        db = MagicMock()
        admin = Mock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_create_role(db, admin, UserRole.USER)

            assert result is True

    def test_admin_can_create_coach(self):
        """Test ADMIN can create COACH role."""
        db = MagicMock()
        admin = Mock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_create_role(db, admin, UserRole.COACH)

            assert result is True

    def test_admin_can_create_admin(self):
        """Test ADMIN can create ADMIN role."""
        db = MagicMock()
        admin = Mock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_create_role(db, admin, UserRole.ADMIN)

            assert result is True

    def test_user_cannot_create_user(self):
        """Test USER cannot create USER role."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_create_role(db, user, UserRole.USER)

            assert result is False

    def test_coach_cannot_create_admin(self):
        """Test COACH cannot create ADMIN role."""
        db = MagicMock()
        coach = Mock(spec=User)
        coach.id = 1
        coach.role = UserRole.COACH

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_create_role(db, coach, UserRole.ADMIN)

            assert result is False


class TestPermissionServiceCanDeleteUser:
    """Test can_delete_user method."""

    def test_admin_can_delete_user(self):
        """Test ADMIN can delete USER."""
        db = MagicMock()
        admin = Mock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN

        target = Mock(spec=User)
        target.id = 2
        target.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_delete_user(db, admin, target)

            assert result is True

    def test_admin_can_delete_coach(self):
        """Test ADMIN can delete COACH."""
        db = MagicMock()
        admin = Mock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN

        target = Mock(spec=User)
        target.id = 2
        target.role = UserRole.COACH

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_delete_user(db, admin, target)

            assert result is True

    def test_user_cannot_delete_user(self):
        """Test USER cannot delete another USER."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        target = Mock(spec=User)
        target.id = 2
        target.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_delete_user(db, user, target)

            assert result is False


class TestPermissionServiceCanManagePermissions:
    """Test can_manage_permissions method."""

    def test_admin_can_manage_user_permissions(self):
        """Test ADMIN can manage USER permissions."""
        db = MagicMock()
        admin = Mock(spec=User)
        admin.id = 1
        admin.role = UserRole.ADMIN

        target = Mock(spec=User)
        target.id = 2
        target.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_manage_permissions(db, admin, target)

            assert result is True

    def test_cannot_manage_own_permissions(self):
        """Test user cannot manage their own permissions."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.ADMIN

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_manage_permissions(db, user, user)

            assert result is False

    def test_non_admin_cannot_manage_permissions(self):
        """Test non-ADMIN cannot manage permissions."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        target = Mock(spec=User)
        target.id = 2
        target.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_manage_permissions(db, user, target)

            assert result is False

    def test_coach_cannot_manage_permissions(self):
        """Test COACH cannot manage permissions."""
        db = MagicMock()
        coach = Mock(spec=User)
        coach.id = 1
        coach.role = UserRole.COACH

        target = Mock(spec=User)
        target.id = 2
        target.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.can_manage_permissions(db, coach, target)

            assert result is False


class TestPermissionServiceGetAllPermissions:
    """Test get_all_permissions method."""

    def test_get_all_permissions(self):
        """Test get all permissions."""
        db = MagicMock()
        mock_permissions = [Mock(spec=Permission) for _ in range(5)]

        with patch('src.services.permission_service.PermissionRepository') as mock_repo:
            mock_repo.get_all.return_value = mock_permissions

            result = PermissionService.get_all_permissions(db)

            assert result == mock_permissions
            assert len(result) == 5

    def test_get_all_permissions_empty(self):
        """Test get all permissions returns empty list."""
        db = MagicMock()

        with patch('src.services.permission_service.PermissionRepository') as mock_repo:
            mock_repo.get_all.return_value = []

            result = PermissionService.get_all_permissions(db)

            assert result == []


class TestPermissionServiceGetPermissionById:
    """Test get_permission_by_id method."""

    def test_get_permission_by_id_success(self):
        """Test get permission by ID successfully."""
        db = MagicMock()
        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1

        with patch('src.services.permission_service.PermissionRepository') as mock_repo:
            mock_repo.get_by_id.return_value = mock_permission

            result = PermissionService.get_permission_by_id(db, 1)

            assert result == mock_permission

    def test_get_permission_by_id_not_found(self):
        """Test get permission by ID raises 404 when not found."""
        db = MagicMock()

        with patch('src.services.permission_service.PermissionRepository') as mock_repo:
            mock_repo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                PermissionService.get_permission_by_id(db, 999)

            assert exc_info.value.status_code == 404
            assert "Permission not found" in exc_info.value.detail


class TestPermissionServiceAssignPermissionById:
    """Test assign_permission_by_id method."""

    def test_assign_permission_to_user_success(self):
        """Test assign permission to user successfully."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1
        assigner.username = "admin_user"

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1
        mock_permission.permission_name = "test_permission"

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_by_id.return_value = mock_permission
            user_perm_repo.has_permission.return_value = False

            PermissionService.assign_permission_by_id(
                db, permission_id=1, assigner=assigner, user_id=5
            )

            user_perm_repo.assign_permission.assert_called_once()
            user_perm_repo.has_permission.assert_called_once_with(
                db, 1, user_id=5, coach_id=None
            )

    def test_assign_permission_to_coach_success(self):
        """Test assign permission to coach successfully."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1
        assigner.username = "admin_user"

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 2
        mock_permission.permission_name = "coach_permission"

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_by_id.return_value = mock_permission
            user_perm_repo.has_permission.return_value = False

            PermissionService.assign_permission_by_id(
                db, permission_id=2, assigner=assigner, coach_id=3
            )

            user_perm_repo.assign_permission.assert_called_once()

    def test_assign_permission_no_target_raises_error(self):
        """Test assign permission without user_id or coach_id raises 400."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1

        with pytest.raises(HTTPException) as exc_info:
            PermissionService.assign_permission_by_id(
                db, permission_id=1, assigner=assigner
            )

        assert exc_info.value.status_code == 400
        assert "Provide exactly one of user_id or coach_id" in exc_info.value.detail

    def test_assign_permission_both_targets_raises_error(self):
        """Test assign permission with both user_id and coach_id raises 400."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1

        with pytest.raises(HTTPException) as exc_info:
            PermissionService.assign_permission_by_id(
                db, permission_id=1, assigner=assigner, user_id=5, coach_id=3
            )

        assert exc_info.value.status_code == 400

    def test_assign_permission_already_assigned_raises_error(self):
        """Test assign permission that's already assigned raises 400."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_by_id.return_value = mock_permission
            user_perm_repo.has_permission.return_value = True

            with pytest.raises(HTTPException) as exc_info:
                PermissionService.assign_permission_by_id(
                    db, permission_id=1, assigner=assigner, user_id=5
                )

            assert exc_info.value.status_code == 400
            assert "Permission already assigned" in exc_info.value.detail

    def test_assign_permission_not_found(self):
        """Test assign non-existent permission raises 404."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1

        with patch('src.services.permission_service.PermissionRepository') as perm_repo:
            perm_repo.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                PermissionService.assign_permission_by_id(
                    db, permission_id=999, assigner=assigner, user_id=5
                )

            assert exc_info.value.status_code == 404


class TestPermissionServiceRevokePermissionById:
    """Test revoke_permission_by_id method."""

    def test_revoke_permission_from_user_success(self):
        """Test revoke permission from user successfully."""
        db = MagicMock()
        revoker = Mock(spec=User)
        revoker.id = 1
        revoker.username = "admin_user"

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1
        mock_permission.permission_name = "test_permission"

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_by_id.return_value = mock_permission
            user_perm_repo.revoke_permission.return_value = True

            PermissionService.revoke_permission_by_id(
                db, permission_id=1, revoker=revoker, user_id=5
            )

            user_perm_repo.revoke_permission.assert_called_once()

    def test_revoke_permission_from_coach_success(self):
        """Test revoke permission from coach successfully."""
        db = MagicMock()
        revoker = Mock(spec=User)
        revoker.id = 1
        revoker.username = "admin_user"

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 2

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_by_id.return_value = mock_permission
            user_perm_repo.revoke_permission.return_value = True

            PermissionService.revoke_permission_by_id(
                db, permission_id=2, revoker=revoker, coach_id=3
            )

            user_perm_repo.revoke_permission.assert_called_once()

    def test_revoke_permission_not_assigned_raises_error(self):
        """Test revoke permission that wasn't assigned raises 400."""
        db = MagicMock()
        revoker = Mock(spec=User)
        revoker.id = 1

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_by_id.return_value = mock_permission
            user_perm_repo.revoke_permission.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                PermissionService.revoke_permission_by_id(
                    db, permission_id=1, revoker=revoker, user_id=5
                )

            assert exc_info.value.status_code == 400
            assert "Permission not assigned to target" in exc_info.value.detail

    def test_revoke_permission_no_target_raises_error(self):
        """Test revoke permission without user_id or coach_id raises 400."""
        db = MagicMock()
        revoker = Mock(spec=User)
        revoker.id = 1

        with pytest.raises(HTTPException) as exc_info:
            PermissionService.revoke_permission_by_id(
                db, permission_id=1, revoker=revoker
            )

        assert exc_info.value.status_code == 400


class TestPermissionServiceEdgeCases:
    """Test edge cases for PermissionService."""

    def test_assign_permission_with_zero_user_id(self):
        """Test assign permission converts 0 user_id to None."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1

        with pytest.raises(HTTPException) as exc_info:
            PermissionService.assign_permission_by_id(
                db, permission_id=1, assigner=assigner, user_id=0, coach_id=0
            )

        assert exc_info.value.status_code == 400

    def test_get_permission_details_with_none_permission(self):
        """Test get_user_permission_details handles None permission."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        mock_assignment = Mock(spec=UserPermission)
        mock_assignment.permission = None

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo, \
             patch('src.services.permission_service.PermissionRepository'):
            mock_repo.get_user_permissions.return_value = [mock_assignment]

            result = PermissionService.get_user_permission_details(db, user)

            # Should skip None permission
            assert all(detail.permission_name for detail in result)

    def test_has_permission_with_empty_string(self):
        """Test has_permission with empty string permission."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = []

            result = PermissionService.has_permission(db, user, "")

            assert result is False

    def test_can_create_role_with_custom_permission(self):
        """Test can_create_role with user having custom CREATE_COACH permission."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        mock_custom = Mock(spec=UserPermission)
        mock_custom.permission = Mock(spec=Permission)
        mock_custom.permission.permission_name = "create_coach"

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo:
            mock_repo.get_user_permissions.return_value = [mock_custom]

            result = PermissionService.can_create_role(db, user, UserRole.COACH)

            assert result is True

    def test_revoke_permission_alternate_method(self):
        """Test alternate revoke_permission method with PermissionType."""
        db = MagicMock()
        revoker = Mock(spec=User)
        revoker.id = 1
        revoker.username = "admin"

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_by_name.return_value = mock_permission
            user_perm_repo.revoke_permission.return_value = True

            PermissionService.revoke_permission(
                db, user_id=5, permission_type=PermissionType.VIEW_PERMISSIONS, revoker=revoker
            )

            user_perm_repo.revoke_permission.assert_called_once()

    def test_revoke_permission_not_found_raises_404(self):
        """Test alternate revoke_permission raises 404 when permission not found."""
        db = MagicMock()
        revoker = Mock(spec=User)
        revoker.id = 1

        with patch('src.services.permission_service.PermissionRepository') as perm_repo:
            perm_repo.get_by_name.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                PermissionService.revoke_permission(
                    db, user_id=5, permission_type=PermissionType.VIEW_PERMISSIONS, revoker=revoker
                )

            assert exc_info.value.status_code == 404

    def test_assign_permission_alternate_method(self):
        """Test alternate assign_permission method with PermissionType."""
        db = MagicMock()
        assigner = Mock(spec=User)
        assigner.id = 1
        assigner.username = "admin"

        mock_permission = Mock(spec=Permission)
        mock_permission.id = 1

        with patch('src.services.permission_service.PermissionRepository') as perm_repo, \
             patch('src.services.permission_service.UserPermissionRepository') as user_perm_repo:
            perm_repo.get_or_create.return_value = mock_permission
            user_perm_repo.has_permission.return_value = False

            PermissionService.assign_permission(
                db, user_id=5, permission_type=PermissionType.EDIT_ALL_USERS, assigner=assigner
            )

            user_perm_repo.assign_permission.assert_called_once()

    def test_get_permission_details_sorted(self):
        """Test get_user_permission_details returns sorted results."""
        db = MagicMock()
        user = Mock(spec=User)
        user.id = 1
        user.role = UserRole.USER

        with patch('src.services.permission_service.UserPermissionRepository') as mock_repo, \
             patch('src.services.permission_service.PermissionRepository') as perm_repo:
            mock_repo.get_user_permissions.return_value = []
            
            # Mock get_or_create to return different permissions
            def mock_get_or_create(db, perm, desc):
                p = Mock(spec=Permission)
                p.permission_name = perm.value
                p.id = hash(perm.value) % 1000
                return p
            
            perm_repo.get_or_create.side_effect = mock_get_or_create

            result = PermissionService.get_user_permission_details(db, user)

            # Verify sorted by permission_name
            permission_names = [detail.permission_name for detail in result]
            assert permission_names == sorted(permission_names)

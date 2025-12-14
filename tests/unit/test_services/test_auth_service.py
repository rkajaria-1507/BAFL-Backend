"""
Unit tests for AuthService
Tests authentication business logic with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException

from src.services.auth_service import AuthService
from src.db.models.user import User, UserRole
from src.db.models.coach import Coach


@pytest.mark.unit
class TestAuthServiceUserAuthentication:
    """Test user authentication logic."""

    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_user_success(self, mock_password_handler, mock_user_repo):
        """Test successful user authentication."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = "hashed_pwd"
        mock_user.is_active = True
        
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_handler.verify.return_value = True
        
        result = AuthService.authenticate_user(db, "testuser", "password123")
        
        assert result is not None
        assert result[0] == "user"
        assert result[1] == mock_user
        mock_user_repo.get_by_username.assert_called_once_with(db, "testuser")
        mock_password_handler.verify.assert_called_once_with("password123", "hashed_pwd")

    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_user_wrong_password(self, mock_password_handler, mock_user_repo):
        """Test authentication fails with wrong password."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.hashed_password = "hashed_pwd"
        
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_handler.verify.return_value = False
        
        result = AuthService.authenticate_user(db, "testuser", "wrongpassword")
        
        assert result is None

    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_user_inactive(self, mock_password_handler, mock_user_repo):
        """Test authentication fails for inactive user."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = "hashed_pwd"
        mock_user.is_active = False
        
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_handler.verify.return_value = True
        
        result = AuthService.authenticate_user(db, "testuser", "password123")
        
        assert result is None


@pytest.mark.unit
class TestAuthServiceCoachAuthentication:
    """Test coach authentication logic."""

    @patch('src.services.auth_service.CoachRepository')
    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_coach_success(self, mock_password_handler, mock_user_repo, mock_coach_repo):
        """Test successful coach authentication when user not found."""
        db = Mock()
        mock_coach = Mock(spec=Coach)
        mock_coach.username = "coachuser"
        mock_coach.password = "hashed_pwd"
        mock_coach.is_active = True
        
        mock_user_repo.get_by_username.return_value = None  # User not found
        mock_coach_repo.get_by_username.return_value = mock_coach
        mock_password_handler.verify.return_value = True
        
        result = AuthService.authenticate_user(db, "coachuser", "password123")
        
        assert result is not None
        assert result[0] == "coach"
        assert result[1] == mock_coach

    @patch('src.services.auth_service.CoachRepository')
    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_coach_wrong_password(self, mock_password_handler, mock_user_repo, mock_coach_repo):
        """Test coach authentication fails with wrong password."""
        db = Mock()
        mock_coach = Mock(spec=Coach)
        mock_coach.password = "hashed_pwd"
        
        mock_user_repo.get_by_username.return_value = None
        mock_coach_repo.get_by_username.return_value = mock_coach
        mock_password_handler.verify.return_value = False
        
        result = AuthService.authenticate_user(db, "coachuser", "wrongpassword")
        
        assert result is None

    @patch('src.services.auth_service.CoachRepository')
    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_coach_inactive(self, mock_password_handler, mock_user_repo, mock_coach_repo):
        """Test authentication fails for inactive coach."""
        db = Mock()
        mock_coach = Mock(spec=Coach)
        mock_coach.password = "hashed_pwd"
        mock_coach.is_active = False
        
        mock_user_repo.get_by_username.return_value = None
        mock_coach_repo.get_by_username.return_value = mock_coach
        mock_password_handler.verify.return_value = True
        
        result = AuthService.authenticate_user(db, "coachuser", "password123")
        
        assert result is None

    @patch('src.services.auth_service.CoachRepository')
    @patch('src.services.auth_service.UserRepository')
    def test_authenticate_neither_user_nor_coach(self, mock_user_repo, mock_coach_repo):
        """Test authentication fails when neither user nor coach found."""
        db = Mock()
        
        mock_user_repo.get_by_username.return_value = None
        mock_coach_repo.get_by_username.return_value = None
        
        result = AuthService.authenticate_user(db, "nonexistent", "password")
        
        assert result is None


@pytest.mark.unit
class TestAuthServiceTokenCreation:
    """Test token creation logic."""

    def test_build_access_token_payload_user(self):
        """Test building access token payload for user."""
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.id = 1
        mock_user.role = UserRole.ADMIN
        
        payload = AuthService._build_access_token_payload("user", mock_user)
        
        assert payload["sub"] == "testuser"
        assert payload["subject_type"] == "user"
        assert payload["user_id"] == 1
        assert payload["role"] == "admin"

    def test_build_access_token_payload_coach(self):
        """Test building access token payload for coach."""
        mock_coach = Mock(spec=Coach)
        mock_coach.username = "coachuser"
        mock_coach.id = 5
        
        payload = AuthService._build_access_token_payload("coach", mock_coach)
        
        assert payload["sub"] == "coachuser"
        assert payload["subject_type"] == "coach"
        assert payload["coach_id"] == 5
        assert "role" not in payload

    @patch('src.services.auth_service.TokenHandler')
    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_create_tokens_for_user(self, mock_refresh_repo, mock_token_handler):
        """Test creating tokens for user."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.id = 1
        mock_user.role = UserRole.ADMIN
        
        mock_token_handler.create_access_token.return_value = "access_token_123"
        mock_refresh_token = Mock()
        mock_refresh_token.token = "refresh_token_456"
        mock_refresh_repo.create.return_value = mock_refresh_token
        
        access_token, refresh_token = AuthService.create_tokens(db, "user", mock_user)
        
        assert access_token == "access_token_123"
        assert refresh_token == "refresh_token_456"
        mock_refresh_repo.create.assert_called_once_with(db, user_id=1)

    @patch('src.services.auth_service.TokenHandler')
    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_create_tokens_for_coach(self, mock_refresh_repo, mock_token_handler):
        """Test creating tokens for coach."""
        db = Mock()
        mock_coach = Mock(spec=Coach)
        mock_coach.username = "coachuser"
        mock_coach.id = 5
        
        mock_token_handler.create_access_token.return_value = "access_token_789"
        mock_refresh_token = Mock()
        mock_refresh_token.token = "refresh_token_012"
        mock_refresh_repo.create.return_value = mock_refresh_token
        
        access_token, refresh_token = AuthService.create_tokens(db, "coach", mock_coach)
        
        assert access_token == "access_token_789"
        assert refresh_token == "refresh_token_012"
        mock_refresh_repo.create.assert_called_once_with(db, coach_id=5)


@pytest.mark.unit
class TestAuthServiceTokenRefresh:
    """Test token refresh logic."""

    @patch('src.services.auth_service.RefreshTokenRepository')
    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.AuthService.create_tokens')
    def test_refresh_tokens_user_success(self, mock_create_tokens, mock_user_repo, mock_refresh_repo):
        """Test successful token refresh for user."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = False
        mock_token_obj.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_token_obj.user_id = 1
        mock_token_obj.coach_id = None
        
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.is_active = True
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        mock_user_repo.get_by_id.return_value = mock_user
        mock_create_tokens.return_value = ("new_access", "new_refresh")
        
        access, refresh = AuthService.refresh_tokens(db, "old_refresh_token")
        
        assert access == "new_access"
        assert refresh == "new_refresh"
        mock_refresh_repo.revoke.assert_called_once_with(db, "old_refresh_token")

    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_refresh_tokens_invalid_token(self, mock_refresh_repo):
        """Test refresh fails with invalid token."""
        db = Mock()
        mock_refresh_repo.get_by_token.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in str(exc_info.value.detail)

    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_refresh_tokens_revoked_token(self, mock_refresh_repo):
        """Test refresh fails with revoked token."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = True
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "revoked_token")
        
        assert exc_info.value.status_code == 401

    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_refresh_tokens_expired_token(self, mock_refresh_repo):
        """Test refresh fails with expired token."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = False
        mock_token_obj.expires_at = datetime.utcnow() - timedelta(days=1)
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "expired_token")
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()

    @patch('src.services.auth_service.RefreshTokenRepository')
    @patch('src.services.auth_service.UserRepository')
    def test_refresh_tokens_inactive_user(self, mock_user_repo, mock_refresh_repo):
        """Test refresh fails for inactive user."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = False
        mock_token_obj.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_token_obj.user_id = 1
        mock_token_obj.coach_id = None
        
        mock_user = Mock(spec=User)
        mock_user.is_active = False
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        mock_user_repo.get_by_id.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "token")
        
        assert exc_info.value.status_code == 401
        assert "inactive" in str(exc_info.value.detail).lower()


@pytest.mark.unit
class TestAuthServiceLogout:
    """Test logout logic."""

    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_logout_success(self, mock_refresh_repo):
        """Test successful logout."""
        db = Mock()
        mock_refresh_repo.revoke.return_value = True
        
        result = AuthService.logout(db, "refresh_token")
        
        assert result is True
        mock_refresh_repo.revoke.assert_called_once_with(db, "refresh_token")

    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_logout_token_not_found(self, mock_refresh_repo):
        """Test logout with non-existent token."""
        db = Mock()
        mock_refresh_repo.revoke.return_value = False
        
        result = AuthService.logout(db, "nonexistent_token")
        
        assert result is False


@pytest.mark.unit
class TestAuthServiceEdgeCases:
    """Test authentication edge cases and boundary conditions."""

    @patch('src.services.auth_service.CoachRepository')
    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_empty_username(self, mock_password_handler, mock_user_repo, mock_coach_repo):
        """Test authentication with empty username."""
        db = Mock()
        mock_user_repo.get_by_username.return_value = None
        mock_coach_repo.get_by_username.return_value = None
        
        result = AuthService.authenticate_user(db, "", "password")
        
        assert result is None

    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_empty_password(self, mock_password_handler, mock_user_repo):
        """Test authentication with empty password."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.hashed_password = "hashed"
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_handler.verify.return_value = False
        
        result = AuthService.authenticate_user(db, "user", "")
        
        assert result is None

    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_special_characters_username(self, mock_password_handler, mock_user_repo):
        """Test authentication with special characters in username."""
        db = Mock()
        mock_user = Mock(spec=User)
        mock_user.username = "test@user-123"
        mock_user.hashed_password = "hashed"
        mock_user.is_active = True
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_handler.verify.return_value = True
        
        result = AuthService.authenticate_user(db, "test@user-123", "password")
        
        assert result is not None
        assert result[0] == "user"

    @patch('src.services.auth_service.UserRepository')
    @patch('src.services.auth_service.PasswordHandler')
    def test_authenticate_very_long_username(self, mock_password_handler, mock_user_repo):
        """Test authentication with very long username (boundary test)."""
        db = Mock()
        long_username = "a" * 150
        mock_user = Mock(spec=User)
        mock_user.username = long_username
        mock_user.hashed_password = "hashed"
        mock_user.is_active = True
        mock_user_repo.get_by_username.return_value = mock_user
        mock_password_handler.verify.return_value = True
        
        result = AuthService.authenticate_user(db, long_username, "password")
        
        assert result is not None
        assert result[1].username == long_username

    @patch('src.services.auth_service.RefreshTokenRepository')
    @patch('src.services.auth_service.UserRepository')
    def test_refresh_tokens_user_not_found(self, mock_user_repo, mock_refresh_repo):
        """Test token refresh when user is deleted."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = False
        mock_token_obj.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_token_obj.user_id = 1
        mock_token_obj.coach_id = None
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "token")
        
        assert exc_info.value.status_code == 401
        assert "not found" in str(exc_info.value.detail).lower()

    @patch('src.services.auth_service.RefreshTokenRepository')
    @patch('src.services.auth_service.CoachRepository')
    def test_refresh_tokens_coach_deleted(self, mock_coach_repo, mock_refresh_repo):
        """Test token refresh when coach is deleted."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = False
        mock_token_obj.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_token_obj.user_id = None
        mock_token_obj.coach_id = 1
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        mock_coach_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "token")
        
        assert exc_info.value.status_code == 401

    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_refresh_tokens_no_subject(self, mock_refresh_repo):
        """Test token refresh with no user_id or coach_id (edge case)."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = False
        mock_token_obj.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_token_obj.user_id = None
        mock_token_obj.coach_id = None
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid refresh token subject" in str(exc_info.value.detail)

    @patch('src.services.auth_service.RefreshTokenRepository')
    def test_refresh_tokens_just_expired(self, mock_refresh_repo):
        """Test token refresh just after expiration (boundary test)."""
        db = Mock()
        mock_token_obj = Mock()
        mock_token_obj.is_revoked = False
        # Set to 1 second in the past to avoid exact timing issues
        mock_token_obj.expires_at = datetime.utcnow() - timedelta(seconds=1)
        
        mock_refresh_repo.get_by_token.return_value = mock_token_obj
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_tokens(db, "token")
        
        assert exc_info.value.status_code == 401

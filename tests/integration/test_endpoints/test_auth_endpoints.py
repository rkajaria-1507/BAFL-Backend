"""
Full Integration Tests for Authentication Endpoints
Tests the complete authentication flow using API calls
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.api
class TestAuthenticationEndpoints:
    """Test suite for authentication endpoints with full API flows"""
    
    # ========================================
    # User Login Tests
    # ========================================
    
    def test_user_login_success_flow(self, client, test_db):
        """Test complete user login flow: create admin user → login → receive tokens"""
        # Step 1: Create an admin user via the auth/user-login endpoint's initial setup
        # First, we need to create an admin user directly (this simulates initial setup)
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        admin_user = User(
            username="testadmin",
            password=PasswordHandler.hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        test_db.add(admin_user)
        test_db.commit()
        test_db.refresh(admin_user)
        
        # Step 2: Login with the admin user
        login_data = {
            "username": "testadmin",
            "password": "admin123"
        }
        response = client.post("/api/v1/auth/user-login", data=login_data)
        
        # Step 3: Verify login response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["role"] == "ADMIN"
        
        # Step 4: Use access token to access protected endpoint
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_response = client.get("/api/v1/users/me", headers=headers)
        
        assert me_response.status_code == status.HTTP_200_OK
        me_data = me_response.json()
        assert me_data["username"] == "testadmin"
        assert me_data["role"] == "ADMIN"
    
    def test_user_login_invalid_credentials(self, client, test_db):
        """Test user login with invalid credentials returns 401"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            username="testuser",
            password=PasswordHandler.hash("correct_password"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Try login with wrong password
        login_data = {
            "username": "testuser",
            "password": "wrong_password"
        }
        response = client.post("/api/v1/auth/user-login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_login_inactive_user(self, client, test_db):
        """Test login with inactive user is rejected"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            username="inactiveuser",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=False
        )
        test_db.add(user)
        test_db.commit()
        
        login_data = {
            "username": "inactiveuser",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/user-login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_login_nonexistent_user(self, client):
        """Test login with nonexistent user returns 401"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/user-login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================
    # Coach Login Tests
    # ========================================
    
    def test_coach_login_success_flow(self, client, test_db):
        """Test complete coach login flow: create coach → login → receive tokens"""
        from src.db.models.coach import Coach
        from src.core.security import PasswordHandler
        
        # Create a coach
        coach = Coach(
            name="Test Coach",
            username="testcoach",
            password=PasswordHandler.hash("coach123"),
            is_active=True
        )
        test_db.add(coach)
        test_db.commit()
        test_db.refresh(coach)
        
        # Login as coach
        login_data = {
            "username": "testcoach",
            "password": "coach123"
        }
        response = client.post("/api/v1/auth/coach-login", data=login_data)
        
        # Verify login response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["coach"]["username"] == "testcoach"
        assert data["coach"]["name"] == "Test Coach"
    
    def test_coach_login_invalid_credentials(self, client, test_db):
        """Test coach login with invalid credentials returns 401"""
        from src.db.models.coach import Coach
        from src.core.security import PasswordHandler
        
        coach = Coach(
            name="Test Coach",
            username="testcoach",
            password=PasswordHandler.hash("correct_password"),
            is_active=True
        )
        test_db.add(coach)
        test_db.commit()
        
        login_data = {
            "username": "testcoach",
            "password": "wrong_password"
        }
        response = client.post("/api/v1/auth/coach-login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_coach_login_inactive_coach(self, client, test_db):
        """Test login with inactive coach is rejected"""
        from src.db.models.coach import Coach
        from src.core.security import PasswordHandler
        
        coach = Coach(
            name="Inactive Coach",
            username="inactivecoach",
            password=PasswordHandler.hash("password123"),
            is_active=False
        )
        test_db.add(coach)
        test_db.commit()
        
        login_data = {
            "username": "inactivecoach",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/coach-login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================
    # Token Refresh Tests
    # ========================================
    
    def test_refresh_token_flow(self, client, test_db):
        """Test complete token refresh flow: login → use refresh token → get new access token"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        # Create user
        user = User(
            username="refreshuser",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Login to get tokens
        login_data = {
            "username": "refreshuser",
            "password": "password123"
        }
        login_response = client.post("/api/v1/auth/user-login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]  # Should be different
    
    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid token returns 401"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================
    # Logout Tests
    # ========================================
    
    def test_logout_flow(self, client, test_db):
        """Test complete logout flow: login → logout → verify token invalidation"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        # Create user
        user = User(
            username="logoutuser",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Login
        login_data = {
            "username": "logoutuser",
            "password": "password123"
        }
        login_response = client.post("/api/v1/auth/user-login", data=login_data)
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Verify token works before logout
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        
        # Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.json()["message"] == "Successfully logged out"
    
    def test_logout_without_token(self, client):
        """Test logout without authentication token returns 401"""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================
    # Cross-Entity Login Tests
    # ========================================
    
    def test_user_cannot_login_as_coach(self, client, test_db):
        """Test that user credentials cannot be used in coach login endpoint"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            username="onlyuser",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Try to login as coach with user credentials
        login_data = {
            "username": "onlyuser",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/coach-login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_coach_cannot_login_as_user(self, client, test_db):
        """Test that coach credentials cannot be used in user login endpoint (if they don't have user entry)"""
        from src.db.models.coach import Coach
        from src.core.security import PasswordHandler
        
        # Create coach without corresponding user entry
        coach = Coach(
            name="Only Coach",
            username="onlycoach",
            password=PasswordHandler.hash("password123"),
            is_active=True
        )
        test_db.add(coach)
        test_db.commit()
        
        # Try to login as user with coach credentials
        login_data = {
            "username": "onlycoach",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/user-login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================
    # Token Usage in Protected Endpoints
    # ========================================
    
    def test_access_protected_endpoint_without_token(self, client):
        """Test that protected endpoints reject requests without token"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_with_invalid_token(self, client):
        """Test that protected endpoints reject requests with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_with_malformed_header(self, client):
        """Test that protected endpoints reject requests with malformed auth header"""
        headers = {"Authorization": "InvalidFormat token123"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

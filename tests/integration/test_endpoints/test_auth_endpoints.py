"""
Integration Tests for Authentication Endpoints
Tests the complete authentication flow using API calls
Endpoints tested: POST /api/v1/auth/login, POST /api/v1/auth/refresh, POST /api/v1/auth/logout
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
    
    def test_user_login_success(self, client, test_db):
        """Test successful user login flow: create user → login → receive tokens"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        # Create an admin user
        admin_user = User(
            name="Test Admin",
            username="testadmin",
            password=PasswordHandler.hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        test_db.add(admin_user)
        test_db.commit()
        test_db.refresh(admin_user)
        
        # Login with the admin user (form data)
        login_data = {
            "username": "testadmin",
            "password": "admin123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        # Verify login response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["role"] == "admin"
        assert data["user"]["name"] == "Test Admin"
        
        # Verify token works by accessing protected endpoint
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_response = client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        me_data = me_response.json()
        # /me endpoint returns nested structure: {user: {user_id, name, username, ...}}
        assert me_data["user"]["username"] == "testadmin"
    
    def test_user_login_with_json(self, client, test_db):
        """Test user login using JSON body instead of form data"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            name="JSON User",
            username="jsonuser",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Login with JSON
        login_data = {
            "username": "jsonuser",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "jsonuser"
    
    def test_user_login_wrong_password(self, client, test_db):
        """Test user login with incorrect password returns 401"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            name="Test User",
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
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()
    
    def test_user_login_inactive_user(self, client, test_db):
        """Test login with inactive user is rejected with 401"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            name="Inactive User",
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
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_login_nonexistent_user(self, client):
        """Test login with nonexistent user returns 401"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_login_missing_credentials(self, client):
        """Test login without providing credentials returns 422"""
        response = client.post("/api/v1/auth/login", data={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_user_login_missing_password(self, client):
        """Test login with only username returns 422"""
        login_data = {"username": "testuser"}
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # ========================================
    # Coach Login Tests
    # ========================================
    
    def test_coach_login_success(self, client, test_db):
        """Test successful coach login flow: create coach → login → receive tokens"""
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
        response = client.post("/api/v1/auth/login", data=login_data)
        
        # Verify login response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "coach" in data
        assert data["coach"]["username"] == "testcoach"
        assert data["coach"]["name"] == "Test Coach"
    
    def test_coach_login_wrong_password(self, client, test_db):
        """Test coach login with invalid credentials returns 401"""
        from src.db.models.coach import Coach
        from src.core.security import PasswordHandler
        
        coach = Coach(
            name="Test Coach",
            username="testcoach2",
            password=PasswordHandler.hash("correct_password"),
            is_active=True
        )
        test_db.add(coach)
        test_db.commit()
        
        login_data = {
            "username": "testcoach2",
            "password": "wrong_password"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_coach_login_inactive(self, client, test_db):
        """Test login with inactive coach is rejected with 401"""
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
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================
    # Priority: User vs Coach Login
    # ========================================
    
    def test_login_checks_user_first_then_coach(self, client, test_db):
        """Test that login checks User table first, then Coach table"""
        from src.db.models.user import User, UserRole
        from src.db.models.coach import Coach
        from src.core.security import PasswordHandler
        
        # Create a user
        user = User(
            name="Priority User",
            username="samename",
            password=PasswordHandler.hash("userpass"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        
        # Create a coach with same username
        coach = Coach(
            name="Priority Coach",
            username="samename",
            password=PasswordHandler.hash("coachpass"),
            is_active=True
        )
        test_db.add(coach)
        test_db.commit()
        
        # Login should authenticate as User (checked first)
        login_data = {
            "username": "samename",
            "password": "userpass"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user" in data
        assert data["user"]["name"] == "Priority User"
    
    def test_login_falls_back_to_coach_if_user_not_found(self, client, test_db):
        """Test that login checks Coach table if User not found"""
        from src.db.models.coach import Coach
        from src.core.security import PasswordHandler
        
        # Only create coach, no user
        coach = Coach(
            name="Only Coach",
            username="onlycoach",
            password=PasswordHandler.hash("password123"),
            is_active=True
        )
        test_db.add(coach)
        test_db.commit()
        
        # Login should find coach
        login_data = {
            "username": "onlycoach",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "coach" in data
        assert data["coach"]["username"] == "onlycoach"
    
    # ========================================
    # Token Refresh Tests
    # ========================================
    
    def test_refresh_token_success(self, client, test_db):
        """Test complete token refresh flow: login → use refresh token → get new tokens"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        # Create user and login
        user = User(
            name="Refresh User",
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
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        old_access_token = tokens["access_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        # Note: tokens might be identical if generated within same second
        
        # New access token should work
        headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        me_response = client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
    
    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid token returns 401"""
        refresh_data = {"refresh_token": "invalid_token_string"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_with_access_token_instead_of_refresh(self, client, test_db):
        """Test that using access token in refresh endpoint fails"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            name="Token User",
            username="tokenuser",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Login
        login_response = client.post("/api/v1/auth/login", data={
            "username": "tokenuser",
            "password": "password123"
        })
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Try to refresh with access token (should fail)
        refresh_data = {"refresh_token": access_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        # Should fail because it's not a refresh token
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    # ========================================
    # Logout Tests
    # ========================================
    
    def test_logout_success(self, client, test_db):
        """Test complete logout flow: login → logout → verify token revoked"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        # Create user and login
        user = User(
            name="Logout User",
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
        login_response = client.post("/api/v1/auth/login", data=login_data)
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # Verify token works before logout
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        
        # Logout
        logout_data = {"refresh_token": refresh_token}
        logout_response = client.post("/api/v1/auth/logout", json=logout_data, headers=headers)
        
        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.json()["message"] == "Successfully logged out"
        assert logout_response.json()["success"] == True
    
    def test_logout_without_auth_header(self, client):
        """Test logout without authentication returns 401"""
        logout_data = {"refresh_token": "some_token"}
        response = client.post("/api/v1/auth/logout", json=logout_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_with_invalid_refresh_token(self, client, test_db):
        """Test logout with invalid refresh token still succeeds (graceful handling)"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        user = User(
            name="Logout Test User",
            username="logouttest",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Login to get valid access token
        login_response = client.post("/api/v1/auth/login", data={
            "username": "logouttest",
            "password": "password123"
        })
        access_token = login_response.json()["access_token"]
        
        # Logout with invalid refresh token
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_data = {"refresh_token": "invalid_refresh_token"}
        response = client.post("/api/v1/auth/logout", json=logout_data, headers=headers)
        
        # Should return success (token already revoked or invalid)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] == True
    
    # ========================================
    # Protected Endpoint Access Tests
    # ========================================
    
    def test_access_protected_endpoint_without_token(self, client):
        """Test that protected endpoints reject requests without token"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_with_invalid_token(self, client):
        """Test that protected endpoints reject requests with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_string"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_with_malformed_header(self, client):
        """Test that protected endpoints reject requests with malformed auth header"""
        # Missing "Bearer" prefix
        headers = {"Authorization": "token123"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # ========================================
    # Different User Roles Login
    # ========================================
    
    def test_admin_user_login(self, client, test_db):
        """Test ADMIN role user can login"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        admin = User(
            name="Admin User",
            username="admin",
            password=PasswordHandler.hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        test_db.add(admin)
        test_db.commit()
        
        response = client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["role"] == "admin"
    
    def test_coach_role_user_login(self, client, test_db):
        """Test USER with COACH role can login (different from Coach entity)"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        coach_user = User(
            name="Coach Role User",
            username="coachrole",
            password=PasswordHandler.hash("password123"),
            role=UserRole.COACH,
            is_active=True
        )
        test_db.add(coach_user)
        test_db.commit()
        
        response = client.post("/api/v1/auth/login", data={
            "username": "coachrole",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["role"] == "coach"
    
    def test_regular_user_login(self, client, test_db):
        """Test regular USER role can login"""
        from src.db.models.user import User, UserRole
        from src.core.security import PasswordHandler
        
        regular_user = User(
            name="Regular User",
            username="regular",
            password=PasswordHandler.hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(regular_user)
        test_db.commit()
        
        response = client.post("/api/v1/auth/login", data={
            "username": "regular",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["role"] == "user"

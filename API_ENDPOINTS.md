# BAFL Backend API - Complete Endpoint Documentation

This document provides a comprehensive list of all API endpoints available in the BAFL Backend system.

## Base URL

- **Development**: `http://localhost:4256`
- **API Version**: All endpoints are prefixed with `/api/v1`

## Table of Contents

- [Root Endpoints](#root-endpoints)
- [Authentication](#authentication)
- [User Management](#user-management)
- [Permission Management](#permission-management)
- [Coach Management](#coach-management)
- [Student Management](#student-management)
- [School Management](#school-management)
- [Batch Management](#batch-management)
- [Physical Assessments](#physical-assessments)
- [Archery Practice](#archery-practice)
- [Archery Tournaments](#archery-tournaments)

---

## Root Endpoints

### GET `/`
**Description**: Root endpoint with API information  
**Authentication**: Not required  
**Response**:
```json
{
  "message": "Welcome to BAFL Backend API",
  "version": "1.0.0",
  "environment": "development",
  "docs": "/docs",
  "health": "/health"
}
```

### GET `/health`
**Description**: Health check endpoint  
**Authentication**: Not required  
**Response**:
```json
{
  "status": "healthy",
  "app_name": "BAFL Backend API",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Authentication

Base path: `/api/v1/auth`

### POST `/api/v1/auth/login`
**Description**: Login and get access & refresh tokens  
**Authentication**: Not required  
**Content-Type**: `application/json` or `application/x-www-form-urlencoded`  
**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```
**Response**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "user_id": 1,
    "name": "string",
    "username": "string",
    "role": "admin|user|coach"
  }
}
```

### POST `/api/v1/auth/refresh`
**Description**: Refresh access token using refresh token  
**Authentication**: Not required  
**Request Body**:
```json
{
  "refresh_token": "string"
}
```
**Response**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

### POST `/api/v1/auth/logout`
**Description**: Logout user by revoking refresh token  
**Authentication**: Required  
**Request Body**:
```json
{
  "refresh_token": "string"
}
```
**Response**:
```json
{
  "message": "Successfully logged out",
  "success": true
}
```

---

## User Management

Base path: `/api/v1/users`

### POST `/api/v1/users/`
**Description**: Create a new user  
**Authentication**: Required  
**Permission**: Role-based (Admin can create any role, requires specific permissions)  
**Request Body**:
```json
{
  "name": "string",
  "username": "string",
  "password": "string",
  "role": "admin|user|coach"
}
```
**Response**: `201 Created`
```json
{
  "id": 1,
  "name": "string",
  "username": "string",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "permissions": ["create_user", "view_all_users"]
}
```

### GET `/api/v1/users/`
**Description**: List all users (with pagination)  
**Authentication**: Required  
**Permission**: `view_all_users` (Admin only)  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK`
```json
{
  "users": [
    {
      "id": 1,
      "name": "string",
      "username": "string",
      "role": "admin",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "permissions": []
    }
  ],
  "total": 1
}
```

### GET `/api/v1/users/me`
**Description**: Get current authenticated user or coach profile  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "user": {
    "user_id": 1,
    "name": "string",
    "username": "string",
    "role": "admin",
    "permissions": [
      {
        "permission_id": 1,
        "permission_name": "create_user"
      }
    ]
  }
}
```

### GET `/api/v1/users/{user_id}`
**Description**: Get specific user by ID  
**Authentication**: Required  
**Permission**: Admin can view all; users/coaches can only view their own profile  
**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "string",
  "username": "string",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "permissions": []
}
```

### PUT `/api/v1/users/{user_id}`
**Description**: Update user information  
**Authentication**: Required  
**Permission**: Admin can edit all; users/coaches can only edit their own profile  
**Request Body**:
```json
{
  "name": "string (optional)",
  "username": "string (optional)",
  "password": "string (optional)",
  "is_active": "boolean (optional)"
}
```
**Response**: `200 OK` (UserResponse)

### DELETE `/api/v1/users/{user_id}`
**Description**: Delete a user  
**Authentication**: Required  
**Permission**: Requires appropriate delete permission for the target user's role  
**Response**: `200 OK`
```json
{
  "message": "User deleted successfully",
  "success": true
}
```

---

## Permission Management

Base path: `/api/v1/permissions`

### GET `/api/v1/permissions/`
**Description**: List all available permissions in the system  
**Authentication**: Required  
**Permission**: `view_permissions`  
**Response**: `200 OK`
```json
{
  "permissions": [
    {
      "permission_id": 1,
      "permission_name": "create_user"
    }
  ]
}
```

### POST `/api/v1/permissions/assign`
**Description**: Assign a permission to a user or coach  
**Authentication**: Required  
**Permission**: `assign_permissions`  
**Request Body**:
```json
{
  "permission_id": 1,
  "user_id": 2,
  "coach_id": null,
  "assigned_by": 1
}
```
**Response**: `200 OK`
```json
{
  "message": "Permission assigned."
}
```

### DELETE `/api/v1/permissions/revoke`
**Description**: Revoke a permission from a user or coach  
**Authentication**: Required  
**Permission**: `revoke_permissions`  
**Request Body**:
```json
{
  "permission_id": 1,
  "user_id": 2,
  "coach_id": null
}
```
**Response**: `200 OK`
```json
{
  "message": "Permission revoked."
}
```

---

## Coach Management

Base path: `/api/v1/coaches`

### POST `/api/v1/coaches/`
**Description**: Create a new coach  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "name": "string",
  "username": "string",
  "password": "string",
  "phone_number": "string (optional)",
  "email": "string (optional)",
  "address": "string (optional)",
  "contract_start_date": "date",
  "contract_end_date": "date",
  "hourly_rate": "number",
  "school_ids": [1, 2],
  "batch_ids": [1, 2]
}
```
**Response**: `201 Created`
```json
{
  "message": "Coach created successfully",
  "coach": {
    "coach_id": 1,
    "name": "string",
    "username": "string"
  }
}
```

### GET `/api/v1/coaches/pre-create`
**Description**: Get pre-create data (available schools and batches)  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`

### GET `/api/v1/coaches/`
**Description**: List all coaches  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK` (Array of coach details)

### GET `/api/v1/coaches/{coach_id}`
**Description**: Get specific coach by ID  
**Authentication**: Required  
**Response**: `200 OK`

### PUT `/api/v1/coaches/{coach_id}`
**Description**: Update coach information  
**Authentication**: Required (Admin only)  
**Request Body**: Similar to create but all fields optional  
**Response**: `200 OK`

### DELETE `/api/v1/coaches/{coach_id}`
**Description**: Delete a coach  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content`

---

## Student Management

Base path: `/api/v1/students`

### POST `/api/v1/students/`
**Description**: Create a new student  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "name": "string",
  "date_of_birth": "date",
  "gender": "male|female|other",
  "batch_id": 1,
  "school_id": 1,
  "phone_number": "string (optional)",
  "emergency_contact": "string (optional)"
}
```
**Response**: `201 Created`

### GET `/api/v1/students/pre-create`
**Description**: Get pre-create data (available schools and batches)  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`

### GET `/api/v1/students/`
**Description**: List all students  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK` (Array of student details)

### GET `/api/v1/students/{student_id}`
**Description**: Get specific student by ID  
**Authentication**: Required  
**Response**: `200 OK`

### PUT `/api/v1/students/{student_id}`
**Description**: Update student information  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`

### DELETE `/api/v1/students/{student_id}`
**Description**: Delete a student  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content`

---

## School Management

Base path: `/api/v1/schools`

### POST `/api/v1/schools/`
**Description**: Create a new school  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "name": "string",
  "address": "string (optional)",
  "contact_number": "string (optional)",
  "email": "string (optional)"
}
```
**Response**: `201 Created`

### GET `/api/v1/schools/`
**Description**: List all schools  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK` (Array of school details)

### GET `/api/v1/schools/{school_id}`
**Description**: Get specific school by ID  
**Authentication**: Required  
**Response**: `200 OK`

### PUT `/api/v1/schools/{school_id}`
**Description**: Update school information  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`

### DELETE `/api/v1/schools/{school_id}`
**Description**: Delete a school  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content`

---

## Batch Management

Base path: `/api/v1/batches`

### POST `/api/v1/batches/`
**Description**: Create a new batch  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "batch_name": "string",
  "school_id": 1,
  "coach_id": 1,
  "start_date": "date",
  "end_date": "date (optional)"
}
```
**Response**: `201 Created`

### GET `/api/v1/batches/pre-create`
**Description**: Get pre-create data (available schools and coaches)  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`

### GET `/api/v1/batches/`
**Description**: List all batches  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK` (Array of batch details)

### GET `/api/v1/batches/{batch_id}`
**Description**: Get specific batch by ID  
**Authentication**: Required  
**Response**: `200 OK`

### PUT `/api/v1/batches/{batch_id}`
**Description**: Update batch information  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`

### DELETE `/api/v1/batches/{batch_id}`
**Description**: Delete a batch  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content`

---

## Physical Assessments

Base path: `/api/v1/physical`

### POST `/api/v1/physical/sessions`
**Description**: Create a new physical assessment session with results  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_ADD`  
**Request Body**:
```json
{
  "batch_id": 1,
  "coach_id": 1,
  "session_date": "date",
  "notes": "string (optional)",
  "results": [
    {
      "student_id": 1,
      "exercise_levels": {
        "sit_ups": 1,
        "push_ups": 2
      }
    }
  ]
}
```
**Response**: `201 Created`

### GET `/api/v1/physical/sessions/pre-create`
**Description**: Get pre-create data for physical assessment sessions  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_ADD`  
**Response**: `200 OK`

### GET `/api/v1/physical/sessions`
**Description**: Get all physical assessment sessions (admin or coach view)  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_VIEW`  
**Response**: `200 OK`

### GET `/api/v1/physical/sessions/{session_id}`
**Description**: Get specific physical assessment session by ID  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_VIEW`  
**Response**: `200 OK`

### PUT `/api/v1/physical/sessions/{session_id}`
**Description**: Update physical assessment session  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_EDIT`  
**Response**: `200 OK`

### DELETE `/api/v1/physical/sessions/{session_id}`
**Description**: Delete physical assessment session  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_EDIT`  
**Response**: `204 No Content`

### GET `/api/v1/physical/students`
**Description**: Get physical assessment student summary (admin or coach view)  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_VIEW`  
**Response**: `200 OK`

### GET `/api/v1/physical/students/{student_id}`
**Description**: Get detailed physical assessment results for a student  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_VIEW`  
**Response**: `200 OK`

### PUT `/api/v1/physical/students/{student_id}`
**Description**: Update physical assessment results for a student  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_EDIT`  
**Response**: `200 OK`

### DELETE `/api/v1/physical/students/{student_id}`
**Description**: Delete physical assessment results for a student  
**Authentication**: Required  
**Permission**: `PHYSICAL_SESSIONS_EDIT`  
**Response**: `204 No Content`

### GET `/api/v1/physical/level-mappings`
**Description**: Get exercise level mappings (with optional coach filtering)  
**Authentication**: Required  
**Response**: `200 OK`

---

## Archery Practice

Base path: `/api/v1/archery`

### POST `/api/v1/archery/sessions`
**Description**: Create a new archery practice session  
**Authentication**: Required (Admin or Coach)  
**Request Body**:
```json
{
  "batch_id": 1,
  "coach_id": 1,
  "session_date": "date",
  "distance": 10,
  "notes": "string (optional)",
  "results": [
    {
      "student_id": 1,
      "score": 85,
      "arrows_shot": 30
    }
  ]
}
```
**Response**: `201 Created`

### GET `/api/v1/archery/sessions/pre-create`
**Description**: Get pre-create data for archery sessions  
**Authentication**: Required (Admin or Coach)  
**Response**: `200 OK`

### GET `/api/v1/archery/sessions`
**Description**: Get all archery practice sessions (admin or coach view)  
**Authentication**: Required  
**Response**: `200 OK`

### GET `/api/v1/archery/sessions/{session_id}`
**Description**: Get specific archery practice session by ID  
**Authentication**: Required  
**Response**: `200 OK`

### PUT `/api/v1/archery/sessions/{session_id}`
**Description**: Update archery practice session  
**Authentication**: Required (Admin or Coach)  
**Response**: `200 OK`

### DELETE `/api/v1/archery/sessions/{session_id}`
**Description**: Delete archery practice session  
**Authentication**: Required (Admin or Coach)  
**Response**: `204 No Content`

### GET `/api/v1/archery/students`
**Description**: Get archery student summary (admin or coach view)  
**Authentication**: Required  
**Response**: `200 OK`

### GET `/api/v1/archery/students/{student_id}`
**Description**: Get detailed archery results for a student  
**Authentication**: Required  
**Response**: `200 OK`

### PUT `/api/v1/archery/students/{student_id}`
**Description**: Update archery results for a student  
**Authentication**: Required (Admin or Coach)  
**Response**: `200 OK`

### DELETE `/api/v1/archery/students/{student_id}`
**Description**: Delete archery results for a student  
**Authentication**: Required (Admin or Coach)  
**Response**: `204 No Content`

---

## Archery Tournaments

Base path: `/api/v1/archery/tournaments`

### POST `/api/v1/archery/tournaments/categories`
**Description**: Create a new archery tournament category  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "category_name": "string",
  "description": "string (optional)"
}
```
**Response**: `201 Created`

### DELETE `/api/v1/archery/tournaments/categories/{category_id}`
**Description**: Delete an archery tournament category  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content`

### GET `/api/v1/archery/tournaments/sessions/pre-create`
**Description**: Get pre-create data for tournament sessions  
**Authentication**: Required (Admin or Coach)  
**Response**: `200 OK`

### POST `/api/v1/archery/tournaments/sessions`
**Description**: Create a new archery tournament session  
**Authentication**: Required (Admin or Coach)  
**Request Body**:
```json
{
  "batch_id": 1,
  "coach_id": 1,
  "session_date": "date",
  "tournament_name": "string",
  "category_id": 1,
  "distance": 18,
  "notes": "string (optional)",
  "results": [
    {
      "student_id": 1,
      "score": 290,
      "arrows_shot": 60,
      "rank": 1
    }
  ]
}
```
**Response**: `201 Created`

### GET `/api/v1/archery/tournaments/sessions`
**Description**: Get all archery tournament sessions (admin or coach view)  
**Authentication**: Required  
**Response**: `200 OK`

### GET `/api/v1/archery/tournaments/sessions/{session_id}`
**Description**: Get specific archery tournament session by ID  
**Authentication**: Required  
**Response**: `200 OK`

### PUT `/api/v1/archery/tournaments/sessions/{session_id}`
**Description**: Update archery tournament session  
**Authentication**: Required (Admin or Coach)  
**Response**: `200 OK`

### DELETE `/api/v1/archery/tournaments/sessions/{session_id}`
**Description**: Delete archery tournament session  
**Authentication**: Required (Admin or Coach)  
**Response**: `204 No Content`

---

## Authentication & Authorization

### JWT Tokens

The API uses JWT (JSON Web Tokens) for authentication:

- **Access Token**: Valid for 24 hours (default), used for API requests
- **Refresh Token**: Valid for 7 days (default), used to obtain new access tokens

### Using Tokens

Include the access token in the Authorization header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Roles

- **Admin**: Full system access
- **User**: Limited access (own profile only)
- **Coach**: Access to assigned batches and students

### Permissions

Granular permissions can be assigned to users beyond their role defaults. Common permissions include:

- `create_user`, `create_coach`, `create_admin`
- `delete_user`, `delete_coach`, `delete_admin`
- `view_all_users`, `edit_all_users`
- `assign_permissions`, `revoke_permissions`, `view_permissions`
- `view_own_profile`, `edit_own_profile`
- `PHYSICAL_SESSIONS_VIEW`, `PHYSICAL_SESSIONS_ADD`, `PHYSICAL_SESSIONS_EDIT`

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid JSON body."
}
```

### 401 Unauthorized
```json
{
  "detail": "Incorrect username or password"
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Interactive Documentation

For interactive API documentation and testing:

- **Swagger UI**: `http://localhost:4256/docs`
- **ReDoc**: `http://localhost:4256/redoc`
- **OpenAPI Schema**: `http://localhost:4256/openapi.json`

---

## Rate Limiting

Currently, there are no rate limits enforced. This may change in production environments.

---

## Content Types

Most endpoints support both:
- `application/json`
- `application/x-www-form-urlencoded` (for form submissions)
- `multipart/form-data` (for file uploads, where applicable)

---

## Pagination

List endpoints support pagination through query parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

---

*Last Updated: December 2024*

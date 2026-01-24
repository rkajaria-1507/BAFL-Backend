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
- [Attendance](#attendance)

---

## Root Endpoints

### GET `/`
**Description**: Root endpoint with API information  
**Authentication**: Not required  
**Response**:
```json
{
  "message": "Welcome to <APP_NAME>",
  "version": "<APP_VERSION>",
  "environment": "<development|staging|production>",
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
  "app_name": "<APP_NAME>",
  "version": "<APP_VERSION>",
  "environment": "<development|staging|production>"
}
```

---

## Authentication

Base path: `/api/v1/auth`

### POST `/api/v1/auth/login`
**Description**: Login and get access & refresh tokens  
**Authentication**: Not required  
**Content-Type**: `application/json`, `application/x-www-form-urlencoded`, or `multipart/form-data`  
**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```
**Response** (discriminated by `user_type`):

User response:
```json
{
  "user_type": "user",
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "name": "string",
    "username": "string",
    "role": "admin|user|coach"
  }
}
```

Coach response:
```json
{
  "user_type": "coach",
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "coach": {
    "coach_id": 1,
    "name": "string",
    "username": "string"
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
  "success": true,
  "data": null
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
Notes:
- Provide **exactly one** of `user_id` or `coach_id`.

**Response**: `200 OK` (MessageResponse)
```json
{
  "message": "Permission assigned.",
  "success": true,
  "data": null
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
Notes:
- Provide **exactly one** of `user_id` or `coach_id`.

**Response**: `200 OK` (MessageResponse)
```json
{
  "message": "Permission revoked.",
  "success": true,
  "data": null
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
  "schools": [1, 2],
  "batches": [1, 2]
}
```
**Response**: `201 Created`
```json
{
  "message": "Coach created successfully",
  "coach": {
    "coach_id": 1,
    "name": "string",
    "schools": [
      { "school_id": 1, "school_name": "string" }
    ],
    "batches": [
      { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" }
    ]
  }
}
```

### GET `/api/v1/coaches/pre-create`
**Description**: Get pre-create data (available schools and batches)  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`
```json
{
  "schools": [{ "school_id": 1, "school_name": "string" }],
  "batches": [{ "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" }]
}
```

### GET `/api/v1/coaches/`
**Description**: List all coaches  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK`
```json
[
  {
    "coach_id": 1,
    "name": "string",
    "schools": [
      { "school_id": 1, "school_name": "string" }
    ],
    "batches": [
      { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" }
    ]
  }
]
```

### GET `/api/v1/coaches/{coach_id}`
**Description**: Get specific coach by ID  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "coach_id": 1,
  "name": "string",
  "schools": [
    { "school_id": 1, "school_name": "string" }
  ],
  "batches": [
    { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" }
  ]
}
```

### PUT `/api/v1/coaches/{coach_id}`
**Description**: Update coach information  
**Authentication**: Required (Admin only)  
**Request Body** (all fields optional):
```json
{
  "name": "string",
  "password": "string",
  "schools": [1, 2],
  "batches": [1, 2]
}
```
**Response**: `200 OK`
```json
{
  "message": "Coach updated successfully",
  "coach": {
    "coach_id": 1,
    "name": "string",
    "schools": [
      { "school_id": 1, "school_name": "string" }
    ],
    "batches": [
      { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" }
    ]
  }
}
```

### DELETE `/api/v1/coaches/{coach_id}`
**Description**: Delete a coach  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content` (empty body)

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
  "age": 12,
  "school_id": 1,
  "coach_id": 10,
  "batch_id": 1
}
```
**Response**: `201 Created`
```json
{
  "name": "string",
  "age": 12,
  "school_id": 1,
  "coach_id": 10,
  "batch_id": 1,
  "id": 100,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null
}
```

### GET `/api/v1/students/pre-create`
**Description**: Get pre-create data (available schools and batches)  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`
```json
{
  "schools": [{ "school_id": 1, "school_name": "string" }],
  "batches": [{ "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" }],
  "coaches": [
    {
      "coach_id": 10,
      "coach_name": "string",
      "schools": [{ "school_id": 1, "school_name": "string" }],
      "batches": [{ "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" }]
    }
  ]
}
```

### GET `/api/v1/students/`
**Description**: List all students  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK`
```json
[
  {
    "id": 100,
    "name": "string",
    "age": 12,
    "school_id": 1,
    "coach_id": 10,
    "batch_id": 1,
    "created_at": "2026-01-20T12:00:00Z",
    "updated_at": null
  }
]
```

### GET `/api/v1/students/{student_id}`
**Description**: Get specific student by ID  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "id": 100,
  "name": "string",
  "age": 12,
  "school_id": 1,
  "coach_id": 10,
  "batch_id": 1,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null
}
```

### PUT `/api/v1/students/{student_id}`
**Description**: Update student information  
**Authentication**: Required (Admin only)  
**Request Body** (all fields optional):
```json
{
  "name": "string",
  "age": 13,
  "school_id": 1,
  "coach_id": 10,
  "batch_id": 2
}
```
**Response**: `200 OK`
```json
{
  "id": 100,
  "name": "string",
  "age": 13,
  "school_id": 1,
  "coach_id": 10,
  "batch_id": 2,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": "2026-01-21T12:00:00Z"
}
```

### DELETE `/api/v1/students/{student_id}`
**Description**: Delete a student  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content` (empty body)

---

## School Management

Base path: `/api/v1/schools`

### POST `/api/v1/schools/`
**Description**: Create a new school  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "name": "string"
}
```
**Response**: `201 Created`
```json
{
  "school_id": 1,
  "school_name": "string"
}
```

### GET `/api/v1/schools/`
**Description**: List all schools  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "string",
    "created_at": "2026-01-20T12:00:00Z",
    "updated_at": null
  }
]
```

### GET `/api/v1/schools/{school_id}`
**Description**: Get specific school by ID  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "string",
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null
}
```

### PUT `/api/v1/schools/{school_id}`
**Description**: Update school information  
**Authentication**: Required (Admin only)  
**Request Body** (all fields optional):
```json
{
  "name": "string"
}
```
**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "string",
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": "2026-01-21T12:00:00Z"
}
```

### DELETE `/api/v1/schools/{school_id}`
**Description**: Delete a school  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content` (empty body)

---

## Batch Management

Base path: `/api/v1/batches`

### POST `/api/v1/batches/`
**Description**: Create a new batch  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "school_id": 1,
  "batch_name": "string",
  "schedule": [
    { "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
  ]
}
```
**Response**: `201 Created`
```json
{
  "batch_id": 1,
  "batch_name": "string",
  "school_id": 1,
  "school_name": "string",
  "schedule": [
    { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
  ]
}
```

### GET `/api/v1/batches/pre-create`
**Description**: Get pre-create data (available schools and coaches)  
**Authentication**: Required (Admin only)  
**Response**: `200 OK`
```json
{
  "schools": [
    {
      "school_id": 1,
      "school_name": "string",
      "coaches": [{ "coach_id": 10, "coach_name": "string" }]
    }
  ],
  "days_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
}
```

### GET `/api/v1/batches/`
**Description**: List all batches  
**Authentication**: Required  
**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK`
```json
[
  {
    "batch_id": 1,
    "batch_name": "string",
    "school_id": 1,
    "school_name": "string",
    "schedule": [
      { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
    ],
    "created_at": "2026-01-20T12:00:00Z",
    "updated_at": null
  }
]
```

### GET `/api/v1/batches/{batch_id}`
**Description**: Get specific batch by ID  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "batch_id": 1,
  "batch_name": "string",
  "school_id": 1,
  "school_name": "string",
  "schedule": [
    { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
  ],
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null
}
```

### PUT `/api/v1/batches/{batch_id}`
**Description**: Update batch information  
**Authentication**: Required (Admin only)  
**Request Body** (all fields optional):
```json
{
  "batch_name": "string",
  "school_id": 1,
  "schedule": [
    { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:30 PM", "end_time": "05:30 PM" },
    { "day_of_week": "Wednesday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
  ]
}
```
**Response**: `200 OK`
```json
{
  "batch_id": 1,
  "batch_name": "string",
  "school_id": 1,
  "school_name": "string",
  "schedule": [
    { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:30 PM", "end_time": "05:30 PM" },
    { "schedule_id": 2, "day_of_week": "Wednesday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
  ],
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": "2026-01-21T12:00:00Z"
}
```

### DELETE `/api/v1/batches/{batch_id}`
**Description**: Delete a batch  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content` (empty body)

---

## Physical Assessments

Base path: `/api/v1/physical`

### POST `/api/v1/physical/sessions`
**Description**: Create a new physical assessment session with results  
**Authentication**: Required  
**Required permission**: `physical_sessions_add`  
**Request Body**:
```json
{
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-20",
  "student_count": 21,
  "admin_override": false,
  "results": [
    {
      "student_id": 100,
      "discipline": "string",
      "curl_up": 0,
      "push_up": 0,
      "sit_and_reach": 0.0,
      "is_present": true
    }
  ]
}
```
**Response**: `201 Created`

### GET `/api/v1/physical/sessions/pre-create`
**Description**: Get pre-create data for physical assessment sessions  
**Authentication**: Required  
**Required permission**: `physical_sessions_add`  
**Response**: `201 Created`
```json
{
  "id": 123,
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-20",
  "student_count": 21,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null,
  "coach_name": null,
  "batch": { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" },
  "school": null,
  "batch_schedule": [
    { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
  ],
  "results": [
    {
      "id": 1000,
      "session_id": 123,
      "student_id": 100,
      "student": { "id": 100, "name": "string", "age": 12, "school_id": 1, "coach_id": 10, "batch_id": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null },
      "discipline": "string",
      "curl_up": 0,
      "push_up": 0,
      "sit_and_reach": 0.0,
      "is_present": true,
      "created_at": "2026-01-20T12:00:00Z",
      "updated_at": null
    }
  ]
}
```
```json
{
  "batches": [
    {
      "batch_id": 1,
      "batch_name": "string",
      "school_id": 1,
      "school_name": "string",
      "schedule": [
        { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" }
      ],
      "coaches": [ { "coach_id": 10, "coach_name": "string" } ],
      "students": [ { "student_id": 100, "student_name": "string", "age": 12 } ]
    }
  ]
}
```

### GET `/api/v1/physical/sessions`
**Description**: Get all physical assessment sessions (admin or coach view)  
**Authentication**: Required  
**Required permission**: `physical_sessions_view`  
**Response**: `200 OK`
```json
{
  "sessions": [
    {
      "session_id": 123,
      "batch_id": 1,
      "batch_name": "string",
      "school_id": 1,
      "school_name": "string",
      "coach_id": null,
      "coach_name": null,
      "date_of_session": "2026-01-20",
      "student_count": 21
    }
  ]
}
```

### GET `/api/v1/physical/sessions/{session_id}`
**Description**: Get specific physical assessment session by ID  
**Authentication**: Required  
**Required permission**: `physical_sessions_view`  
**Response**: `200 OK`
```json
{
  "id": 123,
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-20",
  "student_count": 21,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null,
  "coach_name": null,
  "batch": { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" },
  "school": null,
  "batch_schedule": [ { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" } ],
  "results": [
    {
      "id": 1000,
      "session_id": 123,
      "student_id": 100,
      "student": { "id": 100, "name": "string", "age": 12, "school_id": 1, "coach_id": 10, "batch_id": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null },
      "discipline": "string",
      "curl_up": 0,
      "push_up": 0,
      "sit_and_reach": 0.0,
      "is_present": true,
      "created_at": "2026-01-20T12:00:00Z",
      "updated_at": null
    }
  ]
}
```

### PUT `/api/v1/physical/sessions/{session_id}`
**Description**: Update physical assessment session  
**Authentication**: Required  
**Required permission**: `physical_sessions_edit`  
**Request Body** (partial update):
```json
{
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-21",
  "student_count": 22,
  "results": [ { "student_id": 100, "discipline": "string", "curl_up": 5 } ]
}
```

**Response**: `200 OK`
```json
{
  "id": 123,
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-21",
  "student_count": 22,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": "2026-01-21T12:00:00Z",
  "coach_name": null,
  "batch": { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" },
  "school": null,
  "batch_schedule": [],
  "results": []
}
```

### DELETE `/api/v1/physical/sessions/{session_id}`
**Description**: Delete physical assessment session  
**Authentication**: Required  
**Required permission**: `physical_sessions_edit`  
**Response**: `204 No Content`

### GET `/api/v1/physical/students`
**Description**: Get physical assessment student summary (admin or coach view)  
**Authentication**: Required  
**Required permission**: `physical_sessions_view`  
**Response**: `200 OK`
```json
{
  "students": [
    {
      "student_id": 100,
      "student_name": "string",
      "batch_id": 1,
      "batch_name": "string",
      "school_id": 1,
      "school_name": "string",
      "total_sessions": 3,
      "last_session_date": "2026-01-20"
    }
  ]
}
```

### GET `/api/v1/physical/students/{student_id}`
**Description**: Get detailed physical assessment results for a student  
**Authentication**: Required  
**Required permission**: `physical_sessions_view`  
**Response**: `200 OK`
```json
{
  "student_id": 100,
  "student_name": "string",
  "batch_id": 1,
  "batch_name": "string",
  "school_id": 1,
  "school_name": "string",
  "sessions": [
    {
      "session_id": 123,
      "date_of_session": "2026-01-20",
      "coach_id": null,
      "coach_name": null,
      "result": {
        "id": 1000,
        "session_id": 123,
        "student_id": 100,
        "discipline": "string",
        "curl_up": 0,
        "push_up": 0,
        "sit_and_reach": 0.0,
        "is_present": true,
        "created_at": "2026-01-20T12:00:00Z",
        "updated_at": null
      }
    }
  ]
}
```

### PUT `/api/v1/physical/students/{student_id}`
**Description**: Update physical assessment results for a student  
**Authentication**: Required  
**Required permission**: `physical_sessions_edit`  
**Response**: `200 OK`

### DELETE `/api/v1/physical/students/{student_id}`
**Description**: Delete physical assessment results for a student  
**Authentication**: Required  
**Required permission**: `physical_sessions_edit`  
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
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-20",
  "distance": 18,
  "results": [
    {
      "student_id": 100,
      "rounds": [
        {
          "number": 1,
          "shots": [
            { "x_coordinate": 0.0, "y_coordinate": 0.0, "score": 10, "max_score": 10, "arrow_number": 1 }
          ]
        }
      ]
    }
  ]
}
```
**Response**: `201 Created`
```json
{
  "id": 321,
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-20",
  "distance": 18,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null,
  "coach_name": null,
  "batch": { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" },
  "school": null,
  "results": [
    {
      "student_id": 100,
      "student": { "id": 100, "name": "string", "age": 12, "school_id": 1, "coach_id": 10, "batch_id": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null },
      "rounds": [ { "number": 1, "shots": [ { "id": 1, "x_coordinate": 0.0, "y_coordinate": 0.0, "score": 10, "max_score": 10, "arrow_number": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null } ] } ]
    }
  ],
  "student_count": 1
}
```

### GET `/api/v1/archery/sessions/pre-create`
**Description**: Get pre-create data for archery sessions  
**Authentication**: Required (Admin or Coach)  
**Response**: `200 OK`
```json
{
  "batches": [
    {
      "batch_id": 1,
      "batch_name": "string",
      "school_id": 1,
      "school_name": "string",
      "schedule": [ { "schedule_id": 1, "day_of_week": "Monday", "start_time": "04:00 PM", "end_time": "05:00 PM" } ],
      "coaches": [ { "coach_id": 10, "coach_name": "string" } ],
      "students": [ { "student_id": 100, "student_name": "string", "age": 12 } ]
    }
  ]
}
```

### GET `/api/v1/archery/sessions`
**Description**: Get all archery practice sessions (admin or coach view)  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "sessions": [
    {
      "session_id": 321,
      "batch_id": 1,
      "batch_name": "string",
      "school_id": 1,
      "school_name": "string",
      "coach_id": null,
      "coach_name": null,
      "date_of_session": "2026-01-20",
      "distance": 18.0,
      "student_count": 10
    }
  ]
}
```

### GET `/api/v1/archery/sessions/{session_id}`
**Description**: Get specific archery practice session by ID  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "id": 321,
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "date_of_session": "2026-01-20",
  "distance": 18.0,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null,
  "coach_name": null,
  "batch": { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" },
  "school": null,
  "results": [
    {
      "student_id": 100,
      "student": { "id": 100, "name": "string", "age": 12, "school_id": 1, "coach_id": 10, "batch_id": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null },
      "rounds": [ { "number": 1, "shots": [ { "id": 1, "x_coordinate": 0.0, "y_coordinate": 0.0, "score": 10, "max_score": 10, "arrow_number": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null } ] } ]
    }
  ],
  "student_count": 1
}
```

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
```json
{
  "students": [
    {
      "student_id": 100,
      "student_name": "string",
      "batch_id": 1,
      "batch_name": "string",
      "school_id": 1,
      "school_name": "string",
      "total_sessions": 5,
      "total_shots": 150,
      "average_score": 8.6,
      "last_session_date": "2026-01-20"
    }
  ]
}
```

### GET `/api/v1/archery/students/{student_id}`
**Description**: Get detailed archery results for a student  
**Authentication**: Required  
**Response**: `200 OK`
```json
{
  "student_id": 100,
  "student_name": "string",
  "batch_id": 1,
  "batch_name": "string",
  "school_id": 1,
  "school_name": "string",
  "sessions": [
    {
      "session_id": 321,
      "date_of_session": "2026-01-20",
      "coach_id": null,
      "coach_name": null,
      "distance": 18.0,
      "rounds": [ { "number": 1, "shots": [ { "id": 1, "x_coordinate": 0.0, "y_coordinate": 0.0, "score": 10, "max_score": 10, "arrow_number": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null } ] } ]
    }
  ]
}
```

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
  "name": "string",
  "description": "string (optional)"
}
```
**Response**: `201 Created`
```json
{
  "id": 11,
  "name": "Recurve Open",
  "description": "Optional description",
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null
}
```

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
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "category_id": 1,
  "tournament_name": "string",
  "tournament_location": "string",
  "date_of_session": "2026-01-20",
  "distance": 18,
  "results": [
    {
      "student_id": 100,
      "rounds": [
        {
          "number": 1,
          "shots": [
            { "x_coordinate": 0.0, "y_coordinate": 0.0, "score": 10, "max_score": 10, "arrow_number": 1 }
          ]
        }
      ]
    }
  ]
}
```
**Response**: `201 Created`
```json
{
  "id": 901,
  "coach_id": null,
  "school_id": null,
  "batch_id": 1,
  "category_id": 1,
  "tournament_name": "string",
  "tournament_location": "string",
  "date_of_session": "2026-01-20",
  "distance": 18.0,
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": null,
  "coach_name": null,
  "batch": { "batch_id": 1, "batch_name": "string", "school_id": 1, "school_name": "string" },
  "school": null,
  "category": { "id": 1, "name": "string", "description": "Optional" },
  "category_name_snapshot": "string",
  "results": [
    {
      "student_id": 100,
      "student": { "id": 100, "name": "string", "age": 12, "school_id": 1, "coach_id": 10, "batch_id": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null },
      "rounds": [ { "number": 1, "shots": [ { "id": 1, "x_coordinate": 0.0, "y_coordinate": 0.0, "score": 10, "max_score": 10, "arrow_number": 1, "created_at": "2026-01-20T12:00:00Z", "updated_at": null } ] } ]
    }
  ],
  "student_count": 1
}
```

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

## Attendance

Base path: `/api/v1/attendance`

### Workflow

- **Coach marks attendance**: When a coach creates an attendance session, they are automatically marked as `present` (auto-marked).
- **Admin marks attendance**: Admin can mark both student and coach attendance separately in the same request.
- **Access control**: Coaches can only see/edit sessions for their assigned batches.

### GET `/api/v1/attendance/sessions/pre-create`
**Description**: Get data needed to create an attendance session (batches, students, coaches)  
**Authentication**: Required (Admin or Coach)  
**Response**: `200 OK`
```json
{
  "batches": [
    {
      "id": 1,
      "name": "Batch A",
      "school_id": 1,
      "school_name": "School Name"
    }
  ],
  "students_by_batch": {
    "1": [
      { "id": 100, "name": "Student Name", "batch_id": 1 }
    ]
  },
  "coaches": [
    { "id": 10, "name": "Coach Name" }
  ]
}
```
**Note**: Coaches will only see batches they are assigned to. `coaches` array is only populated for admins.

### POST `/api/v1/attendance/sessions`
**Description**: Create a new attendance session  
**Authentication**: Required (Admin or Coach)  
**Request Body**:
```json
{
  "batch_id": 1,
  "school_id": 1,
  "date": "2026-01-24",
  "notes": "Optional notes",
  "student_attendances": [
    { "student_id": 100, "status": "present", "notes": "Optional" },
    { "student_id": 101, "status": "absent", "notes": "Sick" }
  ],
  "coach_attendances": [
    { "coach_id": 10, "status": "present", "notes": "Optional" }
  ]
}
```
**Notes**:
- `status` can be `"present"` or `"absent"`
- For **coaches**: `coach_attendances` is ignored - the coach is automatically marked present
- For **admins**: can specify both `student_attendances` and `coach_attendances`
- Only one session per batch per date is allowed

**Response**: `201 Created`
```json
{
  "id": 1,
  "batch_id": 1,
  "batch_name": "Batch A",
  "school_id": 1,
  "school_name": "School Name",
  "date": "2026-01-24",
  "marked_by_type": "coach",
  "marked_by_user_id": null,
  "marked_by_coach_id": 10,
  "marked_by_name": "Coach Name",
  "notes": "Optional notes",
  "student_attendances": [
    {
      "id": 1,
      "session_id": 1,
      "student_id": 100,
      "student_name": "Student Name",
      "status": "present",
      "notes": null,
      "created_at": "2026-01-24T12:00:00Z",
      "updated_at": null
    }
  ],
  "coach_attendances": [
    {
      "id": 1,
      "session_id": 1,
      "coach_id": 10,
      "coach_name": "Coach Name",
      "status": "present",
      "auto_marked": true,
      "notes": "Auto-marked present for marking student attendance",
      "created_at": "2026-01-24T12:00:00Z",
      "updated_at": null
    }
  ],
  "present_count": 1,
  "absent_count": 1,
  "total_students": 2,
  "created_at": "2026-01-24T12:00:00Z",
  "updated_at": null
}
```

### GET `/api/v1/attendance/sessions`
**Description**: Get all attendance sessions with optional filters  
**Authentication**: Required  
**Query Parameters**:
- `batch_id`: Filter by batch ID (optional)
- `school_id`: Filter by school ID (optional)
- `start_date`: Filter by start date, format `YYYY-MM-DD` (optional)
- `end_date`: Filter by end date, format `YYYY-MM-DD` (optional)
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 500)

**Note**: Coaches will only see sessions for their assigned batches.

**Response**: `200 OK`
```json
{
  "sessions": [
    {
      "id": 1,
      "batch_id": 1,
      "batch_name": "Batch A",
      "school_id": 1,
      "school_name": "School Name",
      "date": "2026-01-24",
      "marked_by_type": "coach",
      "marked_by_name": "Coach Name",
      "present_count": 5,
      "absent_count": 2,
      "total_students": 7,
      "coach_present_count": 1,
      "coach_absent_count": 0,
      "total_coaches": 1
    }
  ],
  "total": 1
}
```

### GET `/api/v1/attendance/sessions/{session_id}`
**Description**: Get specific attendance session by ID  
**Authentication**: Required  
**Response**: `200 OK` (Full AttendanceSessionResponse as shown in POST response)

### PUT `/api/v1/attendance/sessions/{session_id}`
**Description**: Update an attendance session  
**Authentication**: Required (Admin or Coach)  
**Request Body** (all fields optional):
```json
{
  "date": "2026-01-25",
  "notes": "Updated notes",
  "student_attendances": [
    { "student_id": 100, "status": "absent", "notes": "Changed to absent" }
  ],
  "coach_attendances": [
    { "coach_id": 10, "status": "present" }
  ]
}
```
**Note**: Coaches cannot update `coach_attendances`.

**Response**: `200 OK` (Full AttendanceSessionResponse)

### DELETE `/api/v1/attendance/sessions/{session_id}`
**Description**: Delete an attendance session  
**Authentication**: Required (Admin only)  
**Response**: `204 No Content`

### PATCH `/api/v1/attendance/sessions/{session_id}/students/{student_id}`
**Description**: Update a specific student's attendance in a session  
**Authentication**: Required (Admin or Coach)  
**Request Body**:
```json
{
  "status": "absent",
  "notes": "Left early"
}
```
**Response**: `200 OK`
```json
{
  "id": 1,
  "session_id": 1,
  "student_id": 100,
  "student_name": "Student Name",
  "status": "absent",
  "notes": "Left early",
  "created_at": "2026-01-24T12:00:00Z",
  "updated_at": "2026-01-24T13:00:00Z"
}
```

### PATCH `/api/v1/attendance/sessions/{session_id}/coaches/{coach_id}`
**Description**: Update a specific coach's attendance in a session  
**Authentication**: Required (Admin only)  
**Request Body**:
```json
{
  "status": "absent",
  "notes": "Could not attend"
}
```
**Response**: `200 OK`
```json
{
  "id": 1,
  "session_id": 1,
  "coach_id": 10,
  "coach_name": "Coach Name",
  "status": "absent",
  "auto_marked": false,
  "notes": "Could not attend",
  "created_at": "2026-01-24T12:00:00Z",
  "updated_at": "2026-01-24T13:00:00Z"
}
```

### GET `/api/v1/attendance/students/{student_id}/history`
**Description**: Get attendance history for a specific student  
**Authentication**: Required  
**Query Parameters**:
- `start_date`: Filter by start date (optional)
- `end_date`: Filter by end date (optional)

**Response**: `200 OK`
```json
{
  "student_id": 100,
  "student_name": "Student Name",
  "total_sessions": 10,
  "present_count": 8,
  "absent_count": 2,
  "attendance_percentage": 80.0,
  "history": [
    {
      "session_id": 1,
      "date": "2026-01-24",
      "batch_name": "Batch A",
      "school_name": "School Name",
      "status": "present",
      "marked_by_type": "coach",
      "marked_by_name": "Coach Name"
    }
  ]
}
```

### GET `/api/v1/attendance/coaches/{coach_id}/history`
**Description**: Get attendance history for a specific coach  
**Authentication**: Required  
**Note**: Coaches can only view their own attendance history.
**Query Parameters**:
- `start_date`: Filter by start date (optional)
- `end_date`: Filter by end date (optional)

**Response**: `200 OK`
```json
{
  "coach_id": 10,
  "coach_name": "Coach Name",
  "total_sessions": 15,
  "present_count": 14,
  "absent_count": 1,
  "attendance_percentage": 93.33,
  "history": [
    {
      "session_id": 1,
      "date": "2026-01-24",
      "batch_name": "Batch A",
      "school_name": "School Name",
      "status": "present",
      "auto_marked": true
    }
  ]
}
```

---

## Authentication & Authorization

### JWT Tokens

The API uses JWT (JSON Web Tokens) for authentication.

Token expiry is configured via environment variables (`ACCESS_TOKEN_EXPIRE_HOURS`, `REFRESH_TOKEN_EXPIRE_HOURS`). Default is 6 hours.

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
- Physical assessments: `physical_sessions_view`, `physical_sessions_add`, `physical_sessions_edit`

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

*Last Updated: 2026-01-24*

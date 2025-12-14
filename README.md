# BAFL Backend API# BAFL-Backend



A professional, scalable FastAPI backend with JWT authentication, role-based access control, and granular permission management.This is the backend for the BAFL website for the admins and coaches.



## 🚀 Features## Python Version



- **Clean Architecture**: Properly structured with separation of concernsThis project uses **Python 3.12** (the latest stable version). All developers must use Python 3.12 for consistency.

- **JWT Authentication**: Secure login with access and refresh tokens

- **Role-Based Access Control**: Admin, User, and Coach roles**We strongly recommend using Conda for environment management.** See [CONDA_SETUP.md](CONDA_SETUP.md) for detailed setup instructions.

- **Custom Permissions**: Granular permission assignment and revocation

- **Comprehensive Logging**: Separate logs for API, auth, database, and errors## Quick Setup

- **Type Safety**: Full Pydantic validation and type hints

- **Repository Pattern**: Clean data access layer```bash

- **Service Layer**: Business logic separation# Using Conda (recommended)

conda env create -f environment.yml

## 📁 Project Structureconda activate bafl-backend



```# Verify Python version

backend/python --version  # Should show 3.12.x

├── src/```

│   ├── api/                      # API layer

│   │   └── v1/                   # API version 1## Getting Started

│   │       ├── dependencies/     # Route dependencies (auth, etc.)

│   │       ├── endpoints/        # Route handlers<!-- Add your project-specific documentation here -->

│   │       └── router.py         # API router aggregation

│   ├── core/                     # Core functionality## Development

│   │   ├── config.py             # Application configuration

│   │   ├── logging.py            # Logging setupFor information about the CI/CD pipeline, branch protection, and development workflow, please see [CI/CD Setup Guide](CI_CD_SETUP.md).

│   │   └── security.py           # Security utilities (JWT, bcrypt)
│   ├── db/                       # Database layer
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── user.py           # User & RefreshToken models
│   │   │   └── permission.py    # Permission models
│   │   ├── repositories/         # Data access layer
│   │   │   ├── user_repository.py
│   │   │   └── permission_repository.py
│   │   └── database.py           # DB connection & session
│   ├── schemas/                  # Pydantic schemas
│   │   ├── auth.py               # Auth request/response schemas
│   │   ├── user.py               # User schemas
│   │   ├── permission.py         # Permission schemas
│   │   └── common.py             # Common schemas
│   ├── services/                 # Business logic
│   │   ├── auth_service.py       # Authentication logic
│   │   ├── user_service.py       # User management logic
│   │   └── permission_service.py # Permission management logic
│   └── utils/                    # Utility functions
│       └── db_init.py            # Database initialization
├── logs/                         # Application logs
├── tests/                        # Test files
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
└── README.md                     # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.12
- Conda (recommended for environment management)

### 1. Activate Conda Environment

```powershell
conda activate bafl-backend
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment

The `.env` file is already created. Update if needed:

```env
# Application
APP_NAME="BAFL Backend API"
DEBUG=True
ENVIRONMENT=development

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-this-in-production-minimum-32-characters-long

# Database
DATABASE_URL=sqlite:///./bafl_database.db

# Tokens
ACCESS_TOKEN_EXPIRE_DAYS=7
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. Run the Application

```powershell
conda activate bafl-backend
python main.py
```

The application will automatically:
- Create database tables
- Initialize all permissions
- Create the initial admin user
- Start the server at http://localhost:4256

## 📚 API Documentation

### Interactive Documentation

Once running, access:
- **Swagger UI**: http://localhost:4256/docs
- **ReDoc**: http://localhost:4256/redoc
- **Health Check**: http://localhost:4256/health

### Complete API Reference

For a comprehensive list of all API endpoints with detailed documentation, see [API_ENDPOINTS.md](API_ENDPOINTS.md).

This includes:
- Authentication endpoints
- User and permission management
- Coach, student, school, and batch management
- Physical assessment endpoints
- Archery practice and tournament endpoints
- Request/response examples
- Error codes and authentication details

## 👥 Roles & Permissions

### User Roles

| Role | Description | Can Create |
|------|-------------|------------|
| **Admin** | Full system access (only one) | Users, Coaches, Admins |
| **User** | Regular user access | None |
| **Coach** | Coaching staff access | None |

### Default Permissions by Role

**Admin:**
- `create_user` - Create regular users
- `create_coach` - Create coach users
- `create_admin` - Create admin users
- `delete_user` - Delete any user
- `delete_coach` - Delete coach users
- `delete_admin` - Delete admin users
- `view_all_users` - View all users
- `edit_all_users` - Edit any user information
- `assign_permissions` - Assign custom permissions
- `revoke_permissions` - Revoke custom permissions
- `view_permissions` - View permission details
- `view_own_profile` - View own profile
- `edit_own_profile` - Edit own profile

**User:**
- `view_own_profile` - View own profile
- `edit_own_profile` - Edit own profile

**Coach:**
- `view_own_profile` - View own profile
- `edit_own_profile` - Edit own profile

### Custom Permissions

The Admin can assign additional permissions to users beyond their role defaults, enabling fine-grained access control.

## 🔌 API Endpoints Overview

The backend provides RESTful API endpoints organized into the following modules:

### Core Modules
- **Authentication** (`/api/v1/auth`) - Login, token refresh, logout
- **User Management** (`/api/v1/users`) - CRUD operations for users
- **Permission Management** (`/api/v1/permissions`) - Assign/revoke permissions

### Academic Management
- **Coach Management** (`/api/v1/coaches`) - Manage coaching staff
- **Student Management** (`/api/v1/students`) - Student records and profiles
- **School Management** (`/api/v1/schools`) - School information
- **Batch Management** (`/api/v1/batches`) - Class/batch organization

### Assessment & Training
- **Physical Assessments** (`/api/v1/physical`) - Physical fitness tracking
- **Archery Practice** (`/api/v1/archery`) - Practice session management
- **Archery Tournaments** (`/api/v1/archery/tournaments`) - Tournament records

**📘 For complete endpoint documentation with request/response examples, see [API_ENDPOINTS.md](API_ENDPOINTS.md)**

## 📖 Usage Examples

### 1. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "raghav",
    "password": "raghav123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "abc123...",
  "token_type": "bearer"
}
```

### 2. Create User

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Coach",
    "username": "john_coach",
    "password": "secure_password",
    "role": "coach"
  }'
```

### 3. Assign Permission

```bash
curl -X POST "http://localhost:8000/api/v1/permissions/assign" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "permission": "delete_user"
  }'
```

## 📝 Logging

Logs are stored in the `logs/` directory:

- `api.log` - All API requests with timing and user info
- `auth.log` - Authentication events (login, logout, token operations)
- `database.log` - Database operations
- `error.log` - Error events with full tracebacks

**Log Format:**
```
2025-11-13 10:30:45 - auth - INFO - auth_service:authenticate_user:25 - Login successful for user: raghav
```

## 🔒 Security Features

1. **Password Hashing**: Bcrypt with automatic salt generation
2. **JWT Tokens**: 
   - Access tokens (24 hours default)
   - Refresh tokens (7 days default)
   - Stored refresh tokens with revocation support
3. **Permission Hierarchy**: Prevents privilege escalation
4. **Input Validation**: Comprehensive Pydantic validation
5. **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

## 👤 Initial Credentials

**Admin Account:**
- Username: `raghav`
- Password: `raghav123`

⚠️ **Important**: Change these credentials immediately in production!

## 🚢 Database Migration

Currently using SQLite for development. To migrate to PostgreSQL/Supabase:

1. Update `.env`:
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

2. Install PostgreSQL driver:
```powershell
conda activate bafl-backend
pip install psycopg2-binary
```

3. Restart the application - tables will be created automatically

## 🧪 Development

### Running in Debug Mode

```powershell
conda activate bafl-backend
python main.py
```

### Using Swagger UI

1. Navigate to http://localhost:8000/docs
2. Click "Authorize" button
3. Enter: `Bearer YOUR_ACCESS_TOKEN`
4. Test endpoints interactively

## 🐛 Troubleshooting

### Database Locked
If you get "database is locked", ensure no other process is accessing the SQLite file.

### Token Expired
Access tokens expire after 24 hours. Use the `/api/v1/auth/refresh` endpoint with your refresh token.

### Permission Denied
Check your permissions with `GET /api/v1/users/me` to see all assigned permissions.

### Conda Environment Issues
Make sure to always activate the conda environment before running:
```powershell
conda activate bafl-backend
```

## 📊 Code Quality

- **Type Hints**: Full type annotations throughout
- **Docstrings**: Comprehensive documentation for all functions
- **Separation of Concerns**: Clean architecture with distinct layers
- **Error Handling**: Proper exception handling with meaningful messages
- **Logging**: Comprehensive logging at all levels

## 🤝 Contributing

When adding new features:

1. Create models in `src/db/models/`
2. Create repositories in `src/db/repositories/`
3. Implement business logic in `src/services/`
4. Define schemas in `src/schemas/`
5. Create endpoints in `src/api/v1/endpoints/`
6. Add appropriate logging

---

**Built with ❤️ using FastAPI**

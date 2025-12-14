# BAFL Backend API

A professional, high-performance FastAPI backend for the BAFL (Bangalore Archery for Life) platform with JWT authentication, role-based access control, and comprehensive sports management features.

## 🚀 Key Features

- **Clean Architecture**: Separation of concerns with repository, service, and API layers
- **JWT Authentication**: Secure access and refresh token management
- **Role-Based Access Control**: 77 granular permissions across 10 categories
- **Sports Management**: Physical assessments, archery sessions, and tournament tracking
- **Performance Optimized**: NullPool configuration, eager loading to prevent N+1 queries
- **Comprehensive Logging**: Separate logs for API, auth, database, and errors
- **Type Safety**: Full Pydantic validation and SQLAlchemy 2.0 type hints
- **Database**: Supabase PostgreSQL with session pooler support

## 📋 Prerequisites

- **Python 3.12** (required for consistency)
- **Conda** (recommended for environment management)
- **Supabase Account** (for production database)

## ⚡ Quick Start

```bash
# Create and activate environment
conda env create -f environment.yml
conda activate bafl-backend

# Verify Python version
python --version  # Should show 3.12.x

# Run the application
python main.py
```

The server will start at **http://localhost:4256**

**Default Admin Credentials:**
- Username: `raghav`
- Password: `raghav123`

⚠️ **Change these immediately in production!**

## 📁 Project Structure

```
backend/
├── src/
│   ├── api/v1/              # API endpoints
│   │   ├── dependencies/    # Auth & dependencies
│   │   └── endpoints/       # Route handlers
│   ├── core/                # Configuration & security
│   ├── db/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   └── database.py      # DB connection
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── utils/               # Utilities & DB init
├── docs/                    # Documentation
├── logs/                    # Application logs
├── tests/                   # Unit & integration tests
├── scripts/                 # Deployment scripts
├── main.py                  # Application entry
├── requirements.txt         # Dependencies
└── environment.yml          # Conda environment
```

## 🛠️ Setup & Configuration

### Environment Setup

See **[docs/CONDA_SETUP.md](docs/CONDA_SETUP.md)** for detailed environment setup instructions.

```bash
# Quick setup
conda env create -f environment.yml
conda activate bafl-backend
```

### Database Configuration

Update `.env` with your Supabase connection:

```env
DATABASE_URL=postgresql://postgres.[project]:[password]@[host].pooler.supabase.com:5432/postgres
SECRET_KEY=your-secret-key-minimum-32-characters
ACCESS_TOKEN_EXPIRE_DAYS=7
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Running the Application

```bash
cd backend
conda activate bafl-backend
python main.py
```

The application will:
- ✅ Create database tables
- ✅ Initialize 77 permissions
- ✅ Create admin user
- ✅ Start server at http://localhost:4256

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:4256/docs
- **ReDoc**: http://localhost:4256/redoc
- **Health Check**: http://localhost:4256/health

### Complete API Reference

**[docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)** - Comprehensive API documentation including:
- All endpoints with request/response examples
- Authentication & authorization details
- Error codes and handling
- Rate limiting and best practices

## � Roles & Permissions

### Overview

- **77 Granular Permissions** across 10 categories
- **3 User Roles**: Admin (77 permissions), Coach (28 permissions), User (16 permissions)
- **Custom Permission Assignment**: Fine-grained access control

See **[docs/PERMISSIONS_SETUP.md](docs/PERMISSIONS_SETUP.md)** for complete permission details.

### Quick Reference

| Role | Access Level | Key Permissions |
|------|-------------|-----------------|
| **Admin** | Full system access | All 77 permissions |
| **Coach** | Manage batches & assessments | View/create/edit students, batches, assessments |
| **User** | Limited access | View own profile, edit own info |

## 🔌 API Modules

### Core Services
- **Authentication** - Login, token refresh, logout
- **User Management** - CRUD operations with role-based access
- **Permission Management** - Assign/revoke granular permissions

### Academic Management  
- **Schools** - School information and management
- **Batches** - Class organization and scheduling
- **Coaches** - Staff management with batch/school assignments
- **Students** - Student profiles and batch enrollment

### Performance Tracking
- **Physical Assessments** - Fitness tests and progress tracking
- **Archery Sessions** - Practice session management and scoring
- **Archery Tournaments** - Tournament categories and results

**📘 Complete documentation: [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)**

## 📖 Usage Examples

### Authentication

```bash
# Login
curl -X POST "http://localhost:4256/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "raghav", "password": "raghav123"}'

# Response: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

### Using Swagger UI (Recommended)

1. Navigate to http://localhost:4256/docs
2. Click **"Authorize"** button
3. Enter: `Bearer YOUR_ACCESS_TOKEN`
4. Test all endpoints interactively

**More examples in [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)**

## ⚡ Performance Optimizations

- **NullPool Configuration**: Eliminates dual pooling with Supabase session pooler
- **Eager Loading**: `joinedload` and `selectinload` to prevent N+1 queries
- **Removed Unnecessary Refreshes**: Eliminated 20+ redundant `db.refresh()` calls
- **Optimized Serialization**: Efficient relationship loading for list endpoints

**Details:** [docs/LATENCY_OPTIMIZATIONS.md](docs/LATENCY_OPTIMIZATIONS.md) | [docs/N+1_QUERY_FIX.md](docs/N+1_QUERY_FIX.md)

## 📝 Logging

Logs stored in `logs/` directory:
- `api.log` - All API requests with timing
- `auth.log` - Authentication events
- `database.log` - Database operations
- `error.log` - Errors with tracebacks

## 🔒 Security

- ✅ Bcrypt password hashing
- ✅ JWT access (7 days) and refresh tokens (7 days)
- ✅ Role-based access control with 77 permissions
- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ Comprehensive input validation with Pydantic

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

**Test Results:** [docs/UNIT_TESTS_SUMMARY.md](docs/UNIT_TESTS_SUMMARY.md) | [docs/INTEGRATION_TEST_RESULTS_SUMMARY.md](docs/INTEGRATION_TEST_RESULTS_SUMMARY.md)

## 🚀 Deployment

See **[docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md)** for:
- GitHub Actions CI/CD pipeline
- Branch protection rules
- Staging and production deployment
- Environment configuration

## 📚 Additional Documentation

| Document | Description |
|----------|-------------|
| [API_ENDPOINTS.md](docs/API_ENDPOINTS.md) | Complete API reference with examples |
| [PERMISSIONS_SETUP.md](docs/PERMISSIONS_SETUP.md) | 77 permissions across 10 categories |
| [CONDA_SETUP.md](docs/CONDA_SETUP.md) | Environment setup guide |
| [LATENCY_OPTIMIZATIONS.md](docs/LATENCY_OPTIMIZATIONS.md) | Performance optimization techniques |
| [N+1_QUERY_FIX.md](docs/N+1_QUERY_FIX.md) | Eager loading implementation |
| [EXERCISE_LEVELS_README.md](docs/EXERCISE_LEVELS_README.md) | Exercise level mappings |
| [QUICKSTART.md](docs/QUICKSTART.md) | Quick start guide |
| [CI_CD_SETUP.md](docs/CI_CD_SETUP.md) | CI/CD pipeline and deployment |

## 🐛 Troubleshooting

**Token Expired**: Use `/api/v1/auth/refresh` with refresh token

**Permission Denied**: Check permissions at `GET /api/v1/users/me`

**High Latency**: Ensure eager loading is enabled (see [N+1_QUERY_FIX.md](docs/N+1_QUERY_FIX.md))

**Environment Issues**: Always activate conda environment:
```bash
conda activate bafl-backend
```

## 🤝 Contributing

1. Create models in `src/db/models/`
2. Implement repositories in `src/db/repositories/`
3. Add business logic in `src/services/`
4. Define Pydantic schemas in `src/schemas/`
5. Create API endpoints in `src/api/v1/endpoints/`
6. Add comprehensive logging
7. Write unit and integration tests
8. Update documentation

---

**Built with ❤️ using FastAPI** | **Python 3.12** | **SQLAlchemy 2.0** | **Supabase PostgreSQL**

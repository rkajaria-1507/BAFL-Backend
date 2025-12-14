# BAFL Backend - Unit Tests Summary

## Overview
This document provides a comprehensive summary of unit tests for the BAFL Backend. Unit tests focus on testing individual components (repositories, services) in isolation using mocked dependencies, ensuring that the business logic and data access patterns work correctly without requiring a database or external services.

## Test Execution Results

**Total Tests**: 412 passing  
**Execution Time**: ~1.08 to 1.25 seconds  
**Status**: ✅ All tests passing

## Test Organization

**Breakdown by Component**:
- **Repository Tests**: 211 tests (Physical: 38, Archery: 61, Basic CRUD: 66, Permissions: 46)
- **Service Tests**: 201 tests (Physical: 31, Archery: 45, Auth & Basic CRUD: 79, Permissions: 46)

**Test Coverage Types**:
- ✅ **Normal Cases**: Standard operations and expected inputs
- ✅ **Boundary Cases**: Minimum/maximum values, empty strings, limits
- ✅ **Edge Cases**: Special characters, Unicode, None values, inactive states, negative values

### 1. Physical Assessment Repository Tests (38 tests)

#### Physical Session Repository (16 tests)
Located in `tests/unit/test_repositories/test_physical_session_repository.py`

**Test Categories**:
- **Create Operations (2 tests)**: Session creation with/without coach
- **Read Operations (7 tests)**: Get by ID, get all (with pagination), filter by batch, filter by coach, empty result handling
- **Update Operations (3 tests)**: Single/multiple field updates, empty update handling
- **Delete Operations (2 tests)**: Session deletion, cascade deletion with results
- **Edge Cases (2 tests)**: None coach handling, empty result lists

**Coverage**: All CRUD operations with mocked database Session

#### Physical Results Repository (22 tests)
Located in `tests/unit/test_repositories/test_physical_results_repository.py`

**Test Categories**:
- **Create Operations (4 tests)**: Single result creation, bulk creation, all exercises, absent student
- **Read Operations (7 tests)**: Get by ID, get by session, get by student, get by session+student, empty results, multiple sessions
- **Update Operations (4 tests)**: Single exercise update, multiple exercises, set null values, empty update
- **Delete Operations (4 tests)**: Single deletion, bulk delete by student, empty result handling, None rowcount
- **Edge Cases (3 tests)**: Zero values, float precision, complex queries

**Coverage**: Single and bulk operations, complex filtering, edge case values

### 2. Physical Assessment Service Tests (31 tests)
Located in `tests/unit/test_services/test_physical_assessment_service.py`

#### Test Categories:

**Exercise Validation (19 tests)**:
- Curl-up: Valid range (0-200), exceeds maximum, negative values, boundary values
- Push-up: Valid range (0-150), boundary values  
- Sit-and-reach: Valid range (0-100), exceeds maximum
- Walk 600m: Zero rejected, below minimum (< 1.5 min), valid values, boundaries
- Dash 50m: Zero rejected, below minimum (< 5.0 sec), valid values
- Bow Hold: Valid range (0-600 sec), exceeds maximum
- Plank: Valid range (0-10 min), exceeds maximum, boundaries
- None values allowed for all exercises
- Unknown exercises ignored
- Float values accepted

**Exercise Constraints (4 tests)**:
- All 7 exercises present in EXERCISE_CONSTRAINTS
- Correct types (TIMED vs COUNT)
- Timed exercises have minimum thresholds
- Count exercises start at zero

**Validation Boundaries (3 tests)**:
- Curl-up at 0 and 200
- Walk 600m at 1.5 (minimum valid)
- Plank at 0 and 10 minutes

**Error Details (3 tests)**:
- Maximum exceeded error structure
- Minimum below error structure  
- Zero for timed exercise error structure
- Student ID included in errors

**Multiple Exercise Validation (2 tests)**:
- All valid exercises pass
- Mixed valid and None values
- Stops at first invalid exercise

### 3. Archery Repository Tests (61 tests)

#### Archery Session Repository (6 tests)
Located in `tests/unit/test_repositories/test_archery_repository.py`

**Test Categories**:
- **Create Operations (2 tests)**: Session creation with/without coach, different distances (18m, 30m, 50m)
- **Read Operations (4 tests)**: Get by ID (found/not found), get all (empty/multiple results)

**Coverage**: Basic CRUD operations with modern SQLAlchemy 2.0 style (scalar, scalars, execute)

#### Archery Result Repository (19 tests)
Located in `tests/unit/test_repositories/test_archery_repository.py`

**Test Categories**:
- **Create Operations (5 tests)**: Empty list, single result, multiple results, zero score, max score, negative coordinates, different rounds
- **Read Operations (6 tests)**: Get by session, get by student, get by session+student (found/not found)
- **Delete Operations (6 tests)**: Delete by session, delete by student, delete for student in session (success/no-op)
- **Edge Cases (2 tests)**: Negative coordinates, maximum score (bullseye)

**Coverage**: Bulk operations, complex queries, coordinate-based scoring

#### Archery Tournament Category Repository (11 tests)
Located in `tests/unit/test_repositories/test_archery_tournament_repository.py`

**Test Categories**:
- **Create Operations (2 tests)**: Create category with name and description
- **Read Operations (7 tests)**: Get all (empty/multiple), get by ID (found/not found), get by name (found/not found/case-sensitive)
- **Delete Operations (2 tests)**: Delete category (success/non-existent), returns boolean

**Coverage**: Category management, name-based lookups, case-sensitive queries

#### Archery Tournament Session Repository (7 tests)
Located in `tests/unit/test_repositories/test_archery_tournament_repository.py`

**Test Categories**:
- **Create Operations (3 tests)**: Session creation with/without coach, different distances (18m, 30m, 50m)
- **Read Operations (4 tests)**: Get by ID (found/not found), get all (empty/multiple)

**Coverage**: Tournament session management with category relationships

#### Archery Tournament Result Repository (18 tests)
Located in `tests/unit/test_repositories/test_archery_tournament_repository.py`

**Test Categories**:
- **Create Operations (6 tests)**: Empty list, single/multiple results, zero/max score, negative coordinates, different rounds, multiple students
- **Read Operations (4 tests)**: Get by session, get by student (found/not found)
- **Delete Operations (6 tests)**: Delete by session, delete by student, delete for student in session (success/no-op)
- **Edge Cases (2 tests)**: Multiple students in same session, different rounds

**Coverage**: Tournament-specific result tracking with competitive scoring

---

### 4. Permission Repository Tests (46 tests)

**Location**: `tests/unit/test_repositories/`
**File**: `test_permission_repository.py`

#### PermissionRepository (15 tests)

**Test Categories**:
- **Read Operations (6 tests)**: Get by name (enum/string/not found), get by ID (success/not found), get all
- **Create Operations (4 tests)**: Create with enum, create with string, create without description, long name (100 chars)
- **Get or Create (2 tests)**: Existing permission, new permission
- **Edge Cases (3 tests)**: Empty string name, max length (100 chars), special characters

**Coverage**: Permission CRUD operations with boundary testing (max name length) and edge cases (empty names, special characters)

#### UserPermissionRepository (18 tests)

**Test Categories**:
- **Read Operations (6 tests)**: Get user permissions (empty/with results), get coach permissions, has_permission (user/coach - true/false)
- **Assign Operations (4 tests)**: Assign to user, assign to coach, no target raises error, without assigner (None)
- **Revoke Operations (3 tests)**: Revoke from user/coach success, not found
- **Edge Cases (5 tests)**: User ID 0, negative user ID, both user and coach IDs, revoke with zero IDs, has_permission with both IDs

**Coverage**: Custom permission assignment/revocation with boundary testing (ID 0, negative IDs) and edge cases (multiple targets, None values)

#### RefreshTokenRepository (13 tests)

**Test Categories**:
- **Create Operations (4 tests)**: Create for user, create for coach, no target raises error, both targets raises error
- **Read Operations (2 tests)**: Get by token (success/not found)
- **Revoke Operations (4 tests)**: Revoke token (success/not found), revoke all user tokens, revoke all coach tokens
- **Edge Cases (3 tests)**: User ID 0, empty token string, very long token (1000 chars), special characters, nonexistent user, token uniqueness

**Coverage**: Refresh token lifecycle with boundary testing (ID 0, token length) and edge cases (empty/special character tokens, nonexistent users)

---

### 5. Authentication & Basic CRUD Repository Tests (45 tests)

**Location**: `tests/unit/test_repositories/`

#### Coach Repository (21 tests)
**File**: `test_coach_repository.py`

**Test Categories**:
- **Create Operations (3 tests)**: Active coach, inactive coach, special characters in username
- **Read Operations (8 tests)**: Get by ID (found/not found), get by username (found/not found/case-sensitive), get all (empty/paginated/zero limit/large skip)
- **Update Operations (6 tests)**: Single field, multiple fields, empty data, inactive status, password update, username update
- **Delete Operations (1 test)**: Successful deletion
- **Edge Cases (3 tests)**: Case-sensitive username, boundary pagination values, inactive coach creation

**Coverage**: CRUD operations with boundary testing (pagination limits, case sensitivity) and edge cases (inactive status, special characters)

#### School Repository (7 tests)
**File**: `test_basic_repositories.py`

**Test Categories**:
- **Create Operations (2 tests)**: School creation, Unicode names (École Française)
- **Read Operations (3 tests)**: Get by ID (found/not found), get all
- **Update Operations (1 test)**: Update school name
- **Delete Operations (1 test)**: School deletion

**Coverage**: School CRUD operations with Unicode support

#### User Repository (11 tests)
**File**: `test_basic_repositories.py`

**Test Categories**:
- **Create Operations (2 tests)**: User creation with hashed password, all role types (ADMIN/USER/COACH - boundary test)
- **Read Operations (4 tests)**: Get by ID, get by username, get all with pagination
- **Update Operations (1 test)**: Update user fields
- **Delete Operations (1 test)**: User deletion
- **Utility Operations (2 tests)**: Username existence check (true/false)

**Coverage**: User management with all role types and username uniqueness validation

#### Student Repository (12 tests)
**File**: `test_basic_repositories.py`

**Test Categories**:
- **Create Operations (2 tests)**: Student creation with batch, negative age handling
- **Read Operations (7 tests)**: Get by ID, get all, get by batch (with results/empty), pagination (boundary values, large skip)
- **Update Operations (2 tests)**: Update student fields, None values (removing batch assignment)
- **Delete Operations (1 test)**: Student deletion

**Coverage**: Student management with boundary testing (age 0, negative age, pagination) and edge cases (None batch_id)

#### Batch Repository (10 tests)
**File**: `test_basic_repositories.py`

**Test Categories**:
- **Create Operations (2 tests)**: Batch creation, very long names (150 chars - boundary test)
- **Read Operations (6 tests)**: Get by ID, get all, get by school (with results/empty), get by coach (with results/empty/multiple batches)
- **Update Operations (1 test)**: Update batch name
- **Delete Operations (1 test)**: Batch deletion

**Coverage**: Batch management with boundary testing (maximum name length, multiple batches per coach)

---

### 6. Archery Service Tests (45 tests)

**Location**: `tests/unit/test_services/`

#### ArcheryService Tests (19 tests)
Located in `tests/unit/test_services/test_archery_service.py`

**Test Categories**:
- **Validation Tests (10 tests)**: Student-batch membership validation, duplicate round detection using `seen_pairs` set, valid student ID set creation from batch students, error message format verification
- **Results Structure Tests (3 tests)**: Shot data structure validation (x, y, score), session info inclusion, multiple students per session
- **Edge Cases (6 tests)**: Zero scores and maximum scores (10), negative coordinates handling, multiple rounds per student (1-6), different distances (18m, 30m, 50m), empty results list handling

**Coverage**: Service-level validation logic, duplicate detection algorithms, business rule enforcement

#### ArcheryTournamentService Tests (26 tests)
Located in `tests/unit/test_services/test_archery_tournament_service.py`

**Test Categories**:
- **Category Validation (4 tests)**: Category ID required (None rejected), category not found raises 404, category exists validation
- **Category Creation (4 tests)**: Duplicate name rejection (400 error), unique name acceptance, category data structure, case-sensitive name handling
- **Category Deletion (2 tests)**: Not found raises 404, successful deletion
- **Session Validation (4 tests)**: Student-batch membership checks, duplicate round detection, tournament-specific validation
- **Session Creation (3 tests)**: Category name snapshot at creation, tournament details (name, location, date), distance tracking
- **Results Creation (3 tests)**: Result structure validation, multiple students handling, empty results list
- **Pre-Create Data (2 tests)**: Categories and batches structure, data formatting for frontend
- **Edge Cases (4 tests)**: Case-sensitive category names, optional coach field, coordinate ranges, score boundaries

**Coverage**: Category management, tournament session logic, validation rules for competitive archery

---

### 7. Authentication Service Tests (26 tests)

**Location**: `tests/unit/test_services/`
**File**: `test_auth_service.py`

**Test Categories**:
- **User Authentication (3 tests)**: Successful login, wrong password, inactive user
- **Coach Authentication (4 tests)**: Successful login, wrong password, inactive coach, neither user nor coach found
- **Token Creation (4 tests)**: Build user payload, build coach payload, create tokens for user, create tokens for coach
- **Token Refresh (5 tests)**: Successful refresh, invalid token, revoked token, expired token, inactive user
- **Logout (2 tests)**: Successful logout, token not found
- **Edge Cases (8 tests)**: Empty username/password, special characters in username, very long username (150 chars), user/coach deleted during token refresh, no subject in token, just-expired token

**Coverage**: Authentication flow with comprehensive boundary testing (username length limits, empty inputs) and edge cases (deleted users, special characters, timing boundaries)

---

### 8. Basic CRUD Service Tests (53 tests)

**Location**: `tests/unit/test_services/`
**File**: `test_basic_services.py`

#### SchoolService Tests (11 tests)
- **Create (3 tests)**: School creation, empty address (optional field), very long name (150 chars), special characters
- **Read (2 tests)**: Get school (found/not found)
- **Update (3 tests)**: Update success, not found, partial data (exclude_unset)
- **Delete (2 tests)**: Delete success, not found
- **Edge Cases (1 test)**: Special characters in school name

**Coverage**: School CRUD with boundary testing (max length names, empty optional fields, special characters)

#### UserService Tests (14 tests)
- **Create (6 tests)**: Regular user, coach role creates coach profile, duplicate username rejection, min/max username length (2-150 chars), special characters
- **Read (2 tests)**: Get by ID (found/404)
- **Update (6 tests)**: Password hashing, duplicate username rejection, same username (should succeed), empty password (None), all fields None (edge case)

**Coverage**: User management with boundary testing (username length limits 2-150), edge cases (None values, same username update, special characters)

#### StudentService Tests (10 tests)
- **Create (6 tests)**: With batch validation, invalid batch (404), no batch (batch_id=None), min age (5), max age (18), Unicode name
- **Read (5 tests)**: Get student (found/404), get by batch (with validation/empty result), invalid batch (404)
- **Delete (2 tests)**: Delete success, not found returns false

**Coverage**: Student CRUD with boundary testing (age limits 5-18), edge cases (None batch_id, Unicode names, empty batch results)

#### BatchService Tests (18 tests)
- **Create (2 tests)**: Batch creation, school not found (404)
- **Read (3 tests)**: Get batch (found/not found), get all batches (with results/empty)
- **Update (3 tests)**: Update batch name, update school, not found (404)
- **Delete (2 tests)**: Delete success, not found (404)
- **Pre-Create Data (1 test)**: Get schools and coaches for batch creation form
- **Edge Cases (7 tests)**: Very long name (150 chars), special characters, no school (None), all None values in update, no coaches, coach with no assignments

**Coverage**: Batch CRUD with boundary testing (max name length 150 chars), edge cases (None school, None values, special characters, empty coaches)

---

### 9. Permission Service Tests (46 tests)

**Location**: `tests/unit/test_services/`
**File**: `test_permission_service.py`

#### Get User Permissions (6 tests)
- **Role-Based Permissions (3 tests)**: ADMIN permissions (many base permissions), USER permissions (limited base), COACH permissions
- **Custom Permissions (1 test)**: Custom assigned permissions included
- **Deduplication (1 test)**: Duplicate permissions filtered
- **Sorting (1 test)**: Permissions returned sorted

**Coverage**: Role-based permission retrieval with custom permission overlay and deduplication

#### Has Permission (4 tests)
- **Permission Check (2 tests)**: With enum (true), with string (true)
- **No Permission (1 test)**: Returns false when lacking permission
- **Custom Permission (1 test)**: Checks custom assigned permissions

**Coverage**: Permission checking with PermissionType enum and string support

#### Role Authorization (8 tests)
- **Can Create Role (5 tests)**: ADMIN can create USER/COACH/ADMIN, USER cannot create USER, COACH cannot create ADMIN
- **Can Delete User (3 tests)**: ADMIN can delete USER/COACH, USER cannot delete USER

**Coverage**: Role-based creation and deletion authorization

#### Permission Management (4 tests)
- **Can Manage Permissions (4 tests)**: ADMIN can manage user permissions, cannot manage own, non-ADMIN cannot manage, COACH cannot manage

**Coverage**: Permission management authorization rules

#### Get All Permissions (2 tests)
- **Get All (2 tests)**: Returns all permissions, returns empty list

**Coverage**: Permission listing

#### Get Permission By ID (2 tests)
- **Get By ID (2 tests)**: Success, 404 not found

**Coverage**: Permission retrieval with error handling

#### Assign Permission By ID (6 tests)
- **Assign Success (2 tests)**: To user, to coach
- **Assign Errors (4 tests)**: No target (400), both targets (400), already assigned (400), permission not found (404)

**Coverage**: Permission assignment with comprehensive error scenarios

#### Revoke Permission By ID (4 tests)
- **Revoke Success (2 tests)**: From user, from coach
- **Revoke Errors (2 tests)**: Not assigned (400), no target (400)

**Coverage**: Permission revocation with error handling

#### Edge Cases (10 tests)
- **Zero ID Handling (1 test)**: User ID 0 converted to None
- **None Permission (1 test)**: Handles None permission in assignment
- **Empty String (1 test)**: Empty permission string returns false
- **Custom Permission Auth (1 test)**: User with custom CREATE_COACH can create coach
- **Alternate Methods (4 tests)**: Revoke with PermissionType, revoke not found (404), assign with PermissionType, get details sorted
- **Permission Details (2 tests)**: Handles None permission, returns sorted results

**Coverage**: Comprehensive edge case handling including None values, empty strings, zero IDs, sorting, and alternate method signatures

---

## Exercise Validation Rules

| Exercise | Type | Minimum | Maximum | Zero Allowed | None Allowed |
|----------|------|---------|---------|--------------|--------------|
| curl_up | COUNT | 0 | 200 | ✅ Yes | ✅ Yes |
| push_up | COUNT | 0 | 150 | ✅ Yes | ✅ Yes |
| sit_and_reach | COUNT | 0 | 100 | ✅ Yes | ✅ Yes |
| walk_600m | TIMED | 1.5 min | - | ❌ No | ✅ Yes |
| dash_50m | TIMED | 5.0 sec | - | ❌ No | ✅ Yes |
| bow_hold | COUNT | 0 | 600 sec | ✅ Yes | ✅ Yes |
| plank | COUNT | 0 | 10 min | ✅ Yes | ✅ Yes |

## Key Characteristics

### Speed
- **Unit Tests**: ~1.08 to 1.25 seconds (412 tests)
- **Integration Tests**: ~111 seconds (267 tests)
- **Speed Advantage**: 103x faster than integration tests

### Coverage Characteristics
- **Normal Cases**: All CRUD operations tested with expected inputs
- **Boundary Cases**: Min/max values (age 0-18, username 2-150 chars, pagination limits), empty strings, zero limits
- **Edge Cases**: None values, Unicode characters (École, François, Müller), special characters (@, -, #), negative values, inactive states, deleted entities
- **Error Scenarios**: 404 not found, 400 duplicate errors, 401 unauthorized, token expiration, validation failures

### Isolation
- All database interactions mocked using `unittest.mock.Mock`
- No actual database required
- No external service dependencies
- Tests run completely in-memory
- Modern SQLAlchemy 2.0 patterns (scalar, scalars, execute) properly mocked

### Purpose
While integration tests verify the complete flow from API endpoint to database, unit tests:
- **Verify Logic Correctness**: Ensure individual functions work as expected
- **Test Edge Cases**: Easy to test error conditions and boundary values
- **Enable Fast Feedback**: Developers can run tests in < 1 second
- **Pinpoint Failures**: When a test fails, you know exactly which component has the issue
- **Support Refactoring**: Safe to refactor knowing logic is tested independently

### Coverage Focus
1. **Repositories**: Data access patterns, query construction, CRUD operations
2. **Services**: Business logic, validation rules, error handling
3. **Edge Cases**: None values, zero values, boundary conditions, empty results, negative coordinates
4. **Error Scenarios**: Invalid inputs, constraint violations, missing data

## Why Unit Tests Are NOT Repetitive with Integration Tests

### Different Purposes
- **Integration Tests**: Verify entire request/response flow works end-to-end
- **Unit Tests**: Verify individual component logic is correct

### Different Approaches
- **Integration Tests**: Use real database, real services, real repositories
- **Unit Tests**: Use mocks to isolate component being tested

### Different Value
- **Integration Tests**: "Does the system work as a whole?"
- **Unit Tests**: "Does this specific function/method work correctly?"

### Example Scenario
When a test fails:
- **Integration Test Failure**: "Something is broken in the archery flow" (could be endpoint, service, repository, database, schema, or validation)
- **Unit Test Failure**: "The `delete_by_session()` method in ArcheryResultRepository doesn't execute the delete statement" (pinpoints exact issue)

### Complementary Testing
Both types of tests are essential:
- Integration tests catch issues with component interaction
- Unit tests catch issues with individual component logic
- Together they provide comprehensive coverage

## Running Unit Tests

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/test_repositories/test_physical_session_repository.py -v

# Run archery tests only
python -m pytest tests/unit/test_repositories/ -k "archery" -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html
```

## Test Structure

```
tests/unit/
├── test_repositories/
│   ├── test_physical_session_repository.py          (16 tests)
│   ├── test_physical_results_repository.py          (22 tests)
│   ├── test_archery_repository.py                   (25 tests)
│   ├── test_archery_tournament_repository.py        (36 tests)
│   ├── test_coach_repository.py                     (21 tests)
│   ├── test_basic_repositories.py                   (45 tests)
│   └── test_permission_repository.py                (46 tests)
└── test_services/
    ├── test_physical_assessment_service.py          (31 tests)
    ├── test_archery_service.py                      (19 tests)
    ├── test_archery_tournament_service.py           (26 tests)
    ├── test_auth_service.py                         (26 tests)
    ├── test_basic_services.py                       (35 tests)
    └── test_permission_service.py                   (46 tests)
```

## Mocking Strategy

### Database Session Mock (Modern SQLAlchemy 2.0)
```python
db = Mock()  # Mock SQLAlchemy Session

# For scalar queries (returning single object or None)
db.scalar.return_value = mock_object  # or None

# For scalars queries (returning list)
mock_scalars = Mock()
mock_scalars.all.return_value = [mock_obj1, mock_obj2]
db.scalars.return_value = mock_scalars

# For execute queries (INSERT/UPDATE/DELETE)
mock_result = Mock()
mock_result.rowcount = 1  # Number of affected rows
db.execute.return_value = mock_result

# For create/update operations
db.add.assert_called_once_with(expected_object)
db.commit.assert_called_once()
```

### Benefits of Mocking
1. **No Database Required**: Tests run without PostgreSQL or SQLite
2. **Full Control**: Can simulate any scenario (empty results, errors, edge cases)
3. **Deterministic**: Same results every time, no data dependency
4. **Fast**: No I/O operations, pure in-memory computation

## Summary

### Test Coverage Complete ✅

All major components now have comprehensive unit tests:

1. ✅ **Physical Assessment**: Repository (38) + Service (31) = 69 tests
2. ✅ **Archery**: Repository (61) + Service (45) = 106 tests
3. ✅ **Authentication**: Repository (21) + Service (26) = 47 tests
4. ✅ **Basic CRUD**: Repository (45) + Service (53) = 98 tests
   - Schools (11), Users (14), Students (10), Batches (18)
5. ✅ **Permissions**: Repository (46) + Service (46) = 92 tests
   - Permission management, role-based access, refresh tokens

**Total Coverage**: 412 tests across all components
- Normal cases: All CRUD operations
- Boundary cases: Min/max values, limits, empty inputs
- Edge cases: None values, Unicode, special characters, negative values

### Next Steps

Potential areas for enhancement:
1. **Batch Schedule Services**: Schedule management, time conflict validation
2. **Coach Services**: Assignment logic, multi-batch relationships
3. **Student Exercise Averages**: Calculation logic, aggregation
4. **Integration with UUID**: Update tests when ID migration happens

---

*Test Framework*: pytest 9.0.1  
*Python Version*: 3.12.12

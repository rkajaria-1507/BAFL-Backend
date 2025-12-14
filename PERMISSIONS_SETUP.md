# BAFL Permission System - Comprehensive Setup

## Overview
This document describes the comprehensive permission system implemented for the BAFL (sports management) backend.

## Permission Categories

### 1. User Management (15 permissions)
- `create_user`, `create_coach`, `create_admin`
- `delete_user`, `delete_coach`, `delete_admin`
- `view_all_users`, `edit_all_users`
- `view_own_profile`, `edit_own_profile`

### 2. Permission Management (3 permissions)
- `assign_permissions`, `revoke_permissions`, `view_permissions`

### 3. School Management (4 permissions)
- `school_create`, `school_view`, `school_edit`, `school_delete`

### 4. Coach Management (5 permissions)
- `coach_create`, `coach_view`, `coach_view_all`, `coach_edit`, `coach_delete`

### 5. Batch Management (5 permissions)
- `batch_create`, `batch_view`, `batch_view_all`, `batch_edit`, `batch_delete`

### 6. Student Management (5 permissions)
- `student_create`, `student_view`, `student_view_all`, `student_edit`, `student_delete`

### 7. Physical Assessment Management (10 permissions)
- `physical_sessions_view`, `physical_sessions_view_all`, `physical_sessions_edit`
- `physical_sessions_add`, `physical_sessions_delete`
- `physical_assessment_detail_view`, `physical_assessment_detail_edit`, `physical_assessment_detail_delete`
- `physical_level_mapping_view`, `physical_level_mapping_edit`

### 8. Archery Session Management (7 permissions)
- `archery_session_create`, `archery_session_view`, `archery_session_view_all`
- `archery_session_edit`, `archery_session_delete`
- `archery_result_view`, `archery_result_edit`, `archery_result_delete`

### 9. Archery Tournament Management (10 permissions)
- `archery_tournament_create`, `archery_tournament_view`, `archery_tournament_view_all`
- `archery_tournament_edit`, `archery_tournament_delete`
- `archery_tournament_category_create`, `archery_tournament_category_view`
- `archery_tournament_category_edit`, `archery_tournament_category_delete`
- `archery_tournament_result_view`, `archery_tournament_result_edit`, `archery_tournament_result_delete`

### 10. Reports & Analytics (3 permissions)
- `report_view`, `report_export`, `analytics_view`

## Total: 77 Permissions

## Role-Permission Mappings

### ADMIN Role (77 permissions)
- Full access to all features
- User and permission management
- Complete CRUD operations on all entities
- Reports and analytics with export capability

### COACH Role (28 permissions)
- Profile management
- View schools (read-only)
- Manage assigned batches and students
- Create and manage physical assessments for assigned students
- Create and manage archery sessions for assigned students
- View archery tournaments and participate
- View reports and analytics for own data

### USER Role (16 permissions)
- Basic profile management
- View-only access to schools, batches, students
- View physical assessments and results
- View archery sessions and tournaments
- View basic reports

## Key Features

### 1. Granular Permissions
- Separate permissions for create, view, edit, delete operations
- Distinction between viewing own data vs. all data (e.g., `batch_view` vs `batch_view_all`)

### 2. Role-Based Access Control
- Predefined permission sets for each role
- Custom permissions can be assigned on top of role permissions

### 3. Database-Backed Configuration
- Role-permission mappings stored in `role_permissions` table
- Permissions stored in `permissions` table
- User/Coach specific permissions in `user_permissions` table

## Files Modified/Created

1. **Created**: `src/utils/role_permissions_config.py`
   - Defines ROLE_PERMISSIONS mapping

2. **Updated**: `src/db/models/permission.py`
   - Extended PermissionType enum from 16 to 77 permissions

3. **Updated**: `src/db/models/role_permission.py`
   - Fixed data types (Integer)
   - Added unique constraint for role-permission pairs

## Next Steps

To apply these changes:

1. **Restart the application** - The permissions will be automatically created
2. **Run database migrations** if needed
3. **Verify permissions** by checking the `/api/v1/permissions/` endpoint

## Usage in Code

Permissions are checked using the `PermissionService`:

```python
from src.services.permission_service import PermissionService
from src.db.models.permission import PermissionType

# Check if user has permission
user_permissions = PermissionService.get_user_permissions(db, user)
if PermissionType.STUDENT_CREATE in user_permissions:
    # Allow student creation
    pass
```

## Notes

- Coaches have permission to edit batches and students, but typically limited to their assigned ones (enforced in business logic)
- The `_VIEW_ALL` permissions are reserved for admins to see all records across the system
- Regular view permissions are scoped to the user's context (e.g., coach sees only their batches)

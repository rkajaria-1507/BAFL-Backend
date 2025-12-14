"""
Role-based permission mappings configuration.

This module defines comprehensive permissions for the BAFL (sports management) system
and maps them to different user roles (ADMIN, USER, COACH).
"""
from src.db.models.permission import PermissionType
from src.db.models.user import UserRole


# Comprehensive role-permission mappings
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # ===== User Management =====
        PermissionType.CREATE_USER,
        PermissionType.CREATE_COACH,
        PermissionType.CREATE_ADMIN,
        PermissionType.DELETE_USER,
        PermissionType.DELETE_COACH,
        PermissionType.DELETE_ADMIN,
        PermissionType.VIEW_ALL_USERS,
        PermissionType.EDIT_ALL_USERS,
        PermissionType.VIEW_OWN_PROFILE,
        PermissionType.EDIT_OWN_PROFILE,
        
        # ===== Permission Management =====
        PermissionType.ASSIGN_PERMISSIONS,
        PermissionType.REVOKE_PERMISSIONS,
        PermissionType.VIEW_PERMISSIONS,
        
        # ===== School Management =====
        PermissionType.SCHOOL_CREATE,
        PermissionType.SCHOOL_VIEW,
        PermissionType.SCHOOL_EDIT,
        PermissionType.SCHOOL_DELETE,
        
        # ===== Coach Management =====
        PermissionType.COACH_CREATE,
        PermissionType.COACH_VIEW,
        PermissionType.COACH_VIEW_ALL,
        PermissionType.COACH_EDIT,
        PermissionType.COACH_DELETE,
        
        # ===== Batch Management =====
        PermissionType.BATCH_CREATE,
        PermissionType.BATCH_VIEW,
        PermissionType.BATCH_VIEW_ALL,
        PermissionType.BATCH_EDIT,
        PermissionType.BATCH_DELETE,
        
        # ===== Student Management =====
        PermissionType.STUDENT_CREATE,
        PermissionType.STUDENT_VIEW,
        PermissionType.STUDENT_VIEW_ALL,
        PermissionType.STUDENT_EDIT,
        PermissionType.STUDENT_DELETE,
        
        # ===== Physical Assessment Management =====
        PermissionType.PHYSICAL_SESSIONS_VIEW,
        PermissionType.PHYSICAL_SESSIONS_VIEW_ALL,
        PermissionType.PHYSICAL_SESSIONS_EDIT,
        PermissionType.PHYSICAL_SESSIONS_ADD,
        PermissionType.PHYSICAL_SESSIONS_DELETE,
        PermissionType.PHYSICAL_ASSESSMENT_DETAIL_VIEW,
        PermissionType.PHYSICAL_ASSESSMENT_DETAIL_EDIT,
        PermissionType.PHYSICAL_ASSESSMENT_DETAIL_DELETE,
        PermissionType.PHYSICAL_LEVEL_MAPPING_VIEW,
        PermissionType.PHYSICAL_LEVEL_MAPPING_EDIT,
        
        # ===== Archery Session Management =====
        PermissionType.ARCHERY_SESSION_CREATE,
        PermissionType.ARCHERY_SESSION_VIEW,
        PermissionType.ARCHERY_SESSION_VIEW_ALL,
        PermissionType.ARCHERY_SESSION_EDIT,
        PermissionType.ARCHERY_SESSION_DELETE,
        PermissionType.ARCHERY_RESULT_VIEW,
        PermissionType.ARCHERY_RESULT_EDIT,
        PermissionType.ARCHERY_RESULT_DELETE,
        
        # ===== Archery Tournament Management =====
        PermissionType.ARCHERY_TOURNAMENT_CREATE,
        PermissionType.ARCHERY_TOURNAMENT_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_VIEW_ALL,
        PermissionType.ARCHERY_TOURNAMENT_EDIT,
        PermissionType.ARCHERY_TOURNAMENT_DELETE,
        PermissionType.ARCHERY_TOURNAMENT_CATEGORY_CREATE,
        PermissionType.ARCHERY_TOURNAMENT_CATEGORY_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_CATEGORY_EDIT,
        PermissionType.ARCHERY_TOURNAMENT_CATEGORY_DELETE,
        PermissionType.ARCHERY_TOURNAMENT_RESULT_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_RESULT_EDIT,
        PermissionType.ARCHERY_TOURNAMENT_RESULT_DELETE,
        
        # ===== Reports & Analytics =====
        PermissionType.REPORT_VIEW,
        PermissionType.REPORT_EXPORT,
        PermissionType.ANALYTICS_VIEW,
    ],
    
    UserRole.COACH: [
        # ===== Profile Management =====
        PermissionType.VIEW_OWN_PROFILE,
        PermissionType.EDIT_OWN_PROFILE,
        
        # ===== School Management (View Only) =====
        PermissionType.SCHOOL_VIEW,
        
        # ===== Coach Management (Own Profile) =====
        PermissionType.COACH_VIEW,
        
        # ===== Batch Management (Assigned Batches) =====
        PermissionType.BATCH_VIEW,
        PermissionType.BATCH_EDIT,
        
        # ===== Student Management (Assigned Students) =====
        PermissionType.STUDENT_VIEW,
        PermissionType.STUDENT_EDIT,
        
        # ===== Physical Assessment Management (Own Batches/Students) =====
        PermissionType.PHYSICAL_SESSIONS_VIEW,
        PermissionType.PHYSICAL_SESSIONS_EDIT,
        PermissionType.PHYSICAL_SESSIONS_ADD,
        PermissionType.PHYSICAL_ASSESSMENT_DETAIL_VIEW,
        PermissionType.PHYSICAL_ASSESSMENT_DETAIL_EDIT,
        PermissionType.PHYSICAL_LEVEL_MAPPING_VIEW,
        
        # ===== Archery Session Management (Own Batches/Students) =====
        PermissionType.ARCHERY_SESSION_CREATE,
        PermissionType.ARCHERY_SESSION_VIEW,
        PermissionType.ARCHERY_SESSION_EDIT,
        PermissionType.ARCHERY_RESULT_VIEW,
        PermissionType.ARCHERY_RESULT_EDIT,
        
        # ===== Archery Tournament Management (View & Participate) =====
        PermissionType.ARCHERY_TOURNAMENT_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_CATEGORY_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_RESULT_VIEW,
        
        # ===== Reports & Analytics (Own Data) =====
        PermissionType.REPORT_VIEW,
        PermissionType.ANALYTICS_VIEW,
    ],
    
    UserRole.USER: [
        # ===== Basic Profile Access =====
        PermissionType.VIEW_OWN_PROFILE,
        PermissionType.EDIT_OWN_PROFILE,
        
        # ===== View-Only Access =====
        PermissionType.SCHOOL_VIEW,
        PermissionType.BATCH_VIEW,
        PermissionType.STUDENT_VIEW,
        
        # ===== Limited Assessment Viewing =====
        PermissionType.PHYSICAL_SESSIONS_VIEW,
        PermissionType.PHYSICAL_ASSESSMENT_DETAIL_VIEW,
        PermissionType.PHYSICAL_LEVEL_MAPPING_VIEW,
        
        # ===== Limited Archery Viewing =====
        PermissionType.ARCHERY_SESSION_VIEW,
        PermissionType.ARCHERY_RESULT_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_CATEGORY_VIEW,
        PermissionType.ARCHERY_TOURNAMENT_RESULT_VIEW,
        
        # ===== Basic Reports =====
        PermissionType.REPORT_VIEW,
    ],
}

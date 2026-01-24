"""
API v1 router aggregation.
"""
from fastapi import APIRouter

from src.api.v1.endpoints import (
	archery,
	archery_tournaments,
	assessments,
	attendance,
	auth,
	batches,
	coaches,
	permissions,
	schools,
	students,
	users,
)


# Create main v1 router
api_v1_router = APIRouter(prefix="/v1")

# Include all endpoint routers
api_v1_router.include_router(auth.router)
api_v1_router.include_router(permissions.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(coaches.router)
api_v1_router.include_router(students.router)
api_v1_router.include_router(schools.router)
api_v1_router.include_router(batches.router)
api_v1_router.include_router(assessments.router)
api_v1_router.include_router(archery.router)
api_v1_router.include_router(archery_tournaments.router)
api_v1_router.include_router(attendance.router)

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.db.models.coach import Coach
from src.db.models.user import User, UserRole
from src.db.repositories.coach_repository import CoachRepository


def get_coach_profile_or_403(current_user: User, db: Session) -> Coach:
    """Ensure the current user has an associated coach profile and return it."""
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach access required")

    coach_profile = getattr(current_user, "coach_profile", None)
    if coach_profile:
        return coach_profile

    coach_profile = CoachRepository.get_by_username(db, current_user.username)
    if not coach_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach profile not found")

    setattr(current_user, "coach_profile", coach_profile)
    return coach_profile

"""
Script to calculate and populate student exercise averages.
This should be run after populate_data.py to calculate averages
from the physical assessment sessions.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.db.database import SessionLocal
from src.db.repositories.student_exercise_average_repository import StudentExerciseAverageRepository
from src.db.models.physical_assessment import PhysicalAssessmentSession
from src.core.logging import api_logger


def calculate_all_averages():
    """Calculate averages for all physical assessment sessions."""
    api_logger.info("Starting calculation of student exercise averages...")
    
    db = SessionLocal()
    try:
        avg_repo = StudentExerciseAverageRepository(db)
        
        # Get all physical assessment sessions
        sessions = db.query(PhysicalAssessmentSession).all()
        
        if not sessions:
            api_logger.warning("No physical assessment sessions found. Please run populate_data.py first.")
            return
        
        api_logger.info(f"Found {len(sessions)} physical assessment sessions")
        
        total_updated = 0
        for session in sessions:
            api_logger.info(
                f"Processing session {session.id} (Batch: {session.batch_id}, "
                f"School: {session.school_id}, Date: {session.date_of_session})"
            )
            
            updated_count = avg_repo.update_averages_for_session(
                session_id=session.id,
                batch_id=session.batch_id,
                school_id=session.school_id
            )
            
            total_updated += updated_count
            api_logger.info(f"  Updated {updated_count} exercise average records")
        
        db.commit()
        
        api_logger.info("=" * 50)
        api_logger.info("Average calculation completed successfully!")
        api_logger.info("=" * 50)
        api_logger.info(f"Total sessions processed: {len(sessions)}")
        api_logger.info(f"Total average records created/updated: {total_updated}")
        api_logger.info("=" * 50)
        
    except Exception as e:
        api_logger.error(f"Error calculating averages: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Calculating student exercise averages from physical assessment data...")
    calculate_all_averages()
    print("\nDone! Exercise averages have been calculated and stored.")

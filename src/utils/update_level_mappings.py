"""
Update existing exercise level mappings.
Use this script when you need to modify level criteria after the initial seed.

Usage: python -m src.utils.update_level_mappings
"""

from sqlalchemy.orm import Session
from src.db.database import SessionLocal
from src.db.models.exercise_level_mapping import ExerciseLevelMapping


def convert_plank_data_to_minutes(db: Session):
    """
    Convert existing plank data in physical_assessment_details from seconds to minutes.
    """
    from src.db.models.physical_assessment import PhysicalAssessmentDetail
    
    print("Converting plank data from seconds to minutes...")
    
    # Get all records with non-zero plank values
    records = db.query(PhysicalAssessmentDetail).filter(
        PhysicalAssessmentDetail.plank > 0
    ).all()
    
    count = 0
    for record in records:
        # Convert seconds to minutes
        record.plank = record.plank / 60.0
        count += 1
    
    db.commit()
    print(f"Converted {count} plank records from seconds to minutes.")


def update_level_mappings(db: Session):
    """
    Update existing level mappings in the database.
    Modify this function when you need to change level criteria.
    """
    
    print("Updating exercise level mappings...")
    
    # Update plank from seconds to minutes (divide by 60)
    plank_updates = [
        {"level": 1, "min": 0, "max": 0.67, "unit": "min"},      # 0-40 sec -> 0-0.67 min
        {"level": 2, "min": 0.68, "max": 1.33, "unit": "min"},   # 41-80 sec -> 0.68-1.33 min
        {"level": 3, "min": 1.34, "max": 2.0, "unit": "min"},    # 81-120 sec -> 1.34-2.0 min
        {"level": 4, "min": 2.01, "max": 2.67, "unit": "min"},   # 121-160 sec -> 2.01-2.67 min
        {"level": 5, "min": 2.68, "max": 3.33, "unit": "min"},   # 161-200 sec -> 2.68-3.33 min
        {"level": 6, "min": 3.34, "max": 4.0, "unit": "min"},    # 201-240 sec -> 3.34-4.0 min
        {"level": 7, "min": 4.01, "max": 166.65, "unit": "min"}, # 241+ sec -> 4.01+ min
    ]
    
    for update in plank_updates:
        db.query(ExerciseLevelMapping).filter(
            ExerciseLevelMapping.exercise_name == "plank",
            ExerciseLevelMapping.level == update["level"]
        ).update({
            "min_score": update["min"],
            "max_score": update["max"],
            "unit": update["unit"]
        })
    
    db.commit()
    
    print(f"Updated {len(plank_updates)} plank level mappings from seconds to minutes.")


def recalculate_all_levels(db: Session):
    """
    After updating level mappings, recalculate all student levels.
    This ensures existing average records get updated with new level criteria.
    """
    from src.db.models.student_exercise_average import StudentExerciseAverage
    from src.db.repositories.student_exercise_average_repository import StudentExerciseAverageRepository
    
    print("\nRecalculating all student levels based on updated criteria...")
    
    avg_repo = StudentExerciseAverageRepository(db)
    averages = db.query(StudentExerciseAverage).all()
    
    updated_count = 0
    for avg_record in averages:
        # Get new level based on existing average score
        level_info = avg_repo.get_level_for_score(
            avg_record.exercise_name,
            avg_record.average_score
        )
        
        if level_info:
            avg_record.current_level = level_info["level"]
            avg_record.level_score = level_info["level_score"]
            avg_record.level_description = level_info["level_description"]
            updated_count += 1
    
    db.commit()
    print(f"Updated levels for {updated_count} student-exercise records.")


def main():
    """Main function to run the update script."""
    db = SessionLocal()
    try:
        # Step 1: Update level mappings to use minute-based ranges
        update_level_mappings(db)
        
        # Step 2: Recalculate all student levels (no data yet, but safe to run)
        recalculate_all_levels(db)
        
        print("\n✅ All updates completed successfully!")
        
    except Exception as e:
        print(f"Error updating data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

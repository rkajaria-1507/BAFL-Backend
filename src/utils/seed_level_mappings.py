"""
Seed data for exercise level mappings.
This script populates the exercise_level_mappings table with the fitness assessment criteria.

Run this script after creating the database tables to populate the level mapping data.
Usage: python src/utils/seed_level_mappings.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.db.database import SessionLocal, engine
from src.db.models.exercise_level_mapping import ExerciseLevelMapping
from src.db.database import Base


def seed_exercise_level_mappings(db: Session):
    """
    Seed the exercise_level_mappings table with data for all exercises.
    """
    
    # Check if data already exists
    existing_count = db.query(ExerciseLevelMapping).count()
    if existing_count > 0:
        print(f"Level mappings already exist ({existing_count} records). Skipping seed.")
        return
    
    # Define level descriptions and scores
    level_info = {
        1: {"score": 2, "description": "work harder"},
        2: {"score": 4, "description": "must improve"},
        3: {"score": 6, "description": "can do better"},
        4: {"score": 7, "description": "good"},
        5: {"score": 8, "description": "very good"},
        6: {"score": 9, "description": "athletic"},
        7: {"score": 10, "description": "sport fit"}
    }
    
    mappings = []
    
    # 1. CURL UP (count) - Higher is better
    mappings.extend([
        {"exercise": "curl_up", "level": 1, "min": 0, "max": 14, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 2, "min": 14, "max": 15, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 3, "min": 15, "max": 20, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 4, "min": 20, "max": 21, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 5, "min": 21, "max": 23, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 6, "min": 23, "max": 24, "higher_better": 1, "unit": "count"},
        {"exercise": "curl_up", "level": 7, "min": 24, "max": 999, "higher_better": 1, "unit": "count"},
    ])
    
    # 2. PUSH UP (count) - Higher is better
    mappings.extend([
        {"exercise": "push_up", "level": 1, "min": 0, "max": 7, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 2, "min": 7, "max": 8, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 3, "min": 8, "max": 9, "higher_better": 1, "unit": "count"},  # Assuming L3 is 9 reps
        {"exercise": "push_up", "level": 4, "min": 9, "max": 10, "higher_better": 1, "unit": "count"},  # Assuming L4 is 10 reps
        {"exercise": "push_up", "level": 5, "min": 10, "max": 11, "higher_better": 1, "unit": "count"},  # Assuming L5 is 11 reps
        {"exercise": "push_up", "level": 6, "min": 11, "max": 12, "higher_better": 1, "unit": "count"},
        {"exercise": "push_up", "level": 7, "min": 12, "max": 999, "higher_better": 1, "unit": "count"},
    ])
    
    # 3. SIT AND REACH (cm) - Higher is better
    mappings.extend([
        {"exercise": "sit_and_reach", "level": 1, "min": 0, "max": 15.8, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 2, "min": 15.8, "max": 19.7, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 3, "min": 19.7, "max": 23.1, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 4, "min": 23.1, "max": 24.9, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 5, "min": 24.9, "max": 27.1, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 6, "min": 27.1, "max": 32.5, "higher_better": 1, "unit": "cm"},
        {"exercise": "sit_and_reach", "level": 7, "min": 32.5, "max": 999, "higher_better": 1, "unit": "cm"},
    ])
    
    # 4. 600M WALK (minutes) - Lower is better
    mappings.extend([
        {"exercise": "walk_600m", "level": 1, "min": 3.24, "max": 999, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 2, "min": 3.14, "max": 3.24, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 3, "min": 3.07, "max": 3.14, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 4, "min": 3.04, "max": 3.07, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 5, "min": 3.01, "max": 3.04, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 6, "min": 3.00, "max": 3.01, "higher_better": 0, "unit": "min"},
        {"exercise": "walk_600m", "level": 7, "min": 0, "max": 3.00, "higher_better": 0, "unit": "min"},
    ])
    
    # 5. 50M DASH (seconds) - Lower is better
    mappings.extend([
        {"exercise": "dash_50m", "level": 1, "min": 9.5, "max": 999, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 2, "min": 9.0, "max": 9.5, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 3, "min": 8.6, "max": 9.0, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 4, "min": 8.4, "max": 8.6, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 5, "min": 8.2, "max": 8.4, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 6, "min": 8.0, "max": 8.2, "higher_better": 0, "unit": "sec"},
        {"exercise": "dash_50m", "level": 7, "min": 0, "max": 8.0, "higher_better": 0, "unit": "sec"},
    ])
    
    # 6. BOW HOLD (seconds) - Higher is better
    mappings.extend([
        {"exercise": "bow_hold", "level": 1, "min": 0, "max": 40, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 2, "min": 40, "max": 50, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 3, "min": 50, "max": 60, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 4, "min": 60, "max": 70, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 5, "min": 70, "max": 80, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 6, "min": 80, "max": 90, "higher_better": 1, "unit": "sec"},
        {"exercise": "bow_hold", "level": 7, "min": 90, "max": 9999, "higher_better": 1, "unit": "sec"},
    ])
    
    # 7. PLANK (minutes) - Higher is better
    mappings.extend([
        {"exercise": "plank", "level": 1, "min": 0, "max": 0.67, "higher_better": 1, "unit": "min"},      # 0-40 sec
        {"exercise": "plank", "level": 2, "min": 0.67, "max": 1.33, "higher_better": 1, "unit": "min"},   # 41-80 sec
        {"exercise": "plank", "level": 3, "min": 1.33, "max": 2.0, "higher_better": 1, "unit": "min"},    # 81-120 sec
        {"exercise": "plank", "level": 4, "min": 2.0, "max": 2.67, "higher_better": 1, "unit": "min"},   # 121-160 sec
        {"exercise": "plank", "level": 5, "min": 2.67, "max": 3.33, "higher_better": 1, "unit": "min"},   # 161-200 sec
        {"exercise": "plank", "level": 6, "min": 3.33, "max": 4.0, "higher_better": 1, "unit": "min"},    # 201-240 sec
        {"exercise": "plank", "level": 7, "min": 4.0, "max": 166.65, "higher_better": 1, "unit": "min"}, # 241+ sec
    ])
    
    # Create ExerciseLevelMapping objects
    for mapping in mappings:
        level_data = level_info[mapping["level"]]
        db_mapping = ExerciseLevelMapping(
            exercise_name=mapping["exercise"],
            level=mapping["level"],
            min_score=mapping["min"],
            max_score=mapping["max"],
            level_score=level_data["score"],
            level_description=level_data["description"],
            is_higher_better=mapping["higher_better"],
            unit=mapping["unit"]
        )
        db.add(db_mapping)
    
    db.commit()
    print(f"Successfully seeded {len(mappings)} exercise level mappings!")


def main():
    """Main function to run the seed script."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    try:
        seed_exercise_level_mappings(db)
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

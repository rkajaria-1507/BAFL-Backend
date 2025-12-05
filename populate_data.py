"""
Script to populate the database with initial test data.
"""
from datetime import time
from sqlalchemy.orm import Session
from src.db.database import SessionLocal, init_database
from src.db.models.user import User, UserRole
from src.db.models.school import School
from src.db.models.coach import Coach
from src.db.models.batch import Batch
from src.db.models.batch_schedule import BatchSchedule
from src.db.models.coach_batch import CoachBatch
from src.db.models.coach_school import CoachSchool
from src.db.models.student import Student
from src.core.security import PasswordHandler
from src.core.logging import api_logger


def populate_database():
    """Populate the database with test data."""
    api_logger.info("Starting database population...")
    
    db = SessionLocal()
    try:
        # Create Schools
        api_logger.info("Creating schools...")
        avasara = School(
            name="Avasara Academy",
            address="Pune, Maharashtra"
        )
        acharya = School(
            name="Acharya Academy",
            address="Bangalore, Karnataka"
        )
        db.add_all([avasara, acharya])
        db.commit()
        db.refresh(avasara)
        db.refresh(acharya)
        api_logger.info(f"Created schools: {avasara.name} (ID: {avasara.id}), {acharya.name} (ID: {acharya.id})")
        
        # Create Coaches
        api_logger.info("Creating coaches...")
        coach1 = Coach(
            name="Coach One",
            username="coach1",
            password=PasswordHandler.hash("password1"),
            is_active=True
        )
        coach2 = Coach(
            name="Coach Two",
            username="coach2",
            password=PasswordHandler.hash("password2"),
            is_active=True
        )
        db.add_all([coach1, coach2])
        db.commit()
        db.refresh(coach1)
        db.refresh(coach2)
        api_logger.info(f"Created coaches: {coach1.name} (ID: {coach1.id}), {coach2.name} (ID: {coach2.id})")
        
        # Assign coaches to schools
        api_logger.info("Assigning coaches to schools...")
        coach_school_1 = CoachSchool(coach_id=coach1.id, school_id=avasara.id)
        coach_school_2 = CoachSchool(coach_id=coach2.id, school_id=acharya.id)
        db.add_all([coach_school_1, coach_school_2])
        db.commit()
        
        # Create Batches for Avasara Academy
        api_logger.info("Creating batches for Avasara Academy...")
        avasara_u14 = Batch(
            school_id=avasara.id,
            batch_name="U14"
        )
        avasara_u17 = Batch(
            school_id=avasara.id,
            batch_name="U17"
        )
        db.add_all([avasara_u14, avasara_u17])
        db.commit()
        db.refresh(avasara_u14)
        db.refresh(avasara_u17)
        
        # Create Batches for Acharya Academy
        api_logger.info("Creating batches for Acharya Academy...")
        acharya_u14 = Batch(
            school_id=acharya.id,
            batch_name="U14"
        )
        acharya_u17 = Batch(
            school_id=acharya.id,
            batch_name="U17"
        )
        db.add_all([acharya_u14, acharya_u17])
        db.commit()
        db.refresh(acharya_u14)
        db.refresh(acharya_u17)
        api_logger.info("Created all batches")
        
        # Assign coach1 to Avasara batches
        api_logger.info("Assigning coaches to batches...")
        coach_batch_1 = CoachBatch(coach_id=coach1.id, batch_id=avasara_u14.id)
        coach_batch_2 = CoachBatch(coach_id=coach1.id, batch_id=avasara_u17.id)
        coach_batch_3 = CoachBatch(coach_id=coach2.id, batch_id=acharya_u14.id)
        coach_batch_4 = CoachBatch(coach_id=coach2.id, batch_id=acharya_u17.id)
        db.add_all([coach_batch_1, coach_batch_2, coach_batch_3, coach_batch_4])
        db.commit()
        
        # Add batch schedules (optional but good to have)
        api_logger.info("Adding batch schedules...")
        schedules = [
            BatchSchedule(batch_id=avasara_u14.id, day_of_week=1, start_time=time(15, 0), end_time=time(17, 0)),
            BatchSchedule(batch_id=avasara_u14.id, day_of_week=3, start_time=time(15, 0), end_time=time(17, 0)),
            BatchSchedule(batch_id=avasara_u17.id, day_of_week=2, start_time=time(16, 0), end_time=time(18, 0)),
            BatchSchedule(batch_id=avasara_u17.id, day_of_week=4, start_time=time(16, 0), end_time=time(18, 0)),
            BatchSchedule(batch_id=acharya_u14.id, day_of_week=1, start_time=time(15, 0), end_time=time(17, 0)),
            BatchSchedule(batch_id=acharya_u14.id, day_of_week=3, start_time=time(15, 0), end_time=time(17, 0)),
            BatchSchedule(batch_id=acharya_u17.id, day_of_week=2, start_time=time(16, 0), end_time=time(18, 0)),
            BatchSchedule(batch_id=acharya_u17.id, day_of_week=4, start_time=time(16, 0), end_time=time(18, 0)),
        ]
        db.add_all(schedules)
        db.commit()
        
        # Create Students for Avasara U14
        api_logger.info("Creating students for Avasara U14...")
        avasara_u14_students = [
            Student(name="Priya Sharma", age=13, batch_id=avasara_u14.id),
            Student(name="Rahul Verma", age=14, batch_id=avasara_u14.id),
            Student(name="Ananya Patel", age=12, batch_id=avasara_u14.id),
            Student(name="Arjun Singh", age=13, batch_id=avasara_u14.id),
            Student(name="Meera Reddy", age=14, batch_id=avasara_u14.id),
        ]
        
        # Create Students for Avasara U17
        api_logger.info("Creating students for Avasara U17...")
        avasara_u17_students = [
            Student(name="Vikram Kumar", age=16, batch_id=avasara_u17.id),
            Student(name="Neha Gupta", age=17, batch_id=avasara_u17.id),
            Student(name="Rohan Desai", age=15, batch_id=avasara_u17.id),
            Student(name="Kavya Nair", age=16, batch_id=avasara_u17.id),
            Student(name="Aditya Joshi", age=17, batch_id=avasara_u17.id),
        ]
        
        # Create Students for Acharya U14
        api_logger.info("Creating students for Acharya U14...")
        acharya_u14_students = [
            Student(name="Sneha Iyer", age=13, batch_id=acharya_u14.id),
            Student(name="Karan Mehta", age=14, batch_id=acharya_u14.id),
            Student(name="Ishaan Kapoor", age=12, batch_id=acharya_u14.id),
            Student(name="Diya Malhotra", age=13, batch_id=acharya_u14.id),
        ]
        
        # Create Students for Acharya U17
        api_logger.info("Creating students for Acharya U17...")
        acharya_u17_students = [
            Student(name="Siddharth Rao", age=16, batch_id=acharya_u17.id),
            Student(name="Aarav Saxena", age=17, batch_id=acharya_u17.id),
            Student(name="Tanvi Shah", age=15, batch_id=acharya_u17.id),
            Student(name="Riya Bhatt", age=16, batch_id=acharya_u17.id),
        ]
        
        all_students = (
            avasara_u14_students + 
            avasara_u17_students + 
            acharya_u14_students + 
            acharya_u17_students
        )
        db.add_all(all_students)
        db.commit()
        api_logger.info(f"Created {len(all_students)} students")
        
        api_logger.info("=" * 50)
        api_logger.info("Database population completed successfully!")
        api_logger.info("=" * 50)
        api_logger.info("\nSummary:")
        api_logger.info(f"Schools: 2 (Avasara Academy, Acharya Academy)")
        api_logger.info(f"Coaches: 2")
        api_logger.info(f"  - coach1 (password: password1) -> Avasara Academy")
        api_logger.info(f"  - coach2 (password: password2) -> Acharya Academy")
        api_logger.info(f"Batches: 4 (U14 and U17 for each school)")
        api_logger.info(f"Students: {len(all_students)}")
        api_logger.info("=" * 50)
        
    except Exception as e:
        api_logger.error(f"Error populating database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database and populating with test data...")
    init_database()
    populate_database()
    print("\nDone! You can now start the application.")

"""
Script to populate the database with initial test data.
"""
from datetime import time, date, timedelta
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
from src.db.models.physical_assessment import PhysicalAssessmentSession, PhysicalAssessmentDetail
from src.db.models.archery import ArcherySession, ArcheryResult
from src.db.models.archery_tournament import ArcheryTournamentCategory, ArcheryTournamentSession, ArcheryTournamentResult
from src.core.security import PasswordHandler
from src.core.logging import api_logger
import random


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
        
        # Refresh all students to get their IDs
        for student in all_students:
            db.refresh(student)
        
        api_logger.info(f"Created {len(all_students)} students")
        
        # Create Physical Assessment Sessions
        api_logger.info("Creating physical assessment sessions...")
        today = date.today()
        
        # Physical assessment for Avasara U14 - Session 1
        pa_session_1 = PhysicalAssessmentSession(
            batch_id=avasara_u14.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=60),
            student_count=len(avasara_u14_students)
        )
        
        # Physical assessment for Avasara U14 - Session 2
        pa_session_2 = PhysicalAssessmentSession(
            batch_id=avasara_u14.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=30),
            student_count=len(avasara_u14_students)
        )
        
        # Physical assessment for Avasara U17 - Session 1
        pa_session_3 = PhysicalAssessmentSession(
            batch_id=avasara_u17.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=58),
            student_count=len(avasara_u17_students)
        )
        
        # Physical assessment for Avasara U17 - Session 2
        pa_session_4 = PhysicalAssessmentSession(
            batch_id=avasara_u17.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=28),
            student_count=len(avasara_u17_students)
        )
        
        # Physical assessment for Acharya U14 - Session 1
        pa_session_5 = PhysicalAssessmentSession(
            batch_id=acharya_u14.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=55),
            student_count=len(acharya_u14_students)
        )
        
        # Physical assessment for Acharya U14 - Session 2
        pa_session_6 = PhysicalAssessmentSession(
            batch_id=acharya_u14.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=25),
            student_count=len(acharya_u14_students)
        )
        
        # Physical assessment for Acharya U17 - Session 1
        pa_session_7 = PhysicalAssessmentSession(
            batch_id=acharya_u17.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=53),
            student_count=len(acharya_u17_students)
        )
        
        # Physical assessment for Acharya U17 - Session 2
        pa_session_8 = PhysicalAssessmentSession(
            batch_id=acharya_u17.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=23),
            student_count=len(acharya_u17_students)
        )
        
        db.add_all([pa_session_1, pa_session_2, pa_session_3, pa_session_4, pa_session_5, pa_session_6, pa_session_7, pa_session_8])
        db.commit()
        for session in [pa_session_1, pa_session_2, pa_session_3, pa_session_4, pa_session_5, pa_session_6, pa_session_7, pa_session_8]:
            db.refresh(session)
        api_logger.info("Created 8 physical assessment sessions (2 per batch)")
        
        # Create Physical Assessment Details (results for students)
        api_logger.info("Creating physical assessment details...")
        pa_details = []
        
        # Results for Avasara U14 students - Session 1
        for student in avasara_u14_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_1.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(15, 40),
                push_up=random.randint(10, 30),
                sit_and_reach=random.uniform(10.0, 25.0),
                walk_600m=random.uniform(3.5, 5.5),
                dash_50m=random.uniform(7.0, 10.0),
                bow_hold=random.uniform(30.0, 90.0),
                plank=random.uniform(30.0, 120.0),
                is_present=True
            ))
        
        # Results for Avasara U14 students - Session 2 (improved scores)
        for student in avasara_u14_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_2.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(20, 45),
                push_up=random.randint(15, 35),
                sit_and_reach=random.uniform(12.0, 27.0),
                walk_600m=random.uniform(3.3, 5.3),
                dash_50m=random.uniform(6.8, 9.8),
                bow_hold=random.uniform(35.0, 95.0),
                plank=random.uniform(35.0, 125.0),
                is_present=True
            ))
        
        # Results for Avasara U17 students - Session 1
        for student in avasara_u17_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_3.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(20, 50),
                push_up=random.randint(15, 40),
                sit_and_reach=random.uniform(12.0, 30.0),
                walk_600m=random.uniform(3.0, 5.0),
                dash_50m=random.uniform(6.5, 9.5),
                bow_hold=random.uniform(40.0, 100.0),
                plank=random.uniform(40.0, 150.0),
                is_present=True
            ))
        
        # Results for Avasara U17 students - Session 2 (improved scores)
        for student in avasara_u17_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_4.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(25, 55),
                push_up=random.randint(20, 45),
                sit_and_reach=random.uniform(14.0, 32.0),
                walk_600m=random.uniform(2.8, 4.8),
                dash_50m=random.uniform(6.3, 9.3),
                bow_hold=random.uniform(45.0, 105.0),
                plank=random.uniform(45.0, 155.0),
                is_present=True
            ))
        
        # Results for Acharya U14 students - Session 1
        for student in acharya_u14_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_5.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(15, 40),
                push_up=random.randint(10, 30),
                sit_and_reach=random.uniform(10.0, 25.0),
                walk_600m=random.uniform(3.5, 5.5),
                dash_50m=random.uniform(7.0, 10.0),
                bow_hold=random.uniform(30.0, 90.0),
                plank=random.uniform(30.0, 120.0),
                is_present=True
            ))
        
        # Results for Acharya U14 students - Session 2 (improved scores)
        for student in acharya_u14_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_6.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(20, 45),
                push_up=random.randint(15, 35),
                sit_and_reach=random.uniform(12.0, 27.0),
                walk_600m=random.uniform(3.3, 5.3),
                dash_50m=random.uniform(6.8, 9.8),
                bow_hold=random.uniform(35.0, 95.0),
                plank=random.uniform(35.0, 125.0),
                is_present=True
            ))
        
        # Results for Acharya U17 students - Session 1
        for student in acharya_u17_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_7.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(20, 50),
                push_up=random.randint(15, 40),
                sit_and_reach=random.uniform(12.0, 30.0),
                walk_600m=random.uniform(3.0, 5.0),
                dash_50m=random.uniform(6.5, 9.5),
                bow_hold=random.uniform(40.0, 100.0),
                plank=random.uniform(40.0, 150.0),
                is_present=True
            ))
        
        # Results for Acharya U17 students - Session 2 (improved scores)
        for student in acharya_u17_students:
            pa_details.append(PhysicalAssessmentDetail(
                session_id=pa_session_8.id,
                student_id=student.id,
                discipline="Archery",
                curl_up=random.randint(25, 55),
                push_up=random.randint(20, 45),
                sit_and_reach=random.uniform(14.0, 32.0),
                walk_600m=random.uniform(2.8, 4.8),
                dash_50m=random.uniform(6.3, 9.3),
                bow_hold=random.uniform(45.0, 105.0),
                plank=random.uniform(45.0, 155.0),
                is_present=True
            ))
        
        db.add_all(pa_details)
        db.commit()
        api_logger.info(f"Created {len(pa_details)} physical assessment details")
        
        # Create Archery Sessions
        api_logger.info("Creating archery sessions...")
        
        # Archery sessions for Avasara U14 - Session 1
        archery_session_1 = ArcherySession(
            batch_id=avasara_u14.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=20),
            distance=18.0
        )
        
        # Archery sessions for Avasara U14 - Session 2
        archery_session_2 = ArcherySession(
            batch_id=avasara_u14.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=13),
            distance=18.0
        )
        
        # Archery sessions for Avasara U17 - Session 1
        archery_session_3 = ArcherySession(
            batch_id=avasara_u17.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=18),
            distance=30.0
        )
        
        # Archery sessions for Avasara U17 - Session 2
        archery_session_4 = ArcherySession(
            batch_id=avasara_u17.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            date_of_session=today - timedelta(days=11),
            distance=30.0
        )
        
        # Archery sessions for Acharya U14 - Session 1
        archery_session_5 = ArcherySession(
            batch_id=acharya_u14.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=15),
            distance=18.0
        )
        
        # Archery sessions for Acharya U14 - Session 2
        archery_session_6 = ArcherySession(
            batch_id=acharya_u14.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=8),
            distance=18.0
        )
        
        # Archery sessions for Acharya U17 - Session 1
        archery_session_7 = ArcherySession(
            batch_id=acharya_u17.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=12),
            distance=30.0
        )
        
        # Archery sessions for Acharya U17 - Session 2
        archery_session_8 = ArcherySession(
            batch_id=acharya_u17.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            date_of_session=today - timedelta(days=5),
            distance=30.0
        )
        
        db.add_all([archery_session_1, archery_session_2, archery_session_3, archery_session_4, 
                    archery_session_5, archery_session_6, archery_session_7, archery_session_8])
        db.commit()
        for session in [archery_session_1, archery_session_2, archery_session_3, archery_session_4,
                        archery_session_5, archery_session_6, archery_session_7, archery_session_8]:
            db.refresh(session)
        api_logger.info("Created 8 archery sessions (2 per batch)")
        
        # Create Archery Results
        api_logger.info("Creating archery results...")
        archery_results = []
        
        # For each archery session, create results for students
        # Session 1: Avasara U14
        for student in avasara_u14_students:
            for round_num in range(1, 4):  # 3 rounds
                for arrow_num in range(1, 7):  # 6 arrows per round
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_1.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(5, 10),
                        max_score=10
                    ))
        
        # Session 2: Avasara U14
        for student in avasara_u14_students:
            for round_num in range(1, 4):
                for arrow_num in range(1, 7):
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_2.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(5, 10),
                        max_score=10
                    ))
        
        # Session 3: Avasara U17
        for student in avasara_u17_students:
            for round_num in range(1, 4):
                for arrow_num in range(1, 7):
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_3.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(6, 10),
                        max_score=10
                    ))
        
        # Session 4: Avasara U17
        for student in avasara_u17_students:
            for round_num in range(1, 4):
                for arrow_num in range(1, 7):
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_4.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(6, 10),
                        max_score=10
                    ))
        
        # Session 5: Acharya U14
        for student in acharya_u14_students:
            for round_num in range(1, 4):
                for arrow_num in range(1, 7):
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_5.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(5, 10),
                        max_score=10
                    ))
        
        # Session 6: Acharya U14
        for student in acharya_u14_students:
            for round_num in range(1, 4):
                for arrow_num in range(1, 7):
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_6.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(5, 10),
                        max_score=10
                    ))
        
        # Session 7: Acharya U17
        for student in acharya_u17_students:
            for round_num in range(1, 4):
                for arrow_num in range(1, 7):
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_7.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(6, 10),
                        max_score=10
                    ))
        
        # Session 8: Acharya U17
        for student in acharya_u17_students:
            for round_num in range(1, 4):
                for arrow_num in range(1, 7):
                    archery_results.append(ArcheryResult(
                        session_id=archery_session_8.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(6, 10),
                        max_score=10
                    ))
        
        db.add_all(archery_results)
        db.commit()
        api_logger.info(f"Created {len(archery_results)} archery results")
        
        # Create Archery Tournament Categories
        api_logger.info("Creating archery tournament categories...")
        categories = [
            ArcheryTournamentCategory(name="U14 Girls", description="Under 14 Girls Category"),
            ArcheryTournamentCategory(name="U14 Boys", description="Under 14 Boys Category"),
            ArcheryTournamentCategory(name="U17 Girls", description="Under 17 Girls Category"),
            ArcheryTournamentCategory(name="U17 Boys", description="Under 17 Boys Category"),
        ]
        db.add_all(categories)
        db.commit()
        for cat in categories:
            db.refresh(cat)
        api_logger.info("Created 4 tournament categories")
        
        # Create Archery Tournament Sessions
        api_logger.info("Creating archery tournament sessions...")
        
        # Tournament 1: State Championship for Avasara U14
        tournament_1 = ArcheryTournamentSession(
            batch_id=avasara_u14.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            category_id=categories[0].id,  # U14 Girls
            tournament_name="Maharashtra State Archery Championship",
            tournament_location="Pune, Maharashtra",
            category_name_snapshot="U14 Girls",
            date_of_session=today - timedelta(days=10),
            distance=18.0
        )
        
        # Tournament 2: Inter-School Tournament for Avasara U17
        tournament_2 = ArcheryTournamentSession(
            batch_id=avasara_u17.id,
            coach_id=coach1.id,
            school_id=avasara.id,
            category_id=categories[2].id,  # U17 Girls
            tournament_name="National Inter-School Archery Tournament",
            tournament_location="Mumbai, Maharashtra",
            category_name_snapshot="U17 Girls",
            date_of_session=today - timedelta(days=7),
            distance=30.0
        )
        
        # Tournament 3: Regional Championship for Acharya U14
        tournament_3 = ArcheryTournamentSession(
            batch_id=acharya_u14.id,
            coach_id=coach2.id,
            school_id=acharya.id,
            category_id=categories[1].id,  # U14 Boys
            tournament_name="South Zone Archery Championship",
            tournament_location="Bangalore, Karnataka",
            category_name_snapshot="U14 Boys",
            date_of_session=today - timedelta(days=5),
            distance=18.0
        )
        
        db.add_all([tournament_1, tournament_2, tournament_3])
        db.commit()
        for tournament in [tournament_1, tournament_2, tournament_3]:
            db.refresh(tournament)
        api_logger.info("Created 3 archery tournament sessions")
        
        # Create Archery Tournament Results
        api_logger.info("Creating archery tournament results...")
        tournament_results = []
        
        # Tournament 1: Avasara U14 (first 3 students participate)
        for student in avasara_u14_students[:3]:
            for round_num in range(1, 5):  # 4 rounds in tournament
                for arrow_num in range(1, 7):  # 6 arrows per round
                    tournament_results.append(ArcheryTournamentResult(
                        session_id=tournament_1.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(6, 10),
                        max_score=10
                    ))
        
        # Tournament 2: Avasara U17 (first 4 students participate)
        for student in avasara_u17_students[:4]:
            for round_num in range(1, 5):
                for arrow_num in range(1, 7):
                    tournament_results.append(ArcheryTournamentResult(
                        session_id=tournament_2.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(7, 10),
                        max_score=10
                    ))
        
        # Tournament 3: Acharya U14 (3 students participate)
        for student in acharya_u14_students[:3]:
            for round_num in range(1, 5):
                for arrow_num in range(1, 7):
                    tournament_results.append(ArcheryTournamentResult(
                        session_id=tournament_3.id,
                        student_id=student.id,
                        round_number=round_num,
                        arrow_number=arrow_num,
                        x_coordinate=random.uniform(-50.0, 50.0),
                        y_coordinate=random.uniform(-50.0, 50.0),
                        score=random.randint(6, 10),
                        max_score=10
                    ))
        
        db.add_all(tournament_results)
        db.commit()
        api_logger.info(f"Created {len(tournament_results)} archery tournament results")
        
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
        api_logger.info(f"Physical Assessment Sessions: 8 (2 per batch)")
        api_logger.info(f"Physical Assessment Details: {len(pa_details)}")
        api_logger.info(f"Archery Sessions: 8 (2 per batch)")
        api_logger.info(f"Archery Results: {len(archery_results)}")
        api_logger.info(f"Tournament Categories: 4")
        api_logger.info(f"Tournament Sessions: 3")
        api_logger.info(f"Tournament Results: {len(tournament_results)}")
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

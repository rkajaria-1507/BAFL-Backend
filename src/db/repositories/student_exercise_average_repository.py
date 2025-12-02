"""
Repository for managing student exercise averages and level calculations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict
from src.db.models.student_exercise_average import StudentExerciseAverage
from src.db.models.exercise_level_mapping import ExerciseLevelMapping
from src.db.models.physical_assessment import PhysicalAssessmentDetail


class StudentExerciseAverageRepository:
    """Repository for student exercise averages and level calculations."""
    
    # Exercise column mapping from PhysicalAssessmentDetail
    EXERCISE_COLUMNS = {
        "curl_up": "curl_up",
        "push_up": "push_up",
        "sit_and_reach": "sit_and_reach",
        "walk_600m": "walk_600m",
        "dash_50m": "dash_50m",
        "bow_hold": "bow_hold",
        "plank": "plank"
    }
    
    # Exercises that should be rounded (counts)
    INTEGER_EXERCISES = {"curl_up", "push_up"}
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_level_for_score(self, exercise_name: str, score: float) -> Optional[Dict]:
        """
        Get the level information for a given exercise and score.
        Returns dict with level, level_score, and level_description, or None if no mapping exists.
        """
        mapping = self.db.query(ExerciseLevelMapping).filter(
            and_(
                ExerciseLevelMapping.exercise_name == exercise_name,
                ExerciseLevelMapping.min_score <= score,
                ExerciseLevelMapping.max_score >= score
            )
        ).first()
        
        if mapping:
            return {
                "level": mapping.level,
                "level_score": mapping.level_score,
                "level_description": mapping.level_description
            }
        return None
    
    def calculate_average_for_student_batch_exercise(
        self, 
        student_id: int, 
        batch_id: int, 
        exercise_name: str
    ) -> Optional[float]:
        """
        Calculate the average score for a specific student, batch, and exercise
        across all sessions where the student was present.
        Returns rounded value for count exercises, decimal for others.
        """
        # Get the column attribute from PhysicalAssessmentDetail model
        exercise_column = getattr(PhysicalAssessmentDetail, exercise_name, None)
        if exercise_column is None:
            return None
        
        # Query to get average of the exercise where student was present
        result = self.db.query(
            func.avg(exercise_column).label("average"),
            func.count(PhysicalAssessmentDetail.id).label("session_count")
        ).join(
            PhysicalAssessmentDetail.session
        ).filter(
            and_(
                PhysicalAssessmentDetail.student_id == student_id,
                PhysicalAssessmentDetail.is_present == True,
                PhysicalAssessmentDetail.session.has(batch_id=batch_id)
            )
        ).first()
        
        if result and result.average is not None:
            avg_score = float(result.average)
            
            # Round for count exercises
            if exercise_name in self.INTEGER_EXERCISES:
                avg_score = round(avg_score)
            
            return avg_score
        
        return None
    
    def get_session_count_for_student_batch_exercise(
        self,
        student_id: int,
        batch_id: int,
        exercise_name: str
    ) -> int:
        """Get the number of sessions a student attended for a specific exercise in a batch."""
        exercise_column = getattr(PhysicalAssessmentDetail, exercise_name, None)
        if exercise_column is None:
            return 0
        
        count = self.db.query(func.count(PhysicalAssessmentDetail.id)).join(
            PhysicalAssessmentDetail.session
        ).filter(
            and_(
                PhysicalAssessmentDetail.student_id == student_id,
                PhysicalAssessmentDetail.is_present == True,
                PhysicalAssessmentDetail.session.has(batch_id=batch_id),
                exercise_column > 0  # Only count sessions where exercise was performed
            )
        ).scalar()
        
        return count or 0
    
    def update_or_create_average(
        self,
        student_id: int,
        batch_id: int,
        school_id: int,
        exercise_name: str,
        session_id: int
    ) -> Optional[StudentExerciseAverage]:
        """
        Update or create the average record for a student-batch-exercise combination.
        Recalculates average across all sessions and determines the current level.
        """
        # Calculate the new average
        avg_score = self.calculate_average_for_student_batch_exercise(
            student_id, batch_id, exercise_name
        )
        
        if avg_score is None:
            return None
        
        # Get session count
        session_count = self.get_session_count_for_student_batch_exercise(
            student_id, batch_id, exercise_name
        )
        
        # Get level information
        level_info = self.get_level_for_score(exercise_name, avg_score)
        
        # Check if record exists
        existing = self.db.query(StudentExerciseAverage).filter(
            and_(
                StudentExerciseAverage.student_id == student_id,
                StudentExerciseAverage.batch_id == batch_id,
                StudentExerciseAverage.exercise_name == exercise_name
            )
        ).first()
        
        if existing:
            # Update existing record
            existing.average_score = avg_score
            existing.session_count = session_count
            existing.last_updated_session_id = session_id
            if level_info:
                existing.current_level = level_info["level"]
                existing.level_score = level_info["level_score"]
                existing.level_description = level_info["level_description"]
            else:
                existing.current_level = None
                existing.level_score = None
                existing.level_description = None
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new record
            new_average = StudentExerciseAverage(
                student_id=student_id,
                batch_id=batch_id,
                school_id=school_id,
                exercise_name=exercise_name,
                average_score=avg_score,
                current_level=level_info["level"] if level_info else None,
                level_score=level_info["level_score"] if level_info else None,
                level_description=level_info["level_description"] if level_info else None,
                session_count=session_count,
                last_updated_session_id=session_id
            )
            self.db.add(new_average)
            self.db.commit()
            self.db.refresh(new_average)
            return new_average
    
    def update_averages_for_session(self, session_id: int, batch_id: int, school_id: int) -> int:
        """
        Update averages for all students and exercises in a session.
        Returns the number of average records updated/created.
        """
        # Get all students who were present in this session
        results = self.db.query(PhysicalAssessmentDetail).filter(
            and_(
                PhysicalAssessmentDetail.session_id == session_id,
                PhysicalAssessmentDetail.is_present == True
            )
        ).all()
        
        updated_count = 0
        processed_combinations = set()
        
        for result in results:
            student_id = result.student_id
            
            # Update average for each exercise
            for exercise_name in self.EXERCISE_COLUMNS.keys():
                # Skip if already processed this combination
                combination_key = (student_id, batch_id, exercise_name)
                if combination_key in processed_combinations:
                    continue
                
                # Check if the exercise has a non-zero value for this student
                exercise_value = getattr(result, exercise_name, 0)
                if exercise_value > 0:
                    avg_record = self.update_or_create_average(
                        student_id=student_id,
                        batch_id=batch_id,
                        school_id=school_id,
                        exercise_name=exercise_name,
                        session_id=session_id
                    )
                    if avg_record:
                        updated_count += 1
                    
                    processed_combinations.add(combination_key)
        
        return updated_count
    
    def get_student_averages_for_batch(
        self, 
        student_id: int, 
        batch_id: int
    ) -> List[StudentExerciseAverage]:
        """Get all exercise averages for a student in a batch."""
        return self.db.query(StudentExerciseAverage).filter(
            and_(
                StudentExerciseAverage.student_id == student_id,
                StudentExerciseAverage.batch_id == batch_id
            )
        ).all()
    
    def get_batch_averages(self, batch_id: int) -> List[StudentExerciseAverage]:
        """Get all exercise averages for all students in a batch."""
        return self.db.query(StudentExerciseAverage).filter(
            StudentExerciseAverage.batch_id == batch_id
        ).all()
    
    def get_school_averages(self, school_id: int) -> List[StudentExerciseAverage]:
        """Get all exercise averages for all students in a school."""
        return self.db.query(StudentExerciseAverage).filter(
            StudentExerciseAverage.school_id == school_id
        ).all()
    
    def recalculate_averages_after_session_deletion(
        self,
        deleted_session_id: int,
        batch_id: int,
        school_id: int
    ) -> int:
        """
        Recalculate averages for all students affected by a deleted session.
        This handles cases where the deleted session was the last_updated_session_id.
        Returns the number of average records updated.
        """
        from src.db.models.physical_assessment import PhysicalAssessmentSession
        
        # Find all average records that were last updated by the deleted session (now NULL)
        # or all records in this batch that might have been affected
        affected_averages = self.db.query(StudentExerciseAverage).filter(
            and_(
                StudentExerciseAverage.batch_id == batch_id,
                StudentExerciseAverage.last_updated_session_id == None
            )
        ).all()
        
        updated_count = 0
        
        for avg_record in affected_averages:
            student_id = avg_record.student_id
            exercise_name = avg_record.exercise_name
            
            # Recalculate the average
            new_avg = self.calculate_average_for_student_batch_exercise(
                student_id, batch_id, exercise_name
            )
            
            if new_avg is not None:
                # Get new session count
                session_count = self.get_session_count_for_student_batch_exercise(
                    student_id, batch_id, exercise_name
                )
                
                # Get the most recent session for this student in this batch
                latest_session = self.db.query(PhysicalAssessmentSession.id).join(
                    PhysicalAssessmentDetail,
                    PhysicalAssessmentDetail.session_id == PhysicalAssessmentSession.id
                ).filter(
                    and_(
                        PhysicalAssessmentSession.batch_id == batch_id,
                        PhysicalAssessmentDetail.student_id == student_id,
                        PhysicalAssessmentDetail.is_present == True
                    )
                ).order_by(PhysicalAssessmentSession.created_at.desc()).first()
                
                latest_session_id = latest_session[0] if latest_session else None
                
                # Get new level info
                level_info = self.get_level_for_score(exercise_name, new_avg)
                
                # Update the record
                avg_record.average_score = new_avg
                avg_record.session_count = session_count
                avg_record.last_updated_session_id = latest_session_id
                
                if level_info:
                    avg_record.current_level = level_info["level"]
                    avg_record.level_score = level_info["level_score"]
                    avg_record.level_description = level_info["level_description"]
                else:
                    avg_record.current_level = None
                    avg_record.level_score = None
                    avg_record.level_description = None
                
                updated_count += 1
            else:
                # No more sessions with this exercise for this student - delete the record
                self.db.delete(avg_record)
                updated_count += 1
        
        self.db.commit()
        return updated_count

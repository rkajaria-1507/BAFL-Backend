from datetime import datetime
from typing import Dict, Iterable, Sequence, List

from fastapi import HTTPException, status
from sqlalchemy import insert, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.logging import api_logger, db_logger
from src.db.models.batch import Batch
from src.db.models.physical_assessment import PhysicalAssessmentDetail, PhysicalAssessmentSession
from src.db.models.student import Student
from src.db.models.user import UserRole, User
from src.db.models.school import School
from src.db.repositories.batch_repository import BatchRepository
from src.db.repositories.coach_repository import CoachRepository
from src.db.repositories.physical_results_repository import PhysicalResultsRepository
from src.db.repositories.physical_session_repository import PhysicalSessionRepository
from src.db.repositories.school_repository import SchoolRepository
from src.db.repositories.student_repository import StudentRepository
from src.db.repositories.student_exercise_average_repository import StudentExerciseAverageRepository
from src.schemas.batch import BatchSummary, BatchScheduleItem
from src.schemas.physical_assessment import (
    PhysicalAssessmentResultResponse,
    PhysicalAssessmentResultUpdate,
    PhysicalAssessmentSessionCreate,
    PhysicalAssessmentSessionResponse,
    PhysicalAssessmentSessionUpdate,
    PhysicalAssessmentSessionWithResultsCreate,
    PreCreateResponse,
    PreCreateBatch,
    PreCreateSchedule,
    PreCreateCoach,
    PreCreateStudent,
    PhysicalAssessmentSessionAdminViewResponse,
    PhysicalAssessmentSessionAdminView,
    PhysicalAssessmentStudentSummaryResponse,
    PhysicalAssessmentStudentSummary,
    PhysicalAssessmentStudentDetailResponse,
    PhysicalAssessmentStudentSessionResult,
    PhysicalAssessmentStudentUpdate,
)
from src.db.models.coach import Coach
from src.db.models.coach_batch import CoachBatch


class PhysicalAssessmentService:
    # Exercise validation thresholds
    EXERCISE_CONSTRAINTS = {
        "curl_up": {"min": 0, "max": 200, "type": "higher_better"},
        "push_up": {"min": 0, "max": 150, "type": "higher_better"},
        "sit_and_reach": {"min": 0, "max": 100, "type": "higher_better"},
        "walk_600m": {"min": 1.5, "max": None, "type": "lower_better"},  # min 1.5 minutes
        "dash_50m": {"min": 5.0, "max": None, "type": "lower_better"},  # min 5.0 seconds
        "bow_hold": {"min": 0, "max": 600, "type": "higher_better"},  # max 10 minutes
        "plank": {"min": 0, "max": 10, "type": "higher_better"},  # max 10 minutes
    }

    @staticmethod
    def _validate_exercise_value(exercise_name: str, value: float | int | None, student_id: int) -> None:
        """Validate exercise values against absurdity thresholds."""
        if value is None:
            return  # NULL is allowed
        
        if exercise_name not in PhysicalAssessmentService.EXERCISE_CONSTRAINTS:
            return
        
        constraints = PhysicalAssessmentService.EXERCISE_CONSTRAINTS[exercise_name]
        value_type = constraints["type"]
        
        # For lower_better exercises, reject zero (can't complete in 0 time)
        if value_type == "lower_better" and value == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "validation_error",
                    "message": f"Invalid score for {exercise_name}: value cannot be 0 for timed exercises",
                    "exercise": exercise_name,
                    "student_id": student_id,
                    "value": value,
                    "constraint": "non_zero"
                }
            )
        
        # Check minimum threshold
        if constraints["min"] is not None and value < constraints["min"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "validation_error",
                    "message": f"Invalid score for {exercise_name}: {value} is below minimum allowed value of {constraints['min']}",
                    "exercise": exercise_name,
                    "student_id": student_id,
                    "value": value,
                    "constraint": f"min_{constraints['min']}"
                }
            )
        
        # Check maximum threshold
        if constraints["max"] is not None and value > constraints["max"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "validation_error",
                    "message": f"Invalid score for {exercise_name}: {value} exceeds maximum allowed value of {constraints['max']}",
                    "exercise": exercise_name,
                    "student_id": student_id,
                    "value": value,
                    "constraint": f"max_{constraints['max']}"
                }
            )

    @staticmethod
    def _build_batch_summary(batch: Batch | None) -> BatchSummary | None:
        if batch is None:
            return None
        school = batch.school
        return BatchSummary(
            batch_id=batch.id,
            batch_name=batch.batch_name,
            school_id=batch.school_id,
            school_name=school.name if school else "",
        )

    @staticmethod
    def _build_result_response(detail: PhysicalAssessmentDetail) -> PhysicalAssessmentResultResponse:
        return PhysicalAssessmentResultResponse(
            id=detail.id,
            session_id=detail.session_id,
            student_id=detail.student_id,
            student=detail.student,
            discipline=detail.discipline,
            curl_up=detail.curl_up,
            push_up=detail.push_up,
            sit_and_reach=detail.sit_and_reach,
            walk_600m=detail.walk_600m,
            dash_50m=detail.dash_50m,
            bow_hold=detail.bow_hold,
            plank=detail.plank,
            is_present=detail.is_present,
            created_at=detail.created_at,
            updated_at=detail.updated_at,
        )

    @staticmethod
    def _build_session_response(
        db: Session,
        session: PhysicalAssessmentSession,
        *,
        include_results: bool = True,
    ) -> PhysicalAssessmentSessionResponse:
        batch_summary = PhysicalAssessmentService._build_batch_summary(session.batch)

        batch_schedule = []
        if session.batch and session.batch.schedules:
            batch_schedule = [
                BatchScheduleItem(
                    schedule_id=s.id,
                    day_of_week=s.day_of_week,
                    start_time=s.start_time,
                    end_time=s.end_time,
                )
                for s in session.batch.schedules
            ]

        results: List[PhysicalAssessmentResultResponse] = []
        if include_results:
            details = list(session.results)
            if not details:
                details = PhysicalResultsRepository.get_by_session(db, session.id)
            results = [PhysicalAssessmentService._build_result_response(detail) for detail in details]

        return PhysicalAssessmentSessionResponse(
            id=session.id,
            coach_id=session.coach_id,
            coach_name=session.coach.name,
            school_id=session.school_id,
            batch_id=session.batch_id,
            date_of_session=session.date_of_session,
            student_count=session.student_count,
            created_at=session.created_at,
            updated_at=session.updated_at,
            batch=batch_summary,
            school=session.school,
            batch_schedule=batch_schedule,
            results=results,
        )

    @staticmethod
    def serialize_session(
        db: Session,
        session: PhysicalAssessmentSession,
        *,
        include_results: bool = True,
    ) -> PhysicalAssessmentSessionResponse:
        return PhysicalAssessmentService._build_session_response(db, session, include_results=include_results)

    @staticmethod
    def serialize_result(detail: PhysicalAssessmentDetail) -> PhysicalAssessmentResultResponse:
        return PhysicalAssessmentService._build_result_response(detail)

    @staticmethod
    def _resolve_relationships(
        db: Session,
        coach_id: int | None,
        school_id: int | None,
        batch_id: int | None,
    ) -> Dict[str, object]:
        batch = None
        if batch_id is not None:
            batch = BatchRepository.get_by_id(db, batch_id)
            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Batch with ID {batch_id} not found",
                )
            if batch.coach_id and coach_id and batch.coach_id != coach_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coach does not match the batch assignment",
                )
            if batch.school_id is not None:
                if school_id is not None and school_id != batch.school_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Batch and school mismatch",
                    )
                school_id = batch.school_id
            if coach_id is None and batch.coach_id:
                coach_id = batch.coach_id

        coach = None
        if coach_id is not None:
            coach = CoachRepository.get_by_id(db, coach_id)
            if not coach:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Coach with ID {coach_id} not found",
                )

            coach_school_ids = {
                assignment.school_id
                for assignment in getattr(coach, "school_assignments", [])
                if assignment.school_id is not None
            }

            if school_id is not None and coach_school_ids and school_id not in coach_school_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coach and school mismatch",
                )

            if school_id is None:
                if len(coach_school_ids) == 1:
                    school_id = next(iter(coach_school_ids))
                elif coach_school_ids and batch is None:
                    # Ambiguous without batch context; require explicit school selection
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Coach assigned to multiple schools; specify school_id or batch_id",
                    )

        school = None
        if school_id is not None:
            school = SchoolRepository.get_by_id(db, school_id)
            if not school:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"School with ID {school_id} not found",
                )

        return {"coach_id": coach_id, "school_id": school_id, "batch": batch}

    @staticmethod
    def _prepare_default_results(session_id: int, students: Sequence[int]) -> Iterable[PhysicalAssessmentDetail]:
        for student_id in students:
            yield PhysicalAssessmentDetail(
                session_id=session_id,
                student_id=student_id,
                curl_up=0,
                push_up=0,
                sit_and_reach=0.0,
                walk_600m=0.0,
                dash_50m=0.0,
                bow_hold=0.0,
                plank=0.0,
                is_present=True,
            )

    @staticmethod
    def create_session(db: Session, session_data: PhysicalAssessmentSessionCreate) -> PhysicalAssessmentSession:
        refs = PhysicalAssessmentService._resolve_relationships(
            db,
            coach_id=session_data.coach_id,
            school_id=session_data.school_id,
            batch_id=session_data.batch_id,
        )

        payload = session_data.model_dump()
        payload["coach_id"] = refs["coach_id"]
        payload["school_id"] = refs["school_id"]

        batch = refs["batch"]
        student_ids: list[int] = []
        if batch:
            students = StudentRepository.get_by_batch(db, batch.id)
            student_ids = [student.id for student in students]
            expected_count = len(student_ids)
            if expected_count and session_data.student_count != expected_count:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="student_count must match batch size",
                )
            payload["student_count"] = expected_count

        session = PhysicalAssessmentSession(**payload)
        session = PhysicalSessionRepository.create(db, session)

        if student_ids:
            PhysicalResultsRepository.create_all(
                db,
                list(PhysicalAssessmentService._prepare_default_results(session.id, student_ids)),
            )

        refreshed = PhysicalSessionRepository.get_by_id(db, session.id)
        if refreshed is None:
            refreshed = session
        return PhysicalAssessmentService.serialize_session(db, refreshed)

    @staticmethod
    def create_session_with_results(
        db: Session,
        payload: PhysicalAssessmentSessionWithResultsCreate,
        current_user,
    ) -> PhysicalAssessmentSession:
        if not payload.results:
            raise ValueError("results must be a non-empty list")
        if payload.batch_id is None:
            raise ValueError("batch_id is required when submitting results")

        refs = PhysicalAssessmentService._resolve_relationships(
            db,
            coach_id=payload.coach_id,
            school_id=payload.school_id,
            batch_id=payload.batch_id,
        )

        stmt = select(Student.id).where(Student.batch_id == payload.batch_id).with_for_update()
        student_rows = list(db.execute(stmt).scalars())
        actual_batch_student_ids = set(student_rows)

        if not actual_batch_student_ids:
            raise ValueError("Batch has no students to record results for")

        if len(payload.results) != len({r.student_id for r in payload.results}):
            raise ValueError("Duplicate student entries detected in results payload")

        provided_ids = {r.student_id for r in payload.results}
        invalid_ids = list(provided_ids - actual_batch_student_ids)
        admin_override = bool(getattr(payload, "admin_override", False))
        role = getattr(current_user, "role", None)
        role_value = getattr(role, "value", role)
        is_admin = role_value == UserRole.ADMIN.value

        if invalid_ids and not (admin_override and is_admin):
            raise ValueError(f"Some student_ids do not belong to batch: {invalid_ids}")

        if payload.student_count is not None and payload.student_count != len(actual_batch_student_ids):
            raise ValueError(
                "student_count mismatch: provided={} actual={}".format(
                    payload.student_count,
                    len(actual_batch_student_ids),
                )
            )

        numeric_int_fields = ["curl_up", "push_up"]
        numeric_float_fields = ["sit_and_reach", "walk_600m", "dash_50m", "bow_hold", "plank"]

        results_to_insert: list[dict[str, object]] = []
        for result in payload.results:
            record: dict[str, object] = {
                "student_id": int(result.student_id),
                "discipline": result.discipline,
            }
            
            temp_values = {}
            any_non_null = False

            for field in numeric_int_fields:
                value = getattr(result, field, None)
                # Handle Pydantic defaults (0) or explicit None
                if value is not None:
                    try:
                        value = int(value)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"Invalid integer for {field} for student {result.student_id}") from exc
                    if value < 0:
                        raise ValueError(f"Negative value for {field} for student {result.student_id}")
                    # Validate for absurd values
                    PhysicalAssessmentService._validate_exercise_value(field, value, result.student_id)
                    any_non_null = True
                temp_values[field] = value

            for field in numeric_float_fields:
                value = getattr(result, field, None)
                if value is not None:
                    try:
                        value = float(value)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"Invalid float for {field} for student {result.student_id}") from exc
                    if value < 0:
                        raise ValueError(f"Negative value for {field} for student {result.student_id}")
                    value = round(value, 2)
                    # Validate for absurd values
                    PhysicalAssessmentService._validate_exercise_value(field, value, result.student_id)
                    any_non_null = True
                temp_values[field] = value

            if not any_non_null:
                # Absent: all null
                record["is_present"] = False
                for field in numeric_int_fields + numeric_float_fields:
                    record[field] = None
            else:
                # Present: store as is
                record["is_present"] = True
                for field in numeric_int_fields + numeric_float_fields:
                    record[field] = temp_values[field]

            results_to_insert.append(record)

        try:
            new_session = PhysicalAssessmentSession(
                coach_id=refs["coach_id"],
                school_id=refs["school_id"],
                batch_id=payload.batch_id,
                date_of_session=payload.date_of_session,
                student_count=len(actual_batch_student_ids),
            )
            db.add(new_session)
            db.flush()

            for result in results_to_insert:
                result["session_id"] = new_session.id

            if results_to_insert:
                db.execute(insert(PhysicalAssessmentDetail), results_to_insert)

            db.commit()
            db.refresh(new_session)
        except IntegrityError as exc:
            db.rollback()
            db_logger.error("DB integrity error during create_session_with_results: %s", str(exc))
            raise
        except Exception:
            db.rollback()
            raise

        if invalid_ids and admin_override and is_admin:
            api_logger.info(
                "Admin override by user %s for batch %s invalid student_ids=%s",
                getattr(current_user, "id", "unknown"),
                payload.batch_id,
                invalid_ids,
            )

        # Update averages and levels for all students in this session
        try:
            avg_repo = StudentExerciseAverageRepository(db)
            avg_repo.update_averages_for_session(
                session_id=new_session.id,
                batch_id=payload.batch_id,
                school_id=refs["school_id"]
            )
            db.commit()
            api_logger.info(
                "Updated exercise averages for session %s, batch %s",
                new_session.id,
                payload.batch_id
            )
        except Exception as avg_exc:
            db.rollback()
            api_logger.warning(
                "Failed to update exercise averages for session %s: %s",
                new_session.id,
                str(avg_exc)
            )

        refreshed = PhysicalSessionRepository.get_by_id(db, new_session.id)
        if refreshed is None:
            refreshed = new_session
        return PhysicalAssessmentService.serialize_session(db, refreshed)

    @staticmethod
    def get_session(db: Session, session_id: int) -> PhysicalAssessmentSessionResponse | None:
        session = PhysicalSessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        return PhysicalAssessmentService.serialize_session(db, session)

    @staticmethod
    def get_session_model(db: Session, session_id: int) -> PhysicalAssessmentSession | None:
        return PhysicalSessionRepository.get_by_id(db, session_id)

    @staticmethod
    def get_all_sessions(db: Session, skip: int = 0, limit: int = 100) -> list[PhysicalAssessmentSession]:
        return PhysicalSessionRepository.get_all(db, skip, limit)

    @staticmethod
    def update_session(
        db: Session,
        session_id: int,
        session_data: PhysicalAssessmentSessionUpdate,
    ) -> PhysicalAssessmentSessionResponse | None:
        try:
            session = PhysicalSessionRepository.get_by_id(db, session_id)
            if not session:
                return None
                
            payload = session_data.model_dump(exclude_unset=True)
            results_data = payload.pop("results", None)

            # Update Session
            if payload:
                refs = PhysicalAssessmentService._resolve_relationships(
                    db,
                    coach_id=payload.get("coach_id", session.coach_id),
                    school_id=payload.get("school_id", session.school_id),
                    batch_id=payload.get("batch_id", session.batch_id),
                )
                payload["coach_id"] = refs["coach_id"]
                payload["school_id"] = refs["school_id"]
                
                for key, value in payload.items():
                    setattr(session, key, value)

            # Update Results
            if results_data:
                existing_results = {r.student_id: r for r in session.results}
                numeric_fields = [
                    "curl_up", "push_up", "sit_and_reach", "walk_600m", 
                    "dash_50m", "bow_hold", "plank"
                ]
                
                for res_input in results_data:
                    student_id = res_input.get("student_id")
                    if student_id in existing_results:
                        result_obj = existing_results[student_id]
                        
                        for field in numeric_fields:
                            if field in res_input:
                                val = res_input[field]
                                if val is None:
                                    val = 0.0 if field in ["sit_and_reach", "walk_600m", "dash_50m", "bow_hold", "plank"] else 0
                                setattr(result_obj, field, val)
                        
                        if "discipline" in res_input:
                            result_obj.discipline = res_input["discipline"]
                        
                        # Recalculate is_present based on values
                        values = [getattr(result_obj, field) for field in numeric_fields]
                        result_obj.is_present = any(value for value in values)
                        
                        # Allow explicit override if provided
                        if "is_present" in res_input:
                            result_obj.is_present = res_input["is_present"]

            db.commit()
            db.refresh(session)
            
            # Update averages if results were updated
            if results_data:
                try:
                    avg_repo = StudentExerciseAverageRepository(db)
                    avg_repo.update_averages_for_session(
                        session_id=session_id,
                        batch_id=session.batch_id,
                        school_id=session.school_id
                    )
                    api_logger.info(
                        "Updated exercise averages after session update %s",
                        session_id
                    )
                except Exception as avg_exc:
                    api_logger.warning(
                        "Failed to update exercise averages for session %s: %s",
                        session_id,
                        str(avg_exc)
                    )
            
            return PhysicalAssessmentService.serialize_session(db, session)

        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        session = PhysicalSessionRepository.get_by_id(db, session_id)
        if not session:
            return False
        
        # Store session info before deletion
        batch_id = session.batch_id
        school_id = session.school_id
        
        try:
            db.delete(session)
            db.commit()
            
            # Recalculate averages for students affected by this deletion
            if batch_id and school_id:
                try:
                    avg_repo = StudentExerciseAverageRepository(db)
                    updated = avg_repo.recalculate_averages_after_session_deletion(
                        deleted_session_id=session_id,
                        batch_id=batch_id,
                        school_id=school_id
                    )
                    api_logger.info(
                        "Recalculated %d exercise averages after deleting session %s",
                        updated,
                        session_id
                    )
                except Exception as avg_exc:
                    api_logger.warning(
                        "Failed to recalculate averages after session deletion %s: %s",
                        session_id,
                        str(avg_exc)
                    )
            
            return True
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def update_result(
        db: Session,
        result_id: int,
        result_data: PhysicalAssessmentResultUpdate,
    ) -> PhysicalAssessmentResultResponse | None:
        result = PhysicalResultsRepository.get_by_id(db, result_id)
        if not result:
            return None

        payload = result_data.model_dump(exclude_unset=True)
        numeric_fields = [
            "curl_up",
            "push_up",
            "sit_and_reach",
            "walk_600m",
            "dash_50m",
            "bow_hold",
            "plank",
        ]

        for field in numeric_fields:
            if field in payload and payload[field] is None:
                payload[field] = 0.0 if field == "sit_and_reach" else 0

        values = [payload.get(field, getattr(result, field)) for field in numeric_fields]
        payload["is_present"] = any(value for value in values)

        updated = PhysicalResultsRepository.update(db, result, payload)
        
        # Update averages for this student's exercises
        try:
            session = result.session
            if session and session.batch_id and session.school_id:
                avg_repo = StudentExerciseAverageRepository(db)
                avg_repo.update_averages_for_session(
                    session_id=session.id,
                    batch_id=session.batch_id,
                    school_id=session.school_id
                )
                api_logger.info(
                    "Updated exercise averages after result update %s",
                    result_id
                )
        except Exception as avg_exc:
            api_logger.warning(
                "Failed to update exercise averages for result %s: %s",
                result_id,
                str(avg_exc)
            )
        
        return PhysicalAssessmentService.serialize_result(updated)

    @staticmethod
    def get_results_by_session(db: Session, session_id: int) -> list[PhysicalAssessmentResultResponse]:
        details = PhysicalResultsRepository.get_by_session(db, session_id)
        return [PhysicalAssessmentService.serialize_result(detail) for detail in details]

    @staticmethod
    def get_result(db: Session, result_id: int) -> PhysicalAssessmentResultResponse | None:
        detail = PhysicalResultsRepository.get_by_id(db, result_id)
        if not detail:
            return None
        return PhysicalAssessmentService.serialize_result(detail)

    @staticmethod
    def get_pre_create_data(db: Session, user: User) -> PreCreateResponse:
        query = select(Batch)
        
        if user.role == UserRole.COACH:
            coach_profile = getattr(user, "coach_profile", None)
            if not coach_profile:
                return PreCreateResponse(batches=[])
            # Filter batches assigned to this coach
            query = query.join(CoachBatch).filter(CoachBatch.coach_id == coach_profile.id)
        
        batches = db.scalars(query).all()
        
        pre_create_batches = []
        for batch in batches:
            # Schedule
            schedule_list = [
                PreCreateSchedule(
                    schedule_id=s.id,
                    day_of_week=s.day_of_week,
                    start_time=s.start_time,
                    end_time=s.end_time
                ) for s in batch.schedules
            ]
            
            # Coaches
            coaches_list = []
            for assignment in batch.coach_assignments:
                if assignment.coach:
                    coaches_list.append(PreCreateCoach(
                        coach_id=assignment.coach.id,
                        coach_name=assignment.coach.name if assignment.coach else None
                    ))
            
            # Students
            students_list = [
                PreCreateStudent(
                    student_id=s.id,
                    student_name=s.name,
                    age=s.age
                ) for s in batch.students
            ]
            
            pre_create_batches.append(PreCreateBatch(
                batch_id=batch.id,
                batch_name=batch.batch_name,
                school_id=batch.school_id,
                school_name=batch.school.name if batch.school else "",
                schedule=schedule_list,
                coaches=coaches_list,
                students=students_list
            ))
            
        return PreCreateResponse(batches=pre_create_batches)

    @staticmethod
    def get_admin_view_sessions(db: Session) -> PhysicalAssessmentSessionAdminViewResponse:
        sessions = PhysicalSessionRepository.get_all(db)
        view_sessions = []
        for session in sessions:
            coach_name = "Unknown"
            if session.coach_id:
                coach = CoachRepository.get_by_id(db, session.coach_id)
                if coach:
                    coach_name = coach.name
            
            view_sessions.append(PhysicalAssessmentSessionAdminView(
                session_id=session.id,
                batch_id=session.batch_id,
                batch_name=session.batch.batch_name if session.batch else None,
                school_id=session.school_id,
                school_name=session.school.name if session.school else None,
                coach_id=session.coach_id,
                coach_name=coach_name,
                date_of_session=session.date_of_session,
                student_count=session.student_count or 0,
            ))
        return PhysicalAssessmentSessionAdminViewResponse(sessions=view_sessions)

    @staticmethod
    def get_coach_view_sessions(db: Session, coach_id: int) -> PhysicalAssessmentSessionAdminViewResponse:
        # Sessions created by coach OR sessions for batches assigned to coach
        
        # 1. Get batches assigned to coach
        assigned_batches_query = select(CoachBatch.batch_id).where(CoachBatch.coach_id == coach_id)
        assigned_batch_ids = db.scalars(assigned_batches_query).all()
        
        # 2. Query sessions
        query = select(PhysicalAssessmentSession).where(
            (PhysicalAssessmentSession.coach_id == coach_id) |
            (PhysicalAssessmentSession.batch_id.in_(assigned_batch_ids))
        )
        sessions = db.scalars(query).all()
        
        view_sessions = []
        for session in sessions:
            coach_name = "Unknown"
            if session.coach_id:
                coach = CoachRepository.get_by_id(db, session.coach_id)
                if coach:
                    coach_name = coach.name
            
            view_sessions.append(PhysicalAssessmentSessionAdminView(
                session_id=session.id,
                batch_id=session.batch_id,
                batch_name=session.batch.batch_name if session.batch else None,
                school_id=session.school_id,
                school_name=session.school.name if session.school else None,
                coach_id=session.coach_id,
                coach_name=coach_name,
                date_of_session=session.date_of_session,
                student_count=session.student_count or 0,
            ))
        return PhysicalAssessmentSessionAdminViewResponse(sessions=view_sessions)

    @staticmethod
    def get_admin_view_students(db: Session) -> PhysicalAssessmentStudentSummaryResponse:
        stmt = (
            select(
                Student.id.label("student_id"),
                Student.name.label("student_name"),
                Student.batch_id.label("batch_id"),
                Batch.batch_name.label("batch_name"),
                Batch.school_id.label("school_id"),
                School.name.label("school_name"),
                func.count(func.distinct(PhysicalAssessmentDetail.session_id)).label("total_sessions"),
                func.max(PhysicalAssessmentSession.date_of_session).label("last_session_date"),
            )
            .outerjoin(PhysicalAssessmentDetail, PhysicalAssessmentDetail.student_id == Student.id)
            .outerjoin(PhysicalAssessmentSession, PhysicalAssessmentSession.id == PhysicalAssessmentDetail.session_id)
            .outerjoin(Batch, Batch.id == Student.batch_id)
            .outerjoin(School, School.id == Batch.school_id)
            .group_by(
                Student.id,
                Student.name,
                Student.batch_id,
                Batch.batch_name,
                Batch.school_id,
                School.name,
            )
        )
        rows = db.execute(stmt).all()

        summaries: List[PhysicalAssessmentStudentSummary] = []
        for row in rows:
            summaries.append(
                PhysicalAssessmentStudentSummary(
                    student_id=row.student_id,
                    student_name=row.student_name,
                    batch_id=row.batch_id,
                    batch_name=row.batch_name,
                    school_id=row.school_id,
                    school_name=row.school_name,
                    total_sessions=row.total_sessions or 0,
                    last_session_date=row.last_session_date,
                )
            )

        return PhysicalAssessmentStudentSummaryResponse(students=summaries)

    @staticmethod
    def get_coach_view_students(db: Session, coach_id: int) -> PhysicalAssessmentStudentSummaryResponse:
        assigned_batches_query = select(CoachBatch.batch_id).where(CoachBatch.coach_id == coach_id)
        assigned_batch_ids = list(db.scalars(assigned_batches_query).all())
        if not assigned_batch_ids:
            return PhysicalAssessmentStudentSummaryResponse(students=[])

        stmt = (
            select(
                Student.id.label("student_id"),
                Student.name.label("student_name"),
                Student.batch_id.label("batch_id"),
                Batch.batch_name.label("batch_name"),
                Batch.school_id.label("school_id"),
                School.name.label("school_name"),
                func.count(func.distinct(PhysicalAssessmentDetail.session_id)).label("total_sessions"),
                func.max(PhysicalAssessmentSession.date_of_session).label("last_session_date"),
            )
            .outerjoin(PhysicalAssessmentDetail, PhysicalAssessmentDetail.student_id == Student.id)
            .outerjoin(PhysicalAssessmentSession, PhysicalAssessmentSession.id == PhysicalAssessmentDetail.session_id)
            .outerjoin(Batch, Batch.id == Student.batch_id)
            .outerjoin(School, School.id == Batch.school_id)
            .where(Student.batch_id.in_(assigned_batch_ids))
            .group_by(
                Student.id,
                Student.name,
                Student.batch_id,
                Batch.batch_name,
                Batch.school_id,
                School.name,
            )
        )

        rows = db.execute(stmt).all()

        summaries: List[PhysicalAssessmentStudentSummary] = []
        for row in rows:
            summaries.append(
                PhysicalAssessmentStudentSummary(
                    student_id=row.student_id,
                    student_name=row.student_name,
                    batch_id=row.batch_id,
                    batch_name=row.batch_name,
                    school_id=row.school_id,
                    school_name=row.school_name,
                    total_sessions=row.total_sessions or 0,
                    last_session_date=row.last_session_date,
                )
            )

        return PhysicalAssessmentStudentSummaryResponse(students=summaries)

    @staticmethod
    def get_student_detail(db: Session, student_id: int) -> PhysicalAssessmentStudentDetailResponse | None:
        student = StudentRepository.get_by_id(db, student_id)
        if not student:
            return None

        batch = getattr(student, "batch", None)
        school = getattr(batch, "school", None) if batch else None

        results = PhysicalResultsRepository.get_by_student(db, student_id)
        session_entries: List[PhysicalAssessmentStudentSessionResult] = []

        for result in sorted(results, key=lambda r: (r.session.date_of_session if r.session else datetime.min)):
            session = result.session
            if session is None:
                continue
            coach_name = session.coach.name if session.coach else None
            session_entries.append(
                PhysicalAssessmentStudentSessionResult(
                    session_id=session.id,
                    date_of_session=session.date_of_session,
                    coach_id=session.coach_id,
                    coach_name=coach_name,
                    result=PhysicalAssessmentService.serialize_result(result),
                )
            )

        return PhysicalAssessmentStudentDetailResponse(
            student_id=student.id,
            student_name=student.name,
            batch_id=student.batch_id,
            batch_name=batch.batch_name if batch else None,
            school_id=batch.school_id if batch else None,
            school_name=school.name if school else None,
            sessions=session_entries,
        )

    @staticmethod
    def update_student_results(
        db: Session,
        student_id: int,
        payload: PhysicalAssessmentStudentUpdate,
    ) -> PhysicalAssessmentStudentDetailResponse:
        student = StudentRepository.get_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        if not payload.updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="updates must include at least one entry")

        for update in payload.updates:
            result_obj = PhysicalResultsRepository.get_by_session_and_student(db, update.session_id, student_id)
            if not result_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Result for session {update.session_id} and student {student_id} not found",
                )

            PhysicalAssessmentService.update_result(db, result_obj.id, update.result)

        return PhysicalAssessmentService.get_student_detail(db, student_id)

    @staticmethod
    def delete_student_results(db: Session, student_id: int) -> bool:
        student = StudentRepository.get_by_id(db, student_id)
        if not student:
            return False

        deleted = PhysicalResultsRepository.delete_by_student(db, student_id)
        return deleted > 0

    @staticmethod
    def get_level_mappings(db: Session):
        """
        Get all student exercise level mappings grouped by school, batch, and student.
        Includes all 7 exercises for each student with null values for exercises not performed.
        """
        from src.schemas.physical_assessment import (
            PhysicalAssessmentLevelMappingResponse,
            SchoolLevelMapping,
            BatchLevelMapping,
            StudentLevelMapping,
            ExercisePerformance
        )
        from collections import defaultdict
        
        # Define all exercises in order
        ALL_EXERCISES = ["curl_up", "push_up", "sit_and_reach", "walk_600m", "dash_50m", "bow_hold", "plank"]
        
        repo = StudentExerciseAverageRepository(db)
        data = repo.get_all_level_mappings_with_relations()
        
        # Build coach mapping: batch_id -> list of coach names
        coach_map = defaultdict(list)
        for coach_record in data['coaches']:
            coach_map[coach_record.batch_id].append(coach_record.coach_name)
        
        # Build exercise data mapping: (school_id, batch_id, student_id, exercise_name) -> data
        exercise_map = {}
        for record in data['exercise_data']:
            key = (record.school_id, record.batch_id, record.student_id, record.exercise_name)
            exercise_map[key] = {
                'average_score': record.average_score,
                'level': record.current_level,
                'level_description': record.level_description
            }
        
        # Build nested structure using all students
        schools_dict = {}
        
        for student_record in data['all_students']:
            school_id = student_record.school_id
            batch_id = student_record.batch_id
            student_id = student_record.student_id
            
            # Initialize school if not exists
            if school_id not in schools_dict:
                schools_dict[school_id] = {
                    'school_name': student_record.school_name,
                    'batches': {}
                }
            
            # Initialize batch if not exists
            if batch_id not in schools_dict[school_id]['batches']:
                coach_names = coach_map.get(batch_id)
                schools_dict[school_id]['batches'][batch_id] = {
                    'batch_name': student_record.batch_name,
                    'coach_names': coach_names if coach_names else None,
                    'students': []
                }
            
            # Create exercise list for this student (all 7 exercises)
            exercises = []
            for exercise_name in ALL_EXERCISES:
                key = (school_id, batch_id, student_id, exercise_name)
                if key in exercise_map:
                    # Exercise data exists
                    exercises.append(ExercisePerformance(
                        exercise_name=exercise_name,
                        average_score=exercise_map[key]['average_score'],
                        level=exercise_map[key]['level'],
                        level_description=exercise_map[key]['level_description']
                    ))
                else:
                    # Exercise not performed - all null values
                    exercises.append(ExercisePerformance(
                        exercise_name=exercise_name,
                        average_score=None,
                        level=None,
                        level_description=None
                    ))
            
            # Add student to batch
            schools_dict[school_id]['batches'][batch_id]['students'].append(
                StudentLevelMapping(
                    student_name=student_record.student_name,
                    exercises=exercises
                )
            )
        
        # Convert nested dicts to list format for response
        schools_list = []
        for school_id, school_data in schools_dict.items():
            batches_list = []
            for batch_id, batch_data in school_data['batches'].items():
                batches_list.append(BatchLevelMapping(
                    batch_name=batch_data['batch_name'],
                    coach_names=batch_data['coach_names'],
                    students=batch_data['students']
                ))
            
            schools_list.append(SchoolLevelMapping(
                school_name=school_data['school_name'],
                batches=batches_list
            ))
        
        return PhysicalAssessmentLevelMappingResponse(schools=schools_list)

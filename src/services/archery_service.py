from collections import defaultdict
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status

from src.db.models.archery import ArcherySession, ArcheryResult
from src.db.models.batch import Batch
from src.db.models.school import School
from src.db.models.student import Student
from src.db.models.user import User, UserRole
from src.db.models.coach_batch import CoachBatch
from src.db.repositories.archery_repository import ArcherySessionRepository, ArcheryResultRepository
from src.db.repositories.student_repository import StudentRepository
from src.schemas.archery import (
    ArcherySessionCreate,
    ArcherySessionResponse,
    ArcheryStudentRoundResponse,
    ArcheryRoundResponse,
    ArcheryShotResponse,
    ArcherySessionSummaryResponse,
    ArcherySessionSummary,
    ArcheryStudentSummaryResponse,
    ArcheryStudentSummary,
    ArcheryStudentDetailResponse,
    ArcheryStudentSessionDetail,
    ArcheryStudentUpdate,
    ArcherySessionUpdate,
)
from src.schemas.physical_assessment import PreCreateResponse, PreCreateBatch, PreCreateSchedule, PreCreateCoach, PreCreateStudent
from src.services.physical_assessment_service import PhysicalAssessmentService

class ArcheryService:
    @staticmethod
    def get_pre_create_data(db: Session, user: User) -> PreCreateResponse:
        # Reusing logic from PhysicalAssessmentService or duplicating it
        # Since it's identical requirement: "pre create endpoint where we are sending the batch details, school details, coach details and the student details"
        return PhysicalAssessmentService.get_pre_create_data(db, user)

    @staticmethod
    def create_session(db: Session, payload: ArcherySessionCreate) -> ArcherySessionResponse:
        refs = PhysicalAssessmentService._resolve_relationships(
            db,
            coach_id=payload.coach_id,
            school_id=payload.school_id,
            batch_id=payload.batch_id,
        )
        batch = refs["batch"]

        valid_student_ids: Optional[set[int]] = None
        if batch:
            valid_student_ids = {student.id for student in StudentRepository.get_by_batch(db, batch.id)}

        # Create Session
        session = ArcherySession(
            batch_id=payload.batch_id,
            coach_id=refs["coach_id"],
            school_id=refs["school_id"],
            date_of_session=payload.date_of_session,
            distance=payload.distance,
        )
        session = ArcherySessionRepository.create(db, session)

        # Create Results
        results_to_create: List[ArcheryResult] = []
        seen_pairs: set[tuple[int, int]] = set()
        for student_input in payload.results:
            if valid_student_ids is not None and student_input.student_id not in valid_student_ids:
                raise HTTPException(status_code=400, detail=f"Student {student_input.student_id} does not belong to batch {payload.batch_id}")

            for round_input in student_input.rounds:
                round_number = round_input.number
                key = (student_input.student_id, round_number)
                if key in seen_pairs:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duplicate round {round_number} supplied for student {student_input.student_id}",
                    )
                seen_pairs.add(key)

                for shot in round_input.shots:
                    results_to_create.append(
                        ArcheryResult(
                            session_id=session.id,
                            student_id=student_input.student_id,
                            round_number=round_number,
                            x_coordinate=shot.x_coordinate,
                            y_coordinate=shot.y_coordinate,
                            score=shot.score,
                            max_score=shot.max_score,
                            arrow_number=shot.arrow_number,
                        )
                    )
        
        if results_to_create:
            ArcheryResultRepository.create_all(db, results_to_create)

        # Return without refresh - reduces latency by avoiding extra DB round-trip
        return ArcheryService.serialize_session(db, session)

    @staticmethod
    def serialize_session(db: Session, session: ArcherySession) -> ArcherySessionResponse:
        # Build response manually to ensure all fields are populated

        results = session.results

        grouped_by_student: dict[int, dict[str, object]] = {}

        for r in results:
            entry = grouped_by_student.setdefault(
                r.student_id,
                {"student": r.student, "rounds": {}},
            )
            rounds_map: dict[int, List[ArcheryShotResponse]] = entry["rounds"]  # type: ignore[assignment]
            round_shots = rounds_map.setdefault(r.round_number, [])
            round_shots.append(ArcheryShotResponse.model_validate(r))

        final_results: List[ArcheryStudentRoundResponse] = []
        for student_id in sorted(grouped_by_student.keys()):
            data = grouped_by_student[student_id]
            student = data["student"]
            rounds_map = data["rounds"]  # type: ignore[assignment]

            round_responses: List[ArcheryRoundResponse] = []
            for round_number, shots in sorted(rounds_map.items(), key=lambda item: item[0]):
                shots.sort(key=lambda s: getattr(s, "arrow_number", 0))
                round_responses.append(
                    ArcheryRoundResponse(
                        number=round_number,
                        shots=shots,
                    )
                )

            final_results.append(
                ArcheryStudentRoundResponse(
                    student_id=student_id,
                    student=student,
                    rounds=round_responses,
                )
            )

        student_count = len(grouped_by_student)
        
        return ArcherySessionResponse(
            id=session.id,
            coach_id=session.coach_id,
            school_id=session.school_id,
            batch_id=session.batch_id,
            date_of_session=session.date_of_session,
             distance=session.distance,
            created_at=session.created_at,
            updated_at=session.updated_at,
            coach_name=session.coach.name if session.coach else None,
            batch=PhysicalAssessmentService._build_batch_summary(session.batch), # Reuse helper
            school=session.school,
             results=final_results,
            student_count=student_count,
        )

    @staticmethod
    def get_session_model(db: Session, session_id: int) -> Optional[ArcherySession]:
        return ArcherySessionRepository.get_by_id(db, session_id)

    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[ArcherySessionResponse]:
        session = ArcheryService.get_session_model(db, session_id)
        if not session:
            return None
        return ArcheryService.serialize_session(db, session)

    @staticmethod
    def get_admin_view_sessions(db: Session) -> ArcherySessionSummaryResponse:
        sessions = ArcherySessionRepository.get_all(db)
        summaries: List[ArcherySessionSummary] = []

        session_ids = [session.id for session in sessions]
        counts_map: dict[int, int] = {}
        if session_ids:
            count_rows = db.execute(
                select(
                    ArcheryResult.session_id,
                    func.count(func.distinct(ArcheryResult.student_id)).label("student_count"),
                )
                .where(ArcheryResult.session_id.in_(session_ids))
                .group_by(ArcheryResult.session_id)
            ).all()
            counts_map = {row.session_id: int(row.student_count or 0) for row in count_rows}

        for session in sessions:
            batch = session.batch
            school = session.school if session.school else (batch.school if batch else None)
            coach_name = session.coach.name if session.coach else None
            student_count = counts_map.get(session.id, 0)
            summaries.append(
                ArcherySessionSummary(
                    session_id=session.id,
                    batch_id=session.batch_id,
                    batch_name=batch.batch_name if batch else None,
                    school_id=session.school_id or (batch.school_id if batch else None),
                    school_name=school.name if school else None,
                    coach_id=session.coach_id,
                    coach_name=coach_name,
                    date_of_session=session.date_of_session,
                    distance=session.distance,
                    student_count=student_count,
                )
            )

        return ArcherySessionSummaryResponse(sessions=summaries)

    @staticmethod
    def get_coach_view_sessions(db: Session, coach_id: int) -> ArcherySessionSummaryResponse:
        assigned_batches_query = select(CoachBatch.batch_id).where(CoachBatch.coach_id == coach_id)
        assigned_batch_ids = list(db.scalars(assigned_batches_query).all())

        query = select(ArcherySession).where(
            (ArcherySession.coach_id == coach_id) | (ArcherySession.batch_id.in_(assigned_batch_ids))
        )
        sessions = db.scalars(query).all()

        summaries: List[ArcherySessionSummary] = []
        session_ids = [session.id for session in sessions]
        counts_map: dict[int, int] = {}
        if session_ids:
            count_rows = db.execute(
                select(
                    ArcheryResult.session_id,
                    func.count(func.distinct(ArcheryResult.student_id)).label("student_count"),
                )
                .where(ArcheryResult.session_id.in_(session_ids))
                .group_by(ArcheryResult.session_id)
            ).all()
            counts_map = {row.session_id: int(row.student_count or 0) for row in count_rows}
        for session in sessions:
            batch = session.batch
            school = session.school if session.school else (batch.school if batch else None)
            coach_name = session.coach.name if session.coach else None
            student_count = counts_map.get(session.id, 0)
            summaries.append(
                ArcherySessionSummary(
                    session_id=session.id,
                    batch_id=session.batch_id,
                    batch_name=batch.batch_name if batch else None,
                    school_id=session.school_id or (batch.school_id if batch else None),
                    school_name=school.name if school else None,
                    coach_id=session.coach_id,
                    coach_name=coach_name,
                    date_of_session=session.date_of_session,
                    distance=session.distance,
                    student_count=student_count,
                )
            )

        return ArcherySessionSummaryResponse(sessions=summaries)

    @staticmethod
    def update_session(db: Session, session_id: int, payload: ArcherySessionUpdate) -> Optional[ArcherySessionResponse]:
        session = ArcherySessionRepository.get_by_id(db, session_id)
        if not session:
            return None

        data = payload.model_dump(exclude_unset=True)
        results_payload = data.pop("results", None)

        if data:
            refs = PhysicalAssessmentService._resolve_relationships(
                db,
                coach_id=data.get("coach_id", session.coach_id),
                school_id=data.get("school_id", session.school_id),
                batch_id=data.get("batch_id", session.batch_id),
            )
            data.setdefault("coach_id", refs["coach_id"])
            data.setdefault("school_id", refs["school_id"])
            if "batch_id" in data and data["batch_id"] is None:
                data["batch_id"] = session.batch_id

            for key, value in data.items():
                setattr(session, key, value)

            db.commit()
            # Removed refresh - not needed and adds latency

        updated_session = session

        if results_payload is not None:
            target_batch_id = updated_session.batch_id
            valid_student_ids: Optional[set[int]] = None
            if target_batch_id:
                valid_student_ids = {student.id for student in StudentRepository.get_by_batch(db, target_batch_id)}

            ArcheryResultRepository.delete_by_session(db, updated_session.id)

            new_results: List[ArcheryResult] = []
            seen_pairs: set[tuple[int, int]] = set()
            for student_input in results_payload:
                if valid_student_ids is not None and student_input.student_id not in valid_student_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Student {student_input.student_id} does not belong to batch {target_batch_id}",
                    )

                for round_input in student_input.rounds:
                    round_number = round_input.number
                    key = (student_input.student_id, round_number)
                    if key in seen_pairs:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Duplicate round {round_number} supplied for student {student_input.student_id}",
                        )
                    seen_pairs.add(key)

                    for shot in round_input.shots:
                        new_results.append(
                            ArcheryResult(
                                session_id=updated_session.id,
                                student_id=student_input.student_id,
                                round_number=round_number,
                                x_coordinate=shot.x_coordinate,
                                y_coordinate=shot.y_coordinate,
                                score=shot.score,
                                max_score=shot.max_score,
                                arrow_number=shot.arrow_number,
                            )
                        )

            if new_results:
                ArcheryResultRepository.create_all(db, new_results)

            updated_session = ArcherySessionRepository.get_by_id(db, updated_session.id) or updated_session

        return ArcheryService.serialize_session(db, updated_session)

    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        session = ArcherySessionRepository.get_by_id(db, session_id)
        if not session:
            return False
        try:
            db.delete(session)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_admin_view_students(db: Session) -> ArcheryStudentSummaryResponse:
        stmt = (
            select(
                Student.id.label("student_id"),
                Student.name.label("student_name"),
                Student.batch_id.label("batch_id"),
                Batch.batch_name.label("batch_name"),
                Batch.school_id.label("school_id"),
                School.name.label("school_name"),
                func.count(func.distinct(ArcheryResult.session_id)).label("total_sessions"),
                func.count(ArcheryResult.id).label("total_shots"),
                func.avg(ArcheryResult.score).label("average_score"),
                func.max(ArcherySession.date_of_session).label("last_session_date"),
            )
            .outerjoin(ArcheryResult, ArcheryResult.student_id == Student.id)
            .outerjoin(ArcherySession, ArcherySession.id == ArcheryResult.session_id)
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
        summaries: List[ArcheryStudentSummary] = []

        for row in rows:
            avg_score = row.average_score
            summaries.append(
                ArcheryStudentSummary(
                    student_id=row.student_id,
                    student_name=row.student_name,
                    batch_id=row.batch_id,
                    batch_name=row.batch_name,
                    school_id=row.school_id,
                    school_name=row.school_name,
                    total_sessions=row.total_sessions or 0,
                    total_shots=row.total_shots or 0,
                    average_score=float(avg_score) if avg_score is not None else None,
                    last_session_date=row.last_session_date,
                )
            )

        return ArcheryStudentSummaryResponse(students=summaries)

    @staticmethod
    def get_coach_view_students(db: Session, coach_id: int) -> ArcheryStudentSummaryResponse:
        assigned_batches_query = select(CoachBatch.batch_id).where(CoachBatch.coach_id == coach_id)
        assigned_batch_ids = list(db.scalars(assigned_batches_query).all())
        if not assigned_batch_ids:
            return ArcheryStudentSummaryResponse(students=[])

        stmt = (
            select(
                Student.id.label("student_id"),
                Student.name.label("student_name"),
                Student.batch_id.label("batch_id"),
                Batch.batch_name.label("batch_name"),
                Batch.school_id.label("school_id"),
                School.name.label("school_name"),
                func.count(func.distinct(ArcheryResult.session_id)).label("total_sessions"),
                func.count(ArcheryResult.id).label("total_shots"),
                func.avg(ArcheryResult.score).label("average_score"),
                func.max(ArcherySession.date_of_session).label("last_session_date"),
            )
            .outerjoin(ArcheryResult, ArcheryResult.student_id == Student.id)
            .outerjoin(ArcherySession, ArcherySession.id == ArcheryResult.session_id)
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
        summaries: List[ArcheryStudentSummary] = []

        for row in rows:
            avg_score = row.average_score
            summaries.append(
                ArcheryStudentSummary(
                    student_id=row.student_id,
                    student_name=row.student_name,
                    batch_id=row.batch_id,
                    batch_name=row.batch_name,
                    school_id=row.school_id,
                    school_name=row.school_name,
                    total_sessions=row.total_sessions or 0,
                    total_shots=row.total_shots or 0,
                    average_score=float(avg_score) if avg_score is not None else None,
                    last_session_date=row.last_session_date,
                )
            )

        return ArcheryStudentSummaryResponse(students=summaries)

    @staticmethod
    def get_student_detail(db: Session, student_id: int) -> Optional[ArcheryStudentDetailResponse]:
        student = StudentRepository.get_by_id(db, student_id)
        if not student:
            return None

        batch = getattr(student, "batch", None)
        school = getattr(batch, "school", None) if batch else None

        results = ArcheryResultRepository.get_by_student(db, student_id)
        grouped: dict[int, dict[int, list[ArcheryResult]]] = defaultdict(lambda: defaultdict(list))

        for result in results:
            grouped[result.session_id][result.round_number].append(result)

        session_details: List[ArcheryStudentSessionDetail] = []
        for session_id, rounds_map in grouped.items():
            sample_rounds = next(iter(rounds_map.values())) if rounds_map else []
            sample_session = sample_rounds[0].session if sample_rounds and sample_rounds[0].session else None
            session = sample_session or ArcherySessionRepository.get_by_id(db, session_id)
            if not session:
                continue
            coach_name = session.coach.name if session.coach else None

            round_responses: List[ArcheryRoundResponse] = []
            for round_number, shots in sorted(rounds_map.items(), key=lambda item: item[0]):
                shot_responses = [
                    ArcheryShotResponse.model_validate(shot)
                    for shot in sorted(shots, key=lambda s: s.arrow_number)
                ]
                round_responses.append(
                    ArcheryRoundResponse(
                        number=round_number,
                        shots=shot_responses,
                    )
                )

            session_details.append(
                ArcheryStudentSessionDetail(
                    session_id=session.id,
                    date_of_session=session.date_of_session,
                    coach_id=session.coach_id,
                    coach_name=coach_name,
                    distance=session.distance,
                    rounds=round_responses,
                )
            )

        session_details.sort(key=lambda item: item.date_of_session)

        return ArcheryStudentDetailResponse(
            student_id=student.id,
            student_name=student.name,
            batch_id=student.batch_id,
            batch_name=batch.batch_name if batch else None,
            school_id=batch.school_id if batch else None,
            school_name=school.name if school else None,
            sessions=session_details,
        )

    @staticmethod
    def update_student_results(
        db: Session,
        student_id: int,
        payload: ArcheryStudentUpdate,
    ) -> ArcheryStudentDetailResponse:
        student = StudentRepository.get_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        if not payload.updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="updates must include at least one entry")

        for update in payload.updates:
            session = ArcherySessionRepository.get_by_id(db, update.session_id)
            if not session:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {update.session_id} not found")

            if session.batch_id != student.batch_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student does not belong to session batch")

            ArcheryResultRepository.delete_for_student_in_session(db, update.session_id, student_id)

            new_results: List[ArcheryResult] = []
            seen_rounds: set[int] = set()
            for round_input in update.rounds:
                if round_input.number in seen_rounds:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duplicate round {round_input.number} supplied for session {update.session_id}",
                    )
                seen_rounds.add(round_input.number)

                for shot in round_input.shots:
                    new_results.append(
                        ArcheryResult(
                            session_id=update.session_id,
                            student_id=student_id,
                            round_number=round_input.number,
                            x_coordinate=shot.x_coordinate,
                            y_coordinate=shot.y_coordinate,
                            score=shot.score,
                            max_score=shot.max_score,
                            arrow_number=shot.arrow_number,
                        )
                    )

            if new_results:
                ArcheryResultRepository.create_all(db, new_results)

        return ArcheryService.get_student_detail(db, student_id)

    @staticmethod
    def delete_student_results(db: Session, student_id: int) -> bool:
        student = StudentRepository.get_by_id(db, student_id)
        if not student:
            return False

        deleted = ArcheryResultRepository.delete_by_student(db, student_id)
        return deleted > 0

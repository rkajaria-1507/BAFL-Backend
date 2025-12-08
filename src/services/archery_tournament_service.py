from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models.archery_tournament import (
    ArcheryTournamentCategory,
    ArcheryTournamentResult,
    ArcheryTournamentSession,
)
from src.db.models.coach_batch import CoachBatch
from src.db.repositories.archery_tournament_repository import (
    ArcheryTournamentCategoryRepository,
    ArcheryTournamentResultRepository,
    ArcheryTournamentSessionRepository,
)
from src.db.repositories.student_repository import StudentRepository
from src.schemas.archery import ArcheryShotResponse, ArcheryStudentRoundResponse, ArcheryRoundResponse
from src.schemas.archery_tournament import (
    ArcheryTournamentCategoryCreate,
    ArcheryTournamentCategoryResponse,
    ArcheryTournamentPreCreateResponse,
    ArcheryTournamentSessionCreate,
    ArcheryTournamentSessionResponse,
    ArcheryTournamentSessionSummary,
    ArcheryTournamentSessionSummaryResponse,
    ArcheryTournamentSessionUpdate,
)
from src.schemas.physical_assessment import PreCreateResponse
from src.services.physical_assessment_service import PhysicalAssessmentService


class ArcheryTournamentService:
    @staticmethod
    def _validate_category(db: Session, category_id: Optional[int]) -> Optional[ArcheryTournamentCategory]:
        if category_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="category_id is required")
        category = ArcheryTournamentCategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    @staticmethod
    def get_pre_create_data(db: Session, user) -> ArcheryTournamentPreCreateResponse:
        base: PreCreateResponse = PhysicalAssessmentService.get_pre_create_data(db, user)
        categories = [
            ArcheryTournamentCategoryResponse.model_validate(cat)
            for cat in ArcheryTournamentCategoryRepository.get_all(db)
        ]
        return ArcheryTournamentPreCreateResponse(batches=base.batches, categories=categories)

    @staticmethod
    def create_category(db: Session, payload: ArcheryTournamentCategoryCreate) -> ArcheryTournamentCategoryResponse:
        existing = ArcheryTournamentCategoryRepository.get_by_name(db, payload.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")
        category = ArcheryTournamentCategory(name=payload.name, description=payload.description)
        category = ArcheryTournamentCategoryRepository.create(db, category)
        return ArcheryTournamentCategoryResponse.model_validate(category)

    @staticmethod
    def delete_category(db: Session, category_id: int) -> None:
        deleted = ArcheryTournamentCategoryRepository.delete(db, category_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    @staticmethod
    def create_session(db: Session, payload: ArcheryTournamentSessionCreate) -> ArcheryTournamentSessionResponse:
        category = ArcheryTournamentService._validate_category(db, payload.category_id)
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

        session = ArcheryTournamentSession(
            batch_id=payload.batch_id,
            coach_id=refs["coach_id"],
            school_id=refs["school_id"],
            category_id=payload.category_id,
            tournament_name=payload.tournament_name,
            tournament_location=payload.tournament_location,
            category_name_snapshot=category.name,
            date_of_session=payload.date_of_session,
            distance=payload.distance,
        )
        session = ArcheryTournamentSessionRepository.create(db, session)

        seen_pairs: set[tuple[int, int]] = set()
        results_to_create: List[ArcheryTournamentResult] = []
        for student_input in payload.results:
            if valid_student_ids is not None and student_input.student_id not in valid_student_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student {student_input.student_id} does not belong to batch {payload.batch_id}",
                )
            for round_input in student_input.rounds:
                key = (student_input.student_id, round_input.number)
                if key in seen_pairs:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duplicate round {round_input.number} supplied for student {student_input.student_id}",
                    )
                seen_pairs.add(key)
                for shot in round_input.shots:
                    results_to_create.append(
                        ArcheryTournamentResult(
                            session_id=session.id,
                            student_id=student_input.student_id,
                            round_number=round_input.number,
                            x_coordinate=shot.x_coordinate,
                            y_coordinate=shot.y_coordinate,
                            score=shot.score,
                            max_score=shot.max_score,
                            arrow_number=shot.arrow_number,
                        )
                    )

        if results_to_create:
            ArcheryTournamentResultRepository.create_all(db, results_to_create)

        db.refresh(session)
        return ArcheryTournamentService.serialize_session(db, session)

    @staticmethod
    def serialize_session(db: Session, session: ArcheryTournamentSession) -> ArcheryTournamentSessionResponse:
        results = session.results
        grouped: dict[int, dict[str, object]] = {}

        for result in results:
            entry = grouped.setdefault(
                result.student_id,
                {"student": result.student, "rounds": {}},
            )
            rounds_map = entry["rounds"]  # type: ignore[assignment]
            shots = rounds_map.setdefault(result.round_number, [])
            shots.append(ArcheryShotResponse.model_validate(result))

        formatted_results: List[ArcheryStudentRoundResponse] = []
        for student_id in sorted(grouped.keys()):
            data = grouped[student_id]
            student = data["student"]
            rounds_map = data["rounds"]  # type: ignore[assignment]
            round_responses: List[ArcheryRoundResponse] = []
            for round_number, shots in sorted(rounds_map.items(), key=lambda item: item[0]):
                shots.sort(key=lambda shot: getattr(shot, "arrow_number", 0))
                round_responses.append(
                    ArcheryRoundResponse(
                        number=round_number,
                        shots=shots,
                    )
                )
            formatted_results.append(
                ArcheryStudentRoundResponse(
                    student_id=student_id,
                    student=student,
                    rounds=round_responses,
                )
            )

        student_count = len(grouped)

        category = session.category
        category_response = (
            ArcheryTournamentCategoryResponse.model_validate(category)
            if category
            else None
        )

        return ArcheryTournamentSessionResponse(
            id=session.id,
            coach_id=session.coach_id,
            school_id=session.school_id,
            batch_id=session.batch_id,
            category_id=session.category_id,
            tournament_name=session.tournament_name,
            tournament_location=session.tournament_location,
            distance=session.distance,
            date_of_session=session.date_of_session,
            created_at=session.created_at,
            updated_at=session.updated_at,
            coach_name=session.coach.name if session.coach else None,
            batch=PhysicalAssessmentService._build_batch_summary(session.batch),
            school=session.school,
            category=category_response,
            category_name_snapshot=session.category_name_snapshot,
            results=formatted_results,
            student_count=student_count,
        )

    @staticmethod
    def get_session_model(db: Session, session_id: int) -> Optional[ArcheryTournamentSession]:
        return ArcheryTournamentSessionRepository.get_by_id(db, session_id)

    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[ArcheryTournamentSessionResponse]:
        session = ArcheryTournamentService.get_session_model(db, session_id)
        if not session:
            return None
        return ArcheryTournamentService.serialize_session(db, session)

    @staticmethod
    def get_admin_view_sessions(db: Session) -> ArcheryTournamentSessionSummaryResponse:
        sessions = ArcheryTournamentSessionRepository.get_all(db)
        session_ids = [session.id for session in sessions]

        counts_map: dict[int, int] = {}
        if session_ids:
            rows = db.execute(
                select(
                    ArcheryTournamentResult.session_id,
                    func.count(func.distinct(ArcheryTournamentResult.student_id)).label("student_count"),
                )
                .where(ArcheryTournamentResult.session_id.in_(session_ids))
                .group_by(ArcheryTournamentResult.session_id)
            ).all()
            counts_map = {row.session_id: int(row.student_count or 0) for row in rows}

        summaries: List[ArcheryTournamentSessionSummary] = []
        for session in sessions:
            batch = session.batch
            school = session.school if session.school else (batch.school if batch else None)
            category_name = session.category.name if session.category else session.category_name_snapshot
            summaries.append(
                ArcheryTournamentSessionSummary(
                    session_id=session.id,
                    batch_id=session.batch_id,
                    batch_name=batch.batch_name if batch else None,
                    school_id=session.school_id or (batch.school_id if batch else None),
                    school_name=school.name if school else None,
                    coach_id=session.coach_id,
                    coach_name=session.coach.name if session.coach else None,
                    category_id=session.category_id,
                    category_name=category_name,
                    tournament_name=session.tournament_name,
                    tournament_location=session.tournament_location,
                    date_of_session=session.date_of_session,
                    distance=session.distance,
                    student_count=counts_map.get(session.id, 0),
                )
            )

        return ArcheryTournamentSessionSummaryResponse(sessions=summaries)

    @staticmethod
    def get_coach_view_sessions(db: Session, coach_id: int) -> ArcheryTournamentSessionSummaryResponse:
        assigned_batch_ids = list(
            db.scalars(select(CoachBatch.batch_id).where(CoachBatch.coach_id == coach_id)).all()
        )
        query = select(ArcheryTournamentSession).where(
            (ArcheryTournamentSession.coach_id == coach_id)
            | (ArcheryTournamentSession.batch_id.in_(assigned_batch_ids))
        )
        sessions = db.scalars(query).all()

        session_ids = [session.id for session in sessions]
        counts_map: dict[int, int] = {}
        if session_ids:
            rows = db.execute(
                select(
                    ArcheryTournamentResult.session_id,
                    func.count(func.distinct(ArcheryTournamentResult.student_id)).label("student_count"),
                )
                .where(ArcheryTournamentResult.session_id.in_(session_ids))
                .group_by(ArcheryTournamentResult.session_id)
            ).all()
            counts_map = {row.session_id: int(row.student_count or 0) for row in rows}

        summaries: List[ArcheryTournamentSessionSummary] = []
        for session in sessions:
            batch = session.batch
            school = session.school if session.school else (batch.school if batch else None)
            category_name = session.category.name if session.category else session.category_name_snapshot
            summaries.append(
                ArcheryTournamentSessionSummary(
                    session_id=session.id,
                    batch_id=session.batch_id,
                    batch_name=batch.batch_name if batch else None,
                    school_id=session.school_id or (batch.school_id if batch else None),
                    school_name=school.name if school else None,
                    coach_id=session.coach_id,
                    coach_name=session.coach.name if session.coach else None,
                    category_id=session.category_id,
                    category_name=category_name,
                    tournament_name=session.tournament_name,
                    tournament_location=session.tournament_location,
                    date_of_session=session.date_of_session,
                    distance=session.distance,
                    student_count=counts_map.get(session.id, 0),
                )
            )

        return ArcheryTournamentSessionSummaryResponse(sessions=summaries)

    @staticmethod
    def update_session(
        db: Session,
        session_id: int,
        payload: ArcheryTournamentSessionUpdate,
    ) -> Optional[ArcheryTournamentSessionResponse]:
        session = ArcheryTournamentSessionRepository.get_by_id(db, session_id)
        if not session:
            return None

        data = payload.model_dump(exclude_unset=True)
        results_payload = data.pop("results", None)

        if "category_id" in data:
            category = ArcheryTournamentService._validate_category(db, data["category_id"])
            session.category_id = category.id
            session.category_name_snapshot = category.name

        refs = PhysicalAssessmentService._resolve_relationships(
            db,
            coach_id=data.get("coach_id", session.coach_id),
            school_id=data.get("school_id", session.school_id),
            batch_id=data.get("batch_id", session.batch_id),
        )
        resolved_coach_id = refs["coach_id"]
        resolved_school_id = refs["school_id"]

        if "coach_id" in data or ("batch_id" in data and resolved_coach_id is not None):
            session.coach_id = resolved_coach_id
        if "school_id" in data or "batch_id" in data:
            session.school_id = resolved_school_id
        if "batch_id" in data:
            session.batch_id = data["batch_id"]

        for field in [
            "tournament_name",
            "tournament_location",
            "date_of_session",
            "distance",
        ]:
            if field in data:
                setattr(session, field, data[field])

        db.commit()
        db.refresh(session)

        if results_payload is not None:
            target_batch_id = session.batch_id
            valid_student_ids: Optional[set[int]] = None
            if target_batch_id:
                valid_student_ids = {student.id for student in StudentRepository.get_by_batch(db, target_batch_id)}

            ArcheryTournamentResultRepository.delete_by_session(db, session.id)

            new_results: List[ArcheryTournamentResult] = []
            seen_pairs: set[tuple[int, int]] = set()
            for student_input in results_payload:
                if valid_student_ids is not None and student_input.student_id not in valid_student_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Student {student_input.student_id} does not belong to batch {target_batch_id}",
                    )
                for round_input in student_input.rounds:
                    key = (student_input.student_id, round_input.number)
                    if key in seen_pairs:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Duplicate round {round_input.number} supplied for student {student_input.student_id}",
                        )
                    seen_pairs.add(key)
                    for shot in round_input.shots:
                        new_results.append(
                            ArcheryTournamentResult(
                                session_id=session.id,
                                student_id=student_input.student_id,
                                round_number=round_input.number,
                                x_coordinate=shot.x_coordinate,
                                y_coordinate=shot.y_coordinate,
                                score=shot.score,
                                max_score=shot.max_score,
                                arrow_number=shot.arrow_number,
                            )
                        )

            if new_results:
                ArcheryTournamentResultRepository.create_all(db, new_results)

            session = ArcheryTournamentSessionRepository.get_by_id(db, session.id) or session

        return ArcheryTournamentService.serialize_session(db, session)

    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        session = ArcheryTournamentSessionRepository.get_by_id(db, session_id)
        if not session:
            return False
        try:
            db.delete(session)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

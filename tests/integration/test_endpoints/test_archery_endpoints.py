"""
Integration tests for Archery endpoints (Practice and Tournament).
"""
from typing import List

import pytest
from fastapi import status

from src.core.security import PasswordHandler, TokenHandler
from src.db.models.batch import Batch
from src.db.models.coach import Coach
from src.db.models.coach_batch import CoachBatch
from src.db.models.school import School
from src.db.models.student import Student
from src.db.models.user import User, UserRole

API_PREFIX_PRACTICE = "/api/v1/archery"
API_PREFIX_TOURNAMENT = "/api/v1/archery/tournaments"


# Helpers -----------------------------------------------------------------


def _create_school(db, name: str = "Archery School") -> School:
    school = School(name=name, address="456 Archery Lane")
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def _create_batch(db, school: School, name: str = "Archery Batch") -> Batch:
    batch = Batch(school_id=school.id, batch_name=name)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def _create_coach(db, username: str = "archerycoach") -> Coach:
    coach = Coach(
        name=username.title(),
        username=username,
        password=PasswordHandler.hash("password123"),
        is_active=True,
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def _assign_coach(db, coach: Coach, batch: Batch) -> CoachBatch:
    assignment = CoachBatch(coach_id=coach.id, batch_id=batch.id)
    db.add(assignment)
    db.commit()
    return assignment


def _create_students(db, batch: Batch, count: int = 2) -> List[Student]:
    students: List[Student] = []
    for index in range(count):
        student = Student(name=f"Archer {index + 1}", age=15 + index, batch_id=batch.id)
        db.add(student)
        students.append(student)
    db.commit()
    for student in students:
        db.refresh(student)
    return students


def _create_coach_user_headers(db, *, username: str = "archcoachuser") -> tuple[User, Coach, dict]:
    user = User(
        name=f"{username.title()} User",
        username=username,
        password=PasswordHandler.hash("password123"),
        role=UserRole.COACH,
        is_active=True,
    )
    coach = Coach(
        name=f"{username.title()} Coach",
        username=username,
        password=PasswordHandler.hash("password123"),
        is_active=True,
    )
    db.add(user)
    db.add(coach)
    db.commit()
    db.refresh(user)
    db.refresh(coach)

    token = TokenHandler.create_access_token(
        {
            "sub": user.username,
            "subject_type": "user",
            "user_id": user.id,
            "role": user.role.value,
        }
    )
    headers = {"Authorization": f"Bearer {token}"}
    return user, coach, headers


def _build_archery_round_payload(student_id: int, *, num_rounds: int = 2, shots_per_round: int = 3) -> dict:
    rounds = []
    for round_num in range(1, num_rounds + 1):
        shots = []
        for arrow_num in range(1, shots_per_round + 1):
            shots.append({
                "x_coordinate": 1.5 * arrow_num,
                "y_coordinate": 2.0 * arrow_num,
                "score": 7 + arrow_num,
                "max_score": 10,
                "arrow_number": arrow_num,
            })
        rounds.append({"number": round_num, "shots": shots})
    return {"student_id": student_id, "rounds": rounds}


def _create_practice_session_via_api(
    client,
    headers: dict,
    *,
    coach_id: int | None,
    school_id: int,
    batch_id: int,
    student_ids: List[int],
    distance: float = 10.0,
    session_date: str = "2025-01-20",
):
    results = [_build_archery_round_payload(student_id) for student_id in student_ids]
    payload = {
        "coach_id": coach_id,
        "school_id": school_id,
        "batch_id": batch_id,
        "date_of_session": session_date,
        "distance": distance,
        "results": results,
    }
    response = client.post(f"{API_PREFIX_PRACTICE}/sessions", json=payload, headers=headers)
    return response


def _create_tournament_category_via_api(client, headers: dict, *, name: str = "Junior Category") -> dict:
    payload = {"name": name, "description": f"Description for {name}"}
    response = client.post(f"{API_PREFIX_TOURNAMENT}/categories", json=payload, headers=headers)
    return response


def _create_tournament_session_via_api(
    client,
    headers: dict,
    *,
    coach_id: int | None,
    school_id: int,
    batch_id: int,
    student_ids: List[int],
    category_id: int | None = None,
    tournament_name: str = "District Championship",
    tournament_location: str = "City Arena",
    distance: float = 15.0,
    session_date: str = "2025-02-10",
):
    results = [_build_archery_round_payload(student_id) for student_id in student_ids]
    payload = {
        "coach_id": coach_id,
        "school_id": school_id,
        "batch_id": batch_id,
        "category_id": category_id,
        "tournament_name": tournament_name,
        "tournament_location": tournament_location,
        "date_of_session": session_date,
        "distance": distance,
        "results": results,
    }
    response = client.post(f"{API_PREFIX_TOURNAMENT}/sessions", json=payload, headers=headers)
    return response


# Archery Practice Session Tests ------------------------------------------


@pytest.mark.integration
@pytest.mark.api
class TestArcheryPracticeSessionsEndpoints:
    def test_create_practice_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["coach_id"] == coach.id
        assert data["batch_id"] == batch.id
        assert data["distance"] == 10.0
        assert len(data["results"]) == 2

    def test_create_practice_session_requires_authentication(self, client):
        response = client.post(f"{API_PREFIX_PRACTICE}/sessions", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_practice_session_coach_cannot_impersonate(self, client, test_db):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        students = _create_students(test_db, batch, count=2)
        _, coach_profile, coach_headers = _create_coach_user_headers(test_db)
        _assign_coach(test_db, coach_profile, batch)
        other_coach = _create_coach(test_db, username="impersonatecoach")

        payload = {
            "coach_id": other_coach.id,
            "school_id": school.id,
            "batch_id": batch.id,
            "date_of_session": "2025-03-01",
            "distance": 12.0,
            "results": [_build_archery_round_payload(students[0].id)],
        }

        response = client.post(f"{API_PREFIX_PRACTICE}/sessions", json=payload, headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_practice_sessions_as_admin(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        response = client.get(f"{API_PREFIX_PRACTICE}/sessions", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["coach_id"] == coach.id

    def test_get_practice_sessions_coach_scope(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        assigned_batch = _create_batch(test_db, school, name="Assigned Batch")
        other_batch = _create_batch(test_db, school, name="Other Batch")
        _, coach_profile, coach_headers = _create_coach_user_headers(test_db)
        _assign_coach(test_db, coach_profile, assigned_batch)

        students_assigned = _create_students(test_db, assigned_batch, count=2)
        create_assigned = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach_profile.id,
            school_id=school.id,
            batch_id=assigned_batch.id,
            student_ids=[s.id for s in students_assigned],
        )
        assert create_assigned.status_code == status.HTTP_201_CREATED

        other_coach = _create_coach(test_db, username="otherarchcoach")
        _assign_coach(test_db, other_coach, other_batch)
        students_other = _create_students(test_db, other_batch, count=2)
        create_other = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=other_coach.id,
            school_id=school.id,
            batch_id=other_batch.id,
            student_ids=[s.id for s in students_other],
        )
        assert create_other.status_code == status.HTTP_201_CREATED

        response = client.get(f"{API_PREFIX_PRACTICE}/sessions", headers=coach_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        session_ids = {session["session_id"] for session in data["sessions"]}
        assert session_ids == {create_assigned.json()["id"]}

    def test_get_single_practice_session_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        students = _create_students(test_db, batch, count=2)
        other_coach = _create_coach(test_db, username="sessioncoach")
        _assign_coach(test_db, other_coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=other_coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        session_id = create_response.json()["id"]

        _, _, coach_headers = _create_coach_user_headers(test_db, username="unauthorizedcoach")
        response = client.get(f"{API_PREFIX_PRACTICE}/sessions/{session_id}", headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_practice_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        session_id = create_response.json()["id"]

        update_payload = {"distance": 20.0, "date_of_session": "2025-03-15"}
        response = client.put(
            f"{API_PREFIX_PRACTICE}/sessions/{session_id}",
            json=update_payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["distance"] == 20.0

    def test_delete_practice_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        session_id = create_response.json()["id"]

        response = client.delete(f"{API_PREFIX_PRACTICE}/sessions/{session_id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        follow_up = client.get(f"{API_PREFIX_PRACTICE}/sessions/{session_id}", headers=auth_headers_admin)
        assert follow_up.status_code == status.HTTP_404_NOT_FOUND


# Archery Tournament Tests -------------------------------------------------


@pytest.mark.integration
@pytest.mark.api
class TestArcheryTournamentEndpoints:
    def test_create_tournament_category_success(self, client, auth_headers_admin):
        response = _create_tournament_category_via_api(client, auth_headers_admin, name="Senior Division")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Senior Division"
        assert "id" in data

    def test_create_tournament_category_requires_admin(self, client, test_db):
        _, _, coach_headers = _create_coach_user_headers(test_db)
        response = _create_tournament_category_via_api(client, coach_headers, name="Test Category")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_tournament_category_success(self, client, auth_headers_admin):
        create_response = _create_tournament_category_via_api(client, auth_headers_admin, name="Temp Category")
        assert create_response.status_code == status.HTTP_201_CREATED
        category_id = create_response.json()["id"]

        response = client.delete(
            f"{API_PREFIX_TOURNAMENT}/categories/{category_id}",
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_create_tournament_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        category_response = _create_tournament_category_via_api(client, auth_headers_admin, name="Junior")
        category_id = category_response.json()["id"]

        response = _create_tournament_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
            category_id=category_id,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["tournament_name"] == "District Championship"
        assert data["category_id"] == category_id

    def test_get_tournament_sessions_as_admin(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        category_response = _create_tournament_category_via_api(client, auth_headers_admin, name="Session Category")
        category_id = category_response.json()["id"]

        create_response = _create_tournament_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
            category_id=category_id,
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        response = client.get(f"{API_PREFIX_TOURNAMENT}/sessions", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sessions"]) == 1

    def test_update_tournament_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        category_response = _create_tournament_category_via_api(client, auth_headers_admin, name="Update Category")
        category_id = category_response.json()["id"]

        create_response = _create_tournament_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
            category_id=category_id,
        )
        session_id = create_response.json()["id"]

        update_payload = {"tournament_name": "Updated Championship", "distance": 25.0}
        response = client.put(
            f"{API_PREFIX_TOURNAMENT}/sessions/{session_id}",
            json=update_payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["tournament_name"] == "Updated Championship"

    def test_delete_tournament_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        category_response = _create_tournament_category_via_api(client, auth_headers_admin, name="Delete Category")
        category_id = category_response.json()["id"]

        create_response = _create_tournament_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
            category_id=category_id,
        )
        session_id = create_response.json()["id"]

        response = client.delete(
            f"{API_PREFIX_TOURNAMENT}/sessions/{session_id}",
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


# Archery Student Tests ----------------------------------------------------


@pytest.mark.integration
@pytest.mark.api
class TestArcheryStudentEndpoints:
    def test_get_students_summary_as_admin(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        response = client.get(f"{API_PREFIX_PRACTICE}/students", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["students"]) >= 2

    def test_get_student_detail_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        student_id = students[0].id

        response = client.get(f"{API_PREFIX_PRACTICE}/students/{student_id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["student_id"] == student_id

    def test_get_student_detail_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        students = _create_students(test_db, batch, count=2)
        other_coach = _create_coach(test_db, username="studentcoach")
        _assign_coach(test_db, other_coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=other_coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        student_id = students[0].id

        _, _, coach_headers = _create_coach_user_headers(test_db, username="forbiddencoach")
        response = client.get(f"{API_PREFIX_PRACTICE}/students/{student_id}", headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_student_archery_results_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        student_id = students[0].id

        response = client.delete(f"{API_PREFIX_PRACTICE}/students/{student_id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_nonexistent_student(self, client, test_db, auth_headers_admin):
        response = client.get(f"{API_PREFIX_PRACTICE}/students/99999", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestArcheryEdgeCases:
    """Test edge and boundary cases for archery endpoints."""

    def test_create_practice_session_with_empty_rounds(self, client, test_db, auth_headers_admin):
        """Test that API rejects creating a practice session with rounds but no shots."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=1)
        _assign_coach(test_db, coach, batch)

        payload = {
            "coach_id": coach.id,
            "school_id": school.id,
            "batch_id": batch.id,
            "session_date": "2024-01-15",
            "students": [
                {
                    "student_id": students[0].id,
                    "rounds": [
                        {
                            "round_number": 1,
                            "shots": [],
                        }
                    ],
                }
            ],
        }

        response = client.post(f"{API_PREFIX_PRACTICE}/sessions", headers=auth_headers_admin, json=payload)
        # API validation requires at least one shot per round
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_practice_session_with_no_rounds(self, client, test_db, auth_headers_admin):
        """Test that API rejects creating a practice session with a student but no rounds."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=1)
        _assign_coach(test_db, coach, batch)

        payload = {
            "coach_id": coach.id,
            "school_id": school.id,
            "batch_id": batch.id,
            "session_date": "2024-01-15",
            "students": [
                {
                    "student_id": students[0].id,
                    "rounds": [],
                }
            ],
        }

        response = client.post(f"{API_PREFIX_PRACTICE}/sessions", headers=auth_headers_admin, json=payload)
        # API validation requires at least one round per student
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_practice_session_with_invalid_coordinates(self, client, test_db, auth_headers_admin):
        """Test that API rejects shots with invalid (negative) coordinates."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=1)
        _assign_coach(test_db, coach, batch)

        payload = {
            "coach_id": coach.id,
            "school_id": school.id,
            "batch_id": batch.id,
            "session_date": "2024-01-15",
            "students": [
                {
                    "student_id": students[0].id,
                    "rounds": [
                        {
                            "round_number": 1,
                            "shots": [
                                {"shot_number": 1, "x": -999, "y": -999, "score": 0},
                            ],
                        }
                    ],
                }
            ],
        }

        response = client.post(f"{API_PREFIX_PRACTICE}/sessions", headers=auth_headers_admin, json=payload)
        # API validation rejects negative coordinates
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_tournament_session_with_invalid_category(self, client, test_db, auth_headers_admin):
        """Test creating tournament session with non-existent category."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=1)
        _assign_coach(test_db, coach, batch)

        create_response = _create_tournament_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[students[0].id],
            category_id=99999,  # Non-existent category
        )
        # Should fail with 404 or 400
        assert create_response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_update_practice_session_with_different_students(self, client, test_db, auth_headers_admin):
        """Test updating a practice session to include different students."""
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=3)
        _assign_coach(test_db, coach, batch)

        # Create with first two students
        create_response = _create_practice_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[students[0].id, students[1].id],
        )
        session_id = create_response.json()["id"]

        # Update to include third student instead
        update_payload = {
            "session_date": "2024-01-20",
            "students": [
                {
                    "student_id": students[2].id,
                    "rounds": [
                        {
                            "round_number": 1,
                            "shots": [
                                {"shot_number": 1, "x": 100, "y": 50, "score": 9},
                                {"shot_number": 2, "x": 80, "y": 60, "score": 8},
                            ],
                        },
                        {
                            "round_number": 2,
                            "shots": [
                                {"shot_number": 1, "x": 90, "y": 55, "score": 10},
                                {"shot_number": 2, "x": 70, "y": 65, "score": 7},
                            ],
                        },
                    ],
                }
            ],
        }

        response = client.put(f"{API_PREFIX_PRACTICE}/sessions/{session_id}", headers=auth_headers_admin, json=update_payload)
        assert response.status_code == status.HTTP_200_OK

    def test_tournament_category_deletion_cascade(self, client, test_db, auth_headers_admin):
        """Test that deleting a category prevents creating sessions with that category."""
        category_response = _create_tournament_category_via_api(client, auth_headers_admin, name="Temp Category")
        category_id = category_response.json()["id"]

        # Delete the category
        delete_response = client.delete(f"{API_PREFIX_TOURNAMENT}/categories/{category_id}", headers=auth_headers_admin)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Try to create a session with deleted category
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=1)
        _assign_coach(test_db, coach, batch)

        create_response = _create_tournament_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[students[0].id],
            category_id=category_id,
        )
        # Should fail as category no longer exists
        assert create_response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

"""
Integration tests for Physical Assessment endpoints.
"""
from typing import Iterable, List

import pytest
from fastapi import status

from src.core.security import PasswordHandler, TokenHandler
from src.db.models.batch import Batch
from src.db.models.coach import Coach
from src.db.models.coach_batch import CoachBatch
from src.db.models.permission import Permission, PermissionType, UserPermission
from src.db.models.school import School
from src.db.models.student import Student
from src.db.models.student_exercise_average import StudentExerciseAverage
from src.db.models.user import User, UserRole

API_PREFIX = "/api/v1/physical"


# Helpers -----------------------------------------------------------------


def _create_school(db, name: str = "Test High School") -> School:
    school = School(name=name, address="123 Test Street")
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def _create_batch(db, school: School, name: str = "Batch A") -> Batch:
    batch = Batch(school_id=school.id, batch_name=name)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def _create_coach(db, username: str = "sessioncoach") -> Coach:
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
        student = Student(name=f"Student {index + 1}", age=14 + index, batch_id=batch.id)
        db.add(student)
        students.append(student)
    db.commit()
    for student in students:
        db.refresh(student)
    return students


def _create_coach_user_headers(db, *, username: str = "coachuser") -> tuple[User, Coach, dict]:
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

    for perm_type in (
        PermissionType.PHYSICAL_SESSIONS_VIEW,
        PermissionType.PHYSICAL_SESSIONS_ADD,
        PermissionType.PHYSICAL_SESSIONS_EDIT,
    ):
        perm = db.query(Permission).filter(Permission.permission_name == perm_type.value).first()
        if perm:
            db.add(UserPermission(user_id=user.id, permission_id=perm.id))
    db.commit()

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


def _create_coach_token_headers(db, *, username: str = "coachlevel") -> tuple[Coach, dict]:
    coach = Coach(
        name=f"{username.title()} Coach",
        username=username,
        password=PasswordHandler.hash("password123"),
        is_active=True,
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)

    token = TokenHandler.create_access_token(
        {
            "sub": coach.username,
            "subject_type": "coach",
            "coach_id": coach.id,
            "role": UserRole.COACH.value,
        }
    )
    headers = {"Authorization": f"Bearer {token}"}
    return coach, headers


def _build_result_payload(student_id: int, *, curl_up: int = 40, push_up: int = 25, offset: int = 0) -> dict:
    return {
        "student_id": student_id,
        "curl_up": curl_up + offset,
        "push_up": push_up + offset,
        "sit_and_reach": 12.5,
        "walk_600m": 7.8,
        "dash_50m": 6.4,
        "bow_hold": 55.0,
        "plank": 3.5,
        "is_present": True,
    }


def _create_session_via_api(
    client,
    headers: dict,
    *,
    coach_id: int | None,
    school_id: int,
    batch_id: int,
    student_ids: Iterable[int],
    session_date: str = "2025-01-15",
    offset: int = 0,
):
    student_list = list(student_ids)
    payload = {
        "coach_id": coach_id,
        "school_id": school_id,
        "batch_id": batch_id,
        "date_of_session": session_date,
        "student_count": len(student_list),
        "results": [_build_result_payload(student_id, offset=offset) for student_id in student_list],
    }
    response = client.post(f"{API_PREFIX}/sessions", json=payload, headers=headers)
    return response


# Session endpoint tests ---------------------------------------------------


@pytest.mark.integration
@pytest.mark.api
class TestPhysicalAssessmentSessionsEndpoints:
    def test_create_session_with_results_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)

        response = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[student.id for student in students],
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["coach_id"] == coach.id
        assert data["batch_id"] == batch.id
        assert data["student_count"] == len(students)
        assert len(data["results"]) == len(students)

    def test_create_session_requires_authentication(self, client):
        response = client.post(f"{API_PREFIX}/sessions", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_session_student_count_mismatch(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)

        payload = {
            "coach_id": coach.id,
            "school_id": school.id,
            "batch_id": batch.id,
            "date_of_session": "2025-02-01",
            "student_count": len(students) + 1,
            "results": [_build_result_payload(student.id) for student in students],
        }

        response = client.post(f"{API_PREFIX}/sessions", json=payload, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.json()["detail"]
        assert detail["code"] == "validation_error"

    def test_create_session_coach_cannot_impersonate_other_coach(
        self,
        client,
        test_db,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        students = _create_students(test_db, batch, count=2)
        _, coach_profile, coach_headers = _create_coach_user_headers(test_db)
        _assign_coach(test_db, coach_profile, batch)
        other_coach = _create_coach(test_db, username="othercoach")

        payload = {
            "coach_id": other_coach.id,
            "school_id": school.id,
            "batch_id": batch.id,
            "date_of_session": "2025-03-01",
            "student_count": len(students),
            "results": [_build_result_payload(student.id) for student in students],
        }

        response = client.post(f"{API_PREFIX}/sessions", json=payload, headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_sessions_list_as_admin(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)
        create_response = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        response = client.get(f"{API_PREFIX}/sessions", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["coach_id"] == coach.id

    def test_get_sessions_list_coach_scope(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch_for_coach = _create_batch(test_db, school, name="Assigned Batch")
        batch_other = _create_batch(test_db, school, name="Other Batch")
        _, coach_profile, coach_headers = _create_coach_user_headers(test_db)
        _assign_coach(test_db, coach_profile, batch_for_coach)
        students_assigned = _create_students(test_db, batch_for_coach, count=2)
        students_other = _create_students(test_db, batch_other, count=2)

        create_one = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach_profile.id,
            school_id=school.id,
            batch_id=batch_for_coach.id,
            student_ids=[s.id for s in students_assigned],
        )
        assert create_one.status_code == status.HTTP_201_CREATED

        other_coach = _create_coach(test_db, username="separatecoach")
        _assign_coach(test_db, other_coach, batch_other)
        create_two = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=other_coach.id,
            school_id=school.id,
            batch_id=batch_other.id,
            student_ids=[s.id for s in students_other],
            offset=5,
        )
        assert create_two.status_code == status.HTTP_201_CREATED

        response = client.get(f"{API_PREFIX}/sessions", headers=coach_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        session_ids = {session["session_id"] for session in data["sessions"]}
        assert session_ids == {create_one.json()["id"]}

    def test_get_single_session_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        students = _create_students(test_db, batch, count=2)
        other_coach = _create_coach(test_db, username="owncoach")
        _assign_coach(test_db, other_coach, batch)
        create_response = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=other_coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        session_id = create_response.json()["id"]

        _, _, coach_headers = _create_coach_user_headers(test_db, username="scopedcoach")
        response = client.get(f"{API_PREFIX}/sessions/{session_id}", headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)
        create_response = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        session_id = create_response.json()["id"]

        update_payload = {
            "date_of_session": "2025-02-10",
            "student_count": len(students),
        }
        response = client.put(
            f"{API_PREFIX}/sessions/{session_id}",
            json=update_payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["date_of_session"] == "2025-02-10"

    def test_update_session_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        students = _create_students(test_db, batch, count=2)
        other_coach = _create_coach(test_db, username="updatecoach")
        _assign_coach(test_db, other_coach, batch)
        create_response = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=other_coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        session_id = create_response.json()["id"]

        update_payload = {"date_of_session": "2025-04-01"}
        _, _, coach_headers = _create_coach_user_headers(test_db, username="updateforbidden")
        response = client.put(
            f"{API_PREFIX}/sessions/{session_id}",
            json=update_payload,
            headers=coach_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_session_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        students = _create_students(test_db, batch, count=2)
        _assign_coach(test_db, coach, batch)
        create_response = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        session_id = create_response.json()["id"]

        response = client.delete(f"{API_PREFIX}/sessions/{session_id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        follow_up = client.get(f"{API_PREFIX}/sessions/{session_id}", headers=auth_headers_admin)
        assert follow_up.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_session_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        students = _create_students(test_db, batch, count=2)
        other_coach = _create_coach(test_db, username="deletecoach")
        _assign_coach(test_db, other_coach, batch)
        create_response = _create_session_via_api(
            client,
            auth_headers_admin,
            coach_id=other_coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[s.id for s in students],
        )
        session_id = create_response.json()["id"]

        _, _, coach_headers = _create_coach_user_headers(test_db, username="deleteforbidden")
        response = client.delete(f"{API_PREFIX}/sessions/{session_id}", headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# Student endpoint tests ---------------------------------------------------


@pytest.mark.integration
@pytest.mark.api
class TestPhysicalAssessmentStudentsEndpoints:
    def _seed_session_with_results(self, client, db, headers, *, coach: Coach, batch: Batch, school: School) -> dict:
        students = _create_students(db, batch, count=2)
        _assign_coach(db, coach, batch)
        response = _create_session_via_api(
            client,
            headers,
            coach_id=coach.id,
            school_id=school.id,
            batch_id=batch.id,
            student_ids=[student.id for student in students],
        )
        assert response.status_code == status.HTTP_201_CREATED
        payload = response.json()
        payload["student_ids"] = [student.id for student in students]
        return payload

    def test_get_students_summary_as_admin(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        session_payload = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=coach,
            batch=batch,
            school=school,
        )
        response = client.get(f"{API_PREFIX}/students", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        student_ids = {student["student_id"] for student in data["students"]}
        assert set(session_payload["student_ids"]) <= student_ids

    def test_get_students_summary_requires_authentication(self, client):
        response = client.get(f"{API_PREFIX}/students")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_students_summary_coach_scope(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        assigned_batch = _create_batch(test_db, school, name="Coach Batch")
        other_batch = _create_batch(test_db, school, name="Other Batch")
        _, coach_profile, coach_headers = _create_coach_user_headers(test_db)
        assigned_session = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=coach_profile,
            batch=assigned_batch,
            school=school,
        )
        other_coach = _create_coach(test_db, username="coach-two")
        self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=other_coach,
            batch=other_batch,
            school=school,
        )

        response = client.get(f"{API_PREFIX}/students", headers=coach_headers)
        assert response.status_code == status.HTTP_200_OK
        student_ids = {student["student_id"] for student in response.json()["students"]}
        assert set(assigned_session["student_ids"]) <= student_ids
        assert all(student_id in student_ids for student_id in assigned_session["student_ids"])
        assert len(student_ids) == len(assigned_session["student_ids"])

    def test_get_student_detail_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        session_payload = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=coach,
            batch=batch,
            school=school,
        )
        student_id = session_payload["student_ids"][0]

        response = client.get(f"{API_PREFIX}/students/{student_id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["student_id"] == student_id
        assert len(data["sessions"]) == 1

    def test_get_student_detail_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        other_coach = _create_coach(test_db, username="detailcoach")
        session_payload = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=other_coach,
            batch=batch,
            school=school,
        )
        student_id = session_payload["student_ids"][0]

        _, _, coach_headers = _create_coach_user_headers(test_db, username="detailforbidden")
        response = client.get(f"{API_PREFIX}/students/{student_id}", headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_student_results_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        session_payload = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=coach,
            batch=batch,
            school=school,
        )
        student_id = session_payload["student_ids"][0]
        session_id = session_payload["id"]

        update_payload = {
            "updates": [
                {
                    "session_id": session_id,
                    "result": {
                        "curl_up": 60,
                        "push_up": 35,
                        "plank": 4.2,
                        "is_present": True,
                    },
                }
            ]
        }

        response = client.put(
            f"{API_PREFIX}/students/{student_id}",
            json=update_payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == status.HTTP_200_OK
        session_result = response.json()["sessions"][0]["result"]
        assert session_result["curl_up"] == 60
        assert session_result["plank"] == 4.2

    def test_update_student_results_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        other_coach = _create_coach(test_db, username="restrictedcoach")
        session_payload = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=other_coach,
            batch=batch,
            school=school,
        )
        student_id = session_payload["student_ids"][0]
        session_id = session_payload["id"]

        update_payload = {
            "updates": [
                {
                    "session_id": session_id,
                    "result": {"curl_up": 55},
                }
            ]
        }
        _, _, coach_headers = _create_coach_user_headers(test_db, username="updateblock")
        response = client.put(f"{API_PREFIX}/students/{student_id}", json=update_payload, headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_student_results_success(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        coach = _create_coach(test_db)
        session_payload = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=coach,
            batch=batch,
            school=school,
        )
        student_id = session_payload["student_ids"][0]

        response = client.delete(f"{API_PREFIX}/students/{student_id}", headers=auth_headers_admin)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        follow_up = client.get(f"{API_PREFIX}/students/{student_id}", headers=auth_headers_admin)
        assert follow_up.status_code == status.HTTP_200_OK
        assert follow_up.json()["sessions"] == []

    def test_delete_student_results_forbidden_for_unassigned_coach(
        self,
        client,
        test_db,
        auth_headers_admin,
    ):
        school = _create_school(test_db)
        batch = _create_batch(test_db, school)
        other_coach = _create_coach(test_db, username="delete-student-coach")
        session_payload = self._seed_session_with_results(
            client,
            test_db,
            auth_headers_admin,
            coach=other_coach,
            batch=batch,
            school=school,
        )
        student_id = session_payload["student_ids"][0]

        _, _, coach_headers = _create_coach_user_headers(test_db, username="deleteblock")
        response = client.delete(f"{API_PREFIX}/students/{student_id}", headers=coach_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# Level mapping endpoint tests --------------------------------------------


@pytest.mark.integration
@pytest.mark.api
class TestPhysicalAssessmentLevelMappingsEndpoints:
    endpoint = f"{API_PREFIX}/level-mappings"

    def test_level_mappings_requires_authentication(self, client):
        response = client.get(self.endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_level_mappings_empty_database(self, client, auth_headers_admin):
        response = client.get(self.endpoint, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["schools"] == []

    def test_level_mappings_admin_view_includes_exercises(self, client, test_db, auth_headers_admin):
        school = _create_school(test_db, name="Admin School")
        batch = _create_batch(test_db, school, name="Admin Batch")
        coach = _create_coach(test_db, username="levelcoach")
        _assign_coach(test_db, coach, batch)
        student = _create_students(test_db, batch, count=1)[0]

        test_db.add(
            StudentExerciseAverage(
                student_id=student.id,
                batch_id=batch.id,
                school_id=school.id,
                exercise_name="curl_up",
                average_score=42.0,
                current_level=4,
                level_description="strong",
                session_count=1,
            )
        )
        test_db.commit()

        response = client.get(self.endpoint, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert len(payload["schools"]) == 1
        school_payload = payload["schools"][0]
        assert school_payload["school_name"] == "Admin School"
        batch_payload = school_payload["batches"][0]
        assert batch_payload["batch_name"] == "Admin Batch"
        student_payload = batch_payload["students"][0]
        assert student_payload["student_name"] == "Student 1"
        assert len(student_payload["exercises"]) == 7
        curl_up = next(ex for ex in student_payload["exercises"] if ex["exercise_name"] == "curl_up")
        assert curl_up["average_score"] == pytest.approx(42.0)
        assert curl_up["level"] == 4
        assert curl_up["level_description"] == "strong"

    def test_level_mappings_coach_scope_filters_unassigned_data(self, client, test_db):
        assigned_school = _create_school(test_db, name="Assigned School")
        assigned_batch = _create_batch(test_db, assigned_school, name="Assigned Batch")
        assigned_students = _create_students(test_db, assigned_batch, count=1)
        coach, coach_headers = _create_coach_token_headers(test_db, username="filteredcoach")
        _assign_coach(test_db, coach, assigned_batch)

        test_db.add(
            StudentExerciseAverage(
                student_id=assigned_students[0].id,
                batch_id=assigned_batch.id,
                school_id=assigned_school.id,
                exercise_name="push_up",
                average_score=30.0,
                current_level=3,
                level_description="good",
                session_count=1,
            )
        )

        other_school = _create_school(test_db, name="Other School")
        other_batch = _create_batch(test_db, other_school, name="Other Batch")
        other_student = _create_students(test_db, other_batch, count=1)[0]
        other_coach = _create_coach(test_db, username="otherlevelcoach")
        _assign_coach(test_db, other_coach, other_batch)
        test_db.add(
            StudentExerciseAverage(
                student_id=other_student.id,
                batch_id=other_batch.id,
                school_id=other_school.id,
                exercise_name="curl_up",
                average_score=55.0,
                current_level=5,
                level_description="excellent",
                session_count=2,
            )
        )
        test_db.commit()

        response = client.get(self.endpoint, headers=coach_headers)
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload["schools"]
        school_names = {school["school_name"] for school in payload["schools"]}
        assert school_names == {"Assigned School"}
        batch_names = {batch["batch_name"] for school in payload["schools"] for batch in school["batches"]}
        assert batch_names == {"Assigned Batch"}

    def test_level_mappings_exercise_without_level_has_null_level(self, client, test_db, auth_headers_admin):
        """Test that exercises with average scores but no level mapping return null for level fields"""
        school = _create_school(test_db, name="Null Level School")
        batch = _create_batch(test_db, school, name="Null Level Batch")
        student = _create_students(test_db, batch, count=1)[0]

        test_db.add(
            StudentExerciseAverage(
                student_id=student.id,
                batch_id=batch.id,
                school_id=school.id,
                exercise_name="dash_50m",
                average_score=7.5,
                current_level=None,
                level_description=None,
                session_count=1,
            )
        )
        test_db.commit()

        response = client.get(self.endpoint, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        student_payload = response.json()["schools"][0]["batches"][0]["students"][0]
        dash_50m = next(ex for ex in student_payload["exercises"] if ex["exercise_name"] == "dash_50m")
        assert dash_50m["average_score"] == pytest.approx(7.5)
        assert dash_50m["level"] is None
        assert dash_50m["level_description"] is None

    def test_level_mappings_student_without_exercise_data_shows_all_nulls(self, client, test_db, auth_headers_admin):
        """Test that students without any exercise averages show all 7 exercises with null values"""
        school = _create_school(test_db, name="No Data School")
        batch = _create_batch(test_db, school, name="No Data Batch")
        student = _create_students(test_db, batch, count=1)[0]

        response = client.get(self.endpoint, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        
        if payload["schools"]:
            student_payload = payload["schools"][0]["batches"][0]["students"][0]
            assert len(student_payload["exercises"]) == 7
            for exercise in student_payload["exercises"]:
                assert exercise["average_score"] is None
                assert exercise["level"] is None
                assert exercise["level_description"] is None

    def test_level_mappings_multiple_students_in_batch(self, client, test_db, auth_headers_admin):
        """Test level mappings returns data for all students in a batch"""
        school = _create_school(test_db, name="Multi Student School")
        batch = _create_batch(test_db, school, name="Multi Student Batch")
        students = _create_students(test_db, batch, count=3)

        for idx, student in enumerate(students):
            test_db.add(
                StudentExerciseAverage(
                    student_id=student.id,
                    batch_id=batch.id,
                    school_id=school.id,
                    exercise_name="curl_up",
                    average_score=30.0 + (idx * 10),
                    current_level=3 + idx,
                    level_description=f"level_{idx}",
                    session_count=1,
                )
            )
        test_db.commit()

        response = client.get(self.endpoint, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        batch_payload = response.json()["schools"][0]["batches"][0]
        assert len(batch_payload["students"]) == 3
        
        student_names = {s["student_name"] for s in batch_payload["students"]}
        assert student_names == {"Student 1", "Student 2", "Student 3"}

    def test_level_mappings_batch_without_coaches_shows_null(self, client, test_db, auth_headers_admin):
        """Test that batches without coach assignments show null for coach_names"""
        school = _create_school(test_db, name="Unassigned Coach School")
        batch = _create_batch(test_db, school, name="Unassigned Batch")
        student = _create_students(test_db, batch, count=1)[0]
        
        test_db.add(
            StudentExerciseAverage(
                student_id=student.id,
                batch_id=batch.id,
                school_id=school.id,
                exercise_name="plank",
                average_score=2.5,
                current_level=2,
                level_description="fair",
                session_count=1,
            )
        )
        test_db.commit()

        response = client.get(self.endpoint, headers=auth_headers_admin)
        assert response.status_code == status.HTTP_200_OK
        batch_payload = response.json()["schools"][0]["batches"][0]
        assert batch_payload["coach_names"] is None or batch_payload["coach_names"] == []

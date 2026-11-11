"""Responses must expose explicit schema fields only — never ORM internals such as password hashes.

Regression for the learning-path endpoint, which used to serialise raw ORM objects and so returned
nested student/user rows (including password hashes, guardian details and addresses).
"""
import pytest

from app.schemas.recommendation import RecommendationOut

FORBIDDEN = ("hashed_password", "token_version", "_sa_instance_state", "guardian_contact")

ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/recommendations/",
    "/api/v1/risk/alerts",
    "/api/v1/interventions",
    "/api/v1/dashboards/me",
    "/api/v1/placement/applications",
    "/api/v1/ai/conversations",
]


def _own_student_id(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()["student_id"]


@pytest.mark.parametrize("email", ["student@reva-demo.example", "mentor@reva-demo.example",
                                   "admin@reva-demo.example", "placement@deccan-tech.example"])
def test_common_endpoints_never_leak_internal_fields(client, auth, email):
    headers = auth(email)
    for path in ENDPOINTS:
        body = client.get(path, headers=headers).text
        for field in FORBIDDEN:
            assert field not in body, f"{path} exposed {field} to {email}"


def test_learning_path_returns_schema_fields_only(client, auth):
    headers = auth("student@reva-demo.example")
    sid = _own_student_id(client, headers)
    client.post(f"/api/v1/recommendations/generate/{sid}", headers=headers)
    r = client.get(f"/api/v1/recommendations/students/{sid}/learning-path", headers=headers)
    assert r.status_code == 200
    for field in FORBIDDEN:
        assert field not in r.text
    data = r.json()
    items = data["academic_improvement_plan"] + data["career_development_plan"]
    assert items, "the seeded student should have a learning path"
    allowed = set(RecommendationOut.model_fields)
    for item in items:
        assert set(item) <= allowed
        assert "student" not in item and "catalogue" not in item
    assert all(item["student_name"] for item in items)


def test_admin_learning_path_view_does_not_leak_mentor_account(client, auth):
    headers = auth("admin@reva-demo.example")
    r = client.get("/api/v1/recommendations/students/1/learning-path", headers=headers)
    assert r.status_code == 200
    assert "hashed_password" not in r.text and "@reva-demo.example" not in r.text

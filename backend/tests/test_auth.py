from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ACEDRA"


def test_login_success_student():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "aarav.sharma@reva.in", "password": "StudentPass123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "student"
    assert data["user"]["email"] == "aarav.sharma@reva.in"


def test_login_invalid_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "aarav.sharma@reva.in", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert "detail" in response.json() or "message" in response.json()


def test_login_nonexistent_user():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@reva.in", "password": "WrongPassword!"}
    )
    assert response.status_code == 401


def test_rbac_admin_vs_student():
    # Login as Student
    student_res = client.post(
        "/api/v1/auth/login",
        json={"email": "aarav.sharma@reva.in", "password": "StudentPass123!"}
    )
    student_token = student_res.json()["access_token"]

    # Student trying to access Admin-only /users/ endpoint -> Forbidden (403)
    res_forbidden = client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_forbidden.status_code == 403

    # Login as Admin
    admin_res = client.post(
        "/api/v1/auth/login",
        json={"email": "anitha.rao@reva.in", "password": "AdminPass123!"}
    )
    admin_token = admin_res.json()["access_token"]

    # Admin accessing /users/ endpoint -> 200 OK
    res_allowed = client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_allowed.status_code == 200
    users = res_allowed.json()["items"]
    assert len(users) >= 5


def test_dashboard_dynamic_metrics():
    # Test for each role
    roles_credentials = [
        ("aarav.sharma@reva.in", "StudentPass123!", "student"),
        ("kavya.menon@reva.in", "FacultyPass123!", "faculty"),
        ("suresh.hegde@reva.in", "MentorPass123!", "mentor"),
        ("anitha.rao@reva.in", "AdminPass123!", "admin"),
        ("rahul.deshpande@reva.in", "PlacementPass123!", "placement_officer"),
    ]

    for email, pwd, expected_role in roles_credentials:
        login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        dash_res = client.get("/api/v1/dashboards/me", headers={"Authorization": f"Bearer {token}"})
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert dash_data["role"] == expected_role
        assert len(dash_data["summary_cards"]) >= 3

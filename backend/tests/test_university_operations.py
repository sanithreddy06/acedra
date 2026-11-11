"""Phase 2: a newly onboarded university runs its own operations end to end.

enquiry → tenant → administrator → configuration (departments, terms, subjects, teaching assignments)
→ faculty / mentor / student invitations → academic data import → risk identification
→ mentor assignment and intervention → progress and outcome tracking.
Every step goes through the API and is read back, and tenant and permission boundaries are checked on the way.
"""
import io

from tests.conftest import legal_versions
from tests.test_platform_workflow import SUPER, _ids_by_email, latest_token

EMP = "arjun.rao@acedra.example"
DOMAIN = "lakeside.example"


def _accept(client, email, password):
    r = client.post("/api/v1/auth/invitations/accept",
                    json={"token": latest_token(email, "invitation"), "password": password,
                          "accepted_versions": legal_versions(client)})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _csv(client, h, kind, text, execute=True):
    files = {"file": (f"{kind}.csv", io.BytesIO(text.encode()), "text/csv")}
    preview = client.post("/api/v1/imports/preview", files=files, data={"import_type": kind}, headers=h)
    assert preview.status_code == 200, preview.text
    if not execute:
        return preview.json()
    files = {"file": (f"{kind}.csv", io.BytesIO(text.encode()), "text/csv")}
    job = client.post("/api/v1/imports/execute", files=files, data={"import_type": kind}, headers=h)
    assert job.status_code == 201, job.text
    return preview.json(), job.json()


def _onboard(client, auth):
    sa = auth(SUPER)
    enquiry = {"university_name": "Lakeside University", "institution_type": "Private university",
               "location": "Udupi, Karnataka", "student_population": "Under 2,000", "contact_name": "Dr. Meera Iyer",
               "contact_designation": "Dean of Academics", "contact_email": f"dean@{DOMAIN}",
               "requested_modules": ["student_intelligence", "risk_identification", "interventions"],
               "email_provisioning": "existing", "consent_to_contact": True}
    assert client.post("/api/v1/public/enquiries", json=enquiry).status_code == 201
    eid = client.get("/api/v1/platform/enquiries?search=Lakeside", headers=sa).json()["items"][0]["id"]
    client.post(f"/api/v1/platform/enquiries/{eid}/agreement", headers=sa,
                json={"reference": "ACD-SA-LAKE-01", "agreed_modules": enquiry["requested_modules"]})
    assert client.post(f"/api/v1/platform/enquiries/{eid}/status", json={"status": "approved"},
                       headers=sa).status_code == 200
    (emp_id,) = _ids_by_email(EMP)
    uni = client.post(f"/api/v1/platform/enquiries/{eid}/create-tenant", headers=sa,
                      json={"short_name": "Lakeside", "slug": "lakeside", "domains": [DOMAIN],
                            "primary_employee_id": emp_id}).json()
    r = client.post(f"/api/v1/platform/universities/{uni['id']}/admins", headers=auth(EMP),
                    json={"email": f"registrar@{DOMAIN}", "full_name": "Ravi Shetty", "title": "Registrar"})
    assert r.status_code == 201, r.text
    admin = _accept(client, f"registrar@{DOMAIN}", "Lakeside#2026")
    return sa, uni["id"], admin


def test_new_university_runs_the_full_student_success_workflow(client, auth):
    sa, uid, admin = _onboard(client, auth)

    # 7. University configuration: department, current term, subject.
    assert client.post("/api/v1/tenant/departments", headers=admin,
                       json={"code": "CSE", "name": "Computer Science"}).status_code in (200, 201)
    dept = client.get("/api/v1/tenant/departments", headers=admin).json()[0]["id"]
    term = client.post("/api/v1/academics/semesters", headers=admin,
                       json={"name": "Semester 3", "academic_year": "2026-2027", "semester_number": 3,
                             "is_current": True})
    assert term.status_code == 201, term.text
    subject = client.post("/api/v1/academics/subjects", headers=admin,
                          json={"code": "LK-CS301", "name": "Data Structures", "department_id": dept,
                                "semester_number": 3})
    assert subject.status_code == 201, subject.text

    # 8. Faculty and mentor invitations (activation needed before non-admins can sign in).
    for email, role, name in ((f"kavya.faculty@{DOMAIN}", "faculty", "Kavya Rao"),
                              (f"suresh.mentor@{DOMAIN}", "mentor", "Suresh Pai")):
        r = client.post("/api/v1/users/invite", headers=admin,
                        json={"email": email, "full_name": name, "role": role, "department_id": dept})
        assert r.status_code == 201, r.text
    assert client.post(f"/api/v1/platform/universities/{uid}/status", json={"status": "active"},
                       headers=sa).status_code == 200
    faculty = _accept(client, f"kavya.faculty@{DOMAIN}", "Faculty#Lake1")
    mentor = _accept(client, f"suresh.mentor@{DOMAIN}", "Mentor#Lake1")

    # 9. Student data import: students, then attendance and results. Bad rows are reported, not invented.
    preview, job = _csv(client, admin, "students",
                        "usn,full_name,email,department_code,semester,section\n"
                        f"LK24CS001,Anu Bhat,anu@{DOMAIN},CSE,3,A\n"
                        f"LK24CS002,Varun Gowda,varun@{DOMAIN},CSE,3,A\n"
                        f"LK24CS003,No Department,nodept@{DOMAIN},MECH,3,A\n")
    assert preview["valid_rows_count"] == 2 and preview["invalid_rows_count"] == 1
    assert job["successful_rows"] == 2 and job["failed_rows"] == 1 and job["status"] == "partially_completed"
    _, job = _csv(client, admin, "attendance",
                  "usn,subject_code,total_classes,attended_classes\nLK24CS001,LK-CS301,40,22\nLK24CS002,LK-CS301,40,38\n")
    assert job["successful_rows"] == 2
    _, job = _csv(client, admin, "academic_records",
                  "usn,semester_number,subject_code,internal_marks,external_marks,grade\n"
                  "LK24CS001,3,LK-CS301,12,20,F\nLK24CS002,3,LK-CS301,40,45,A+\n")
    assert job["successful_rows"] == 2 and job["status"] == "completed"
    students = {s["usn"]: s for s in client.get("/api/v1/students/", headers=admin).json()}
    anu = students["LK24CS001"]["id"]
    analytics = client.get(f"/api/v1/students/{anu}/analytics", headers=admin).json()
    assert analytics["metrics"]["calculated_attendance_percentage"] == 55.0
    assert analytics["subject_performance"][0]["is_backlog"] is True

    # Faculty sees no one until a teaching assignment exists; then exactly that section.
    assert client.get("/api/v1/students/", headers=faculty).json() == []
    (fac_user,) = _ids_by_email(f"kavya.faculty@{DOMAIN}")
    r = client.post("/api/v1/academics/assignments", headers=admin,
                    json={"faculty_user_id": fac_user, "subject_id": subject.json()["id"],
                          "semester_id": term.json()["id"], "section": "A", "academic_year": "2026-2027"})
    assert r.status_code == 201, r.text
    assert {s["usn"] for s in client.get("/api/v1/students/", headers=faculty).json()} == {"LK24CS001", "LK24CS002"}

    # 10. Risk identification flags the student whose attendance is low.
    ev = client.post("/api/v1/risk/evaluate", json={"run_type": "MANUAL"}, headers=admin)
    assert ev.status_code == 200 and ev.json()["alerts_generated_count"] >= 1
    alerts = client.get("/api/v1/risk/alerts", params={"student_id": anu}, headers=admin).json()["items"]
    assert alerts and all(a["student_id"] == anu for a in alerts)
    alert_id = alerts[0]["id"]

    # 11. Mentor assignment and an intervention linked to the alert.
    mentor_profile = next(m for m in client.get("/api/v1/tenant/mentors", headers=admin).json()
                          if m["email"] == f"suresh.mentor@{DOMAIN}")
    assert client.get(f"/api/v1/students/{anu}", headers=mentor).status_code == 403  # not yet a mentee
    r = client.post("/api/v1/tenant/mentor-assignments", headers=admin,
                    json={"mentor_id": mentor_profile["id"], "student_ids": [anu]})
    assert r.status_code == 200, r.text
    assert client.get(f"/api/v1/students/{anu}", headers=mentor).status_code == 200
    r = client.post("/api/v1/interventions", headers=mentor,
                    json={"student_id": anu, "risk_alert_id": alert_id, "title": "Attendance recovery plan",
                          "intervention_type": "ATTENDANCE_CONDONATION_COUNSELING", "priority": "HIGH",
                          "initial_notes": "Agreed weekly check-ins."})
    assert r.status_code == 201, r.text
    case = r.json()
    assert case["mentor_id"] == mentor_profile["id"] and case["status"] == "ASSIGNED"

    # 12. Progress and outcome tracking.
    cid = case["id"]
    fu = client.post(f"/api/v1/interventions/{cid}/followups", headers=mentor,
                     json={"scheduled_date": "2026-11-20", "outcome_notes": "First check-in"})
    assert fu.status_code == 201
    r = client.put(f"/api/v1/interventions/followups/{fu.json()['id']}", headers=mentor,
                   json={"followup_status": "COMPLETED", "outcome_notes": "Attended all classes this week",
                         "student_feedback": "Helpful"})
    assert r.status_code == 200
    assert client.put(f"/api/v1/interventions/{cid}/status", headers=mentor,
                      json={"status": "IN_PROGRESS"}).status_code == 200
    assert client.put(f"/api/v1/interventions/{cid}/status", headers=mentor,
                      json={"status": "RESOLVED"}).status_code == 422          # outcome is required
    r = client.put(f"/api/v1/interventions/{cid}/status", headers=mentor,
                   json={"status": "RESOLVED", "resolution_summary": "Attendance back above 80% for three weeks."})
    assert r.status_code == 200 and r.json()["status"] == "RESOLVED"
    detail = client.get(f"/api/v1/interventions/{cid}", headers=admin).json()
    assert detail["resolution_summary"].startswith("Attendance back") and len(detail["followups"]) == 1
    assert client.post(f"/api/v1/risk/alerts/{alert_id}/resolve", headers=mentor,
                       json={"resolution_reason": "Resolved through intervention"}).status_code == 200

    # The student activates their invitation and sees their own case and progress — nobody else's.
    student = _accept(client, f"anu@{DOMAIN}", "Student#Lake1")
    mine = client.get("/api/v1/interventions", headers=student).json()
    assert [i["id"] for i in mine] == [cid] and mine[0]["status"] == "RESOLVED"
    assert [s["usn"] for s in client.get("/api/v1/students/", headers=student).json()] == ["LK24CS001"]
    assert client.get(f"/api/v1/students/{students['LK24CS002']['id']}", headers=student).status_code == 403

    # Tenant and permission boundaries.
    reva_admin = auth("admin@reva-demo.example")
    assert client.get(f"/api/v1/students/{anu}", headers=reva_admin).status_code == 404
    assert client.get(f"/api/v1/interventions/{cid}", headers=reva_admin).status_code == 404
    assert client.get(f"/api/v1/platform/universities/{uid}/student-directory",
                      headers=auth(EMP)).status_code == 403    # configuration access is not student-data access


def test_configuration_rejects_other_tenants_references(client, auth):
    reva, nf = auth("admin@reva-demo.example"), auth("admin@northfield.example")
    nf_dept = client.get("/api/v1/tenant/departments", headers=nf).json()[0]["id"]
    r = client.post("/api/v1/academics/subjects", headers=reva,
                    json={"code": "X-CROSS-1", "name": "Cross tenant", "department_id": nf_dept, "semester_number": 1})
    assert r.status_code == 422
    nf_mentor = client.get("/api/v1/tenant/mentors", headers=nf).json()[0]["id"]
    reva_student = client.get("/api/v1/students/", headers=reva).json()[0]["id"]
    r = client.post("/api/v1/interventions", headers=reva,
                    json={"student_id": reva_student, "mentor_id": nf_mentor, "title": "Cross tenant mentor"})
    assert r.status_code == 422
    # Teaching assignments are an administrator action.
    assert client.post("/api/v1/academics/assignments", headers=auth("faculty@reva-demo.example"),
                       json={"faculty_user_id": 1, "subject_id": 1, "semester_id": 1,
                             "academic_year": "2026-2027"}).status_code == 403


def test_import_rejects_unknown_type_and_reports_missing_terms(client, auth):
    h = auth("admin@deccan-tech.example")
    files = {"file": ("x.csv", io.BytesIO(b"usn\nX\n"), "text/csv")}
    assert client.post("/api/v1/imports/execute", files=files, data={"import_type": "grades"},
                       headers=h).status_code == 422
    usn = client.get("/api/v1/students/", headers=h).json()[0]["usn"]
    _, job = _csv(client, h, "academic_records",
                  f"usn,semester_number,subject_code,internal_marks,external_marks,grade\n{usn},99,NOPE,1,1,Q\n")
    assert job["successful_rows"] == 0 and job["failed_rows"] == 1 and job["status"] == "failed"

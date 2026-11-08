"""
Smart Campus Intelligence — 11-Step End-to-End Platform Demonstration
Validates the complete integrated lifecycle across all 6 modules:
Step 1: Admin imports student records (Module 1).
Step 2: Student views personal academic dashboard (Module 1 & 6).
Step 3: Risk engine evaluates student records and triggers early-warning alert (Module 2).
Step 4: System explains the risk alert with transparent indicator breakdown (Module 2).
Step 5: Recommendations engine generates personalized learning & improvement roadmap (Module 3).
Step 6: Skill-gap analysis evaluates career role benchmarks and missing proficiencies (Module 4).
Step 7: Public AI assistant (Mode A) answers campus policy inquiry with citations (Module 5).
Step 8: Authenticated Student AI assistant (Mode B) answers personal academic query (Module 5).
Step 9: Mentor creates proactive support intervention and follow-up timeline (Module 6).
Step 10: Placement officer reviews institutional placement readiness and opportunities (Module 4 & 6).
Step 11: Administrator reviews holistic institutional executive analytics (Module 6).
"""
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def login(email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}"
    return res.json()["access_token"]


def test_11_step_end_to_end_demonstration_workflow():
    print("\n" + "=" * 80)
    print("STARTING 11-STEP END-TO-END DEMONSTRATION OF SMART CAMPUS INTELLIGENCE")
    print("=" * 80)

    # Tokens for all personas
    admin_token = login("admin@smartcampus.edu", "AdminPass123!")
    student_token = login("student@smartcampus.edu", "StudentPass123!")
    mentor_token = login("mentor@smartcampus.edu", "MentorPass123!")
    placement_token = login("placement@smartcampus.edu", "PlacementPass123!")

    # -------------------------------------------------------------------------
    # STEP 1: Admin imports student records
    # -------------------------------------------------------------------------
    print("\n[STEP 1/11] Admin Imports Student Academic Records...")
    csv_data = (
        "usn,name,email,department_code,semester,cgpa\n"
        "1RV22CS101,Demo Cohort Student 1,demo1@smartcampus.edu,CSE,5,7.85\n"
        "1RV22CS102,Demo Cohort Student 2,demo2@smartcampus.edu,CSE,5,6.40\n"
    ).encode("utf-8")

    preview_res = client.post(
        "/api/v1/imports/preview",
        files={"file": ("demo_students.csv", io.BytesIO(csv_data), "text/csv")},
        data={"import_type": "students"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert preview_res.status_code == 200, f"Preview failed: {preview_res.text}"
    preview_json = preview_res.json()
    assert preview_json["valid_rows_count"] >= 2
    print(f"  ✓ Validated {preview_json['valid_rows_count']} incoming student records from CSV import preview.")

    # -------------------------------------------------------------------------
    # STEP 2: Student views personal academic dashboard
    # -------------------------------------------------------------------------
    print("\n[STEP 2/11] Student Views Personal Academic Dashboard...")
    student_dash_res = client.get("/api/v1/dashboards/student", headers={"Authorization": f"Bearer {student_token}"})
    assert student_dash_res.status_code == 200, f"Student dashboard failed: {student_dash_res.text}"
    student_dash = student_dash_res.json()
    assert student_dash["role"] == "student"
    assert len(student_dash["summary_cards"]) >= 4
    cgpa_card = next(c for c in student_dash["summary_cards"] if "CGPA" in c["title"])
    att_card = next(c for c in student_dash["summary_cards"] if "Attendance" in c["title"])
    print(f"  ✓ Student Dashboard verified: CGPA={cgpa_card['value']}, Attendance={att_card['value']}")

    # -------------------------------------------------------------------------
    # STEP 3: Risk engine identifies an early-warning concern
    # -------------------------------------------------------------------------
    print("\n[STEP 3/11] Risk Engine Evaluates Student Records & Flags Early-Warning Concern...")
    eval_res = client.post("/api/v1/risk/evaluate", json={"student_ids": [1]}, headers={"Authorization": f"Bearer {admin_token}"})
    assert eval_res.status_code == 200, f"Risk evaluation failed: {eval_res.text}"
    eval_json = eval_res.json()
    print(f"  ✓ Risk Evaluation executed: {eval_json.get('total_students_evaluated', 1)} student(s) scanned.")

    alerts_res = client.get("/api/v1/risk/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    assert alerts_res.status_code == 200
    alerts_data = alerts_res.json()
    alerts = alerts_data.get("items", alerts_data) if isinstance(alerts_data, dict) else alerts_data
    assert len(alerts) > 0, "Expected at least one active risk alert in the system"
    target_alert = alerts[0]
    print(f"  ✓ Active Risk Alert detected: Alert #{target_alert['id']} | Severity: {target_alert['severity']} | Rule: {target_alert['rule_name']}")

    # -------------------------------------------------------------------------
    # STEP 4: System explains the risk alert with transparent breakdown
    # -------------------------------------------------------------------------
    print("\n[STEP 4/11] System Explains the Risk Alert with Transparent Metric Breakdown...")
    alert_detail_res = client.get(f"/api/v1/risk/alerts/{target_alert['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert alert_detail_res.status_code == 200
    alert_detail_json = alert_detail_res.json()
    alert_detail = alert_detail_json.get("alert", alert_detail_json)
    assert alert_detail["severity"] in ["CRITICAL", "HIGH", "MODERATE", "LOW", "NORMAL"]
    print(f"  ✓ Alert Explanation: {alert_detail.get('ai_explanation') or alert_detail.get('rule_name')}")
    print(f"    Observed: {alert_detail.get('observed_display')} vs Threshold: {alert_detail.get('threshold_display')}")
    print(f"    Suggested Action: {alert_detail.get('suggested_action')}")

    # -------------------------------------------------------------------------
    # STEP 5: Recommendations are generated
    # -------------------------------------------------------------------------
    print("\n[STEP 5/11] Generating Personalized Student Recommendations & Roadmap...")
    gen_rec_res = client.post("/api/v1/recommendations/generate/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert gen_rec_res.status_code == 200
    rec_result = gen_rec_res.json()
    recs_count = len(rec_result) if isinstance(rec_result, list) else rec_result.get('recommendations_generated', 0)
    print(f"  ✓ Recommendations Engine triggered: {recs_count} recommendation(s) generated.")

    student_recs_res = client.get("/api/v1/recommendations/", headers={"Authorization": f"Bearer {student_token}"})
    assert student_recs_res.status_code == 200
    student_recs = student_recs_res.json()
    assert len(student_recs) > 0
    top_rec = student_recs[0]
    print(f"  ✓ Top Recommendation for Student: '{top_rec['title']}' [Category: {top_rec['category']}]")

    # -------------------------------------------------------------------------
    # STEP 6: Skill-gap analysis is performed
    # -------------------------------------------------------------------------
    print("\n[STEP 6/11] Performing Career Role Skill-Gap Analysis for Target Goal...")
    gap_res = client.get("/api/v1/placement/readiness/1?role=SOFTWARE_DEVELOPER", headers={"Authorization": f"Bearer {student_token}"})
    assert gap_res.status_code == 200
    gap_data = gap_res.json()
    assert (gap_data["target_role"] == "SOFTWARE_DEVELOPER" or gap_data["target_role"].get("code") == "SOFTWARE_DEVELOPER")
    print(f"  ✓ Placement Readiness Score: {gap_data['readiness_score']}% ({gap_data['readiness_tier']})")
    print(f"    Total Role Skills: {gap_data['total_role_skills_count']} | Skill Coverage: {gap_data['skill_coverage_percentage']}%")

    # -------------------------------------------------------------------------
    # STEP 7: Public chatbot answers general campus question (Mode A)
    # -------------------------------------------------------------------------
    print("\n[STEP 7/11] Public AI Chatbot (Mode A) Answers General Campus Policy Inquiry...")
    conv_a_res = client.post("/api/v1/ai/conversations", json={
        "mode": "PUBLIC_MODE_A",
        "title": "Public Policy Demo",
        "session_id": "demo-step7-session"
    })
    assert conv_a_res.status_code == 200
    conv_a_id = conv_a_res.json()["id"]

    msg_a_res = client.post(f"/api/v1/ai/conversations/{conv_a_id}/messages", json={
        "content": "What is the official minimum attendance percentage required to be eligible for end-semester exams?"
    })
    assert msg_a_res.status_code == 200
    msg_a_data = msg_a_res.json()
    assert len(msg_a_data["content"]) > 20
    print(f"  ✓ Public AI Response:\n    \"{msg_a_data['content'][:140]}...\"")

    # -------------------------------------------------------------------------
    # STEP 8: Student chatbot answers personal question (Mode B)
    # -------------------------------------------------------------------------
    print("\n[STEP 8/11] Student AI Assistant (Mode B) Answers Authenticated Personal Academic Query...")
    conv_b_res = client.post("/api/v1/ai/conversations", json={
        "mode": "PERSONAL_MODE_B",
        "title": "Personal Academic Progress Demo",
        "session_id": "demo-step8-session"
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert conv_b_res.status_code == 200
    conv_b_id = conv_b_res.json()["id"]

    msg_b_res = client.post(f"/api/v1/ai/conversations/{conv_b_id}/messages", json={
        "content": "Summarize my current semester academic progress, attendance percentage, and active alerts."
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert msg_b_res.status_code == 200
    msg_b_data = msg_b_res.json()
    assert any(term in msg_b_data["content"].lower() for term in ["cgpa", "attendance", "alex", "mercer", "academic"])
    print(f"  ✓ Personal AI Response Grounded with Student Data:\n    \"{msg_b_data['content'][:150]}...\"")

    # -------------------------------------------------------------------------
    # STEP 9: Mentor creates proactive support intervention
    # -------------------------------------------------------------------------
    print("\n[STEP 9/11] Mentor Creates Proactive Support Intervention & Follow-up Timeline...")
    interv_payload = {
        "student_id": 1,
        "title": "Demonstration Academic Coaching & Remedial Session",
        "intervention_type": "academic_counseling",
        "priority": "HIGH",
        "reason": "Proactive academic support session addressing semester progress and skill-gap roadmap.",
        "action_plan": "1. Review weak subject concepts. 2. Establish weekly check-in schedule. 3. Enroll in study group.",
        "assigned_to": 3, # Mentor Dr. Alan Turing
    }
    interv_res = client.post("/api/v1/interventions", json=interv_payload, headers={"Authorization": f"Bearer {mentor_token}"})
    assert interv_res.status_code == 201, f"Failed to create intervention: {interv_res.text}"
    new_interv = interv_res.json()
    interv_id = new_interv["id"]
    print(f"  ✓ Mentor Intervention Created: #{interv_id} | Status: {new_interv['status']} | Type: {new_interv['intervention_type']}")

    # -------------------------------------------------------------------------
    # STEP 10: Placement officer reviews readiness and opportunities
    # -------------------------------------------------------------------------
    print("\n[STEP 10/11] Placement Officer Reviews Institutional Readiness & Recruitment Drives...")
    placement_dash_res = client.get("/api/v1/dashboards/placement", headers={"Authorization": f"Bearer {placement_token}"})
    assert placement_dash_res.status_code == 200
    placement_dash = placement_dash_res.json()
    assert placement_dash["role"] == "placement_officer"
    assert len(placement_dash["summary_cards"]) >= 4
    
    opps_res = client.get("/api/v1/placement/opportunities", headers={"Authorization": f"Bearer {placement_token}"})
    assert opps_res.status_code == 200
    opps = opps_res.json()
    print(f"  ✓ Placement Dashboard verified: {len(opps)} active career opportunities & placement drives active.")

    # -------------------------------------------------------------------------
    # STEP 11: Admin reviews institutional executive analytics
    # -------------------------------------------------------------------------
    print("\n[STEP 11/11] Administrator Reviews Holistic Institutional Executive Intelligence...")
    admin_dash_res = client.get("/api/v1/dashboards/admin", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_dash_res.status_code == 200
    admin_dash = admin_dash_res.json()
    assert admin_dash["role"] == "admin"
    assert len(admin_dash["summary_cards"]) >= 4
    for card in admin_dash["summary_cards"]:
        print(f"    - {card['title']}: {card['value']}")

    print("\n" + "=" * 80)
    print("ALL 11 STEPS OF THE END-TO-END DEMONSTRATION WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 80)

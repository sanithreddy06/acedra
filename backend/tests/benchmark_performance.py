"""
Smart Campus Intelligence — Performance Benchmarking & Latency Profiler
Measures:
1. Dashboard Load Times (All 5 Roles: Student, Faculty, Mentor, Admin, Placement)
2. Core API Endpoint Latency (Profiles, Risk Alerts, Recommendations, Placement)
3. CSV Import Ingestion Throughput & Latency
4. Conversational AI & RAG Retrieval Latency (Mode A Public & Mode B Grounded)
5. Document Parsing & Text Ingestion Latency
6. Database Aggregation & Complex Query Efficiency
"""
import io
import statistics
import time
from typing import Any, Dict

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ROLE_CREDENTIALS = {
    "student": ("aarav.sharma@reva.in", "StudentPass123!"),
    "faculty": ("kavya.menon@reva.in", "FacultyPass123!"),
    "mentor": ("suresh.hegde@reva.in", "MentorPass123!"),
    "admin": ("anitha.rao@reva.in", "AdminPass123!"),
    "placement_officer": ("rahul.deshpande@reva.in", "PlacementPass123!"),
}


def authenticate(role: str) -> str:
    email, password = ROLE_CREDENTIALS[role]
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Auth failed for {role}"
    return res.json()["access_token"]


def measure_endpoint(method: str, path: str, token: str = None, json_body: Any = None, iterations: int = 5) -> Dict[str, float]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    latencies = []
    status_codes = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        if method.upper() == "GET":
            r = client.get(path, headers=headers)
        elif method.upper() == "POST":
            r = client.post(path, headers=headers, json=json_body)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)
        status_codes.append(r.status_code)

    return {
        "status": status_codes[0],
        "min_ms": round(min(latencies), 2),
        "avg_ms": round(statistics.mean(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "p95_ms": round(statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies), 2),
    }


def run_benchmarks():
    print("=" * 70)
    print("SMART CAMPUS INTELLIGENCE — PERFORMANCE BENCHMARK SUITE")
    print("=" * 70)

    tokens = {role: authenticate(role) for role in ROLE_CREDENTIALS}
    report = {}

    # 1. Dashboards
    print("\n[1/5] Benchmarking Role-Based Dashboards...")
    dash_endpoints = {
        "Student Dashboard": ("/api/v1/dashboards/student", tokens["student"]),
        "Faculty Dashboard": ("/api/v1/dashboards/faculty", tokens["faculty"]),
        "Mentor Dashboard": ("/api/v1/dashboards/mentor", tokens["mentor"]),
        "Admin Dashboard": ("/api/v1/dashboards/admin", tokens["admin"]),
        "Placement Dashboard": ("/api/v1/dashboards/placement", tokens["placement_officer"]),
    }
    for name, (path, tok) in dash_endpoints.items():
        res = measure_endpoint("GET", path, token=tok, iterations=5)
        print(f"  ✓ {name:<22}: Avg {res['avg_ms']:>6.2f} ms | Min {res['min_ms']:>6.2f} ms | Status {res['status']}")
        report[name] = res

    # 2. Core Operational APIs
    print("\n[2/5] Benchmarking Core Operational APIs...")
    api_endpoints = {
        "Students List": ("/api/v1/students/?limit=50", tokens["admin"]),
        "Risk Alerts List": ("/api/v1/risk/alerts", tokens["faculty"]),
        "Risk Statistics": ("/api/v1/risk/statistics", tokens["admin"]),
        "Recommendation Catalogue": ("/api/v1/recommendations/catalogue", tokens["student"]),
        "Placement Readiness": ("/api/v1/placement/readiness/1?role=SOFTWARE_DEVELOPER", tokens["student"]),
        "Career Opportunities": ("/api/v1/placement/opportunities", tokens["student"]),
    }
    for name, (path, tok) in api_endpoints.items():
        res = measure_endpoint("GET", path, token=tok, iterations=5)
        print(f"  ✓ {name:<24}: Avg {res['avg_ms']:>6.2f} ms | Min {res['min_ms']:>6.2f} ms | Status {res['status']}")
        report[name] = res

    # 3. CSV Import Processing Latency
    print("\n[3/5] Benchmarking CSV Import Validation Throughput...")
    csv_rows = ["usn,name,email,department_code,semester,cgpa"]
    for i in range(100):
        csv_rows.append(f"1RV22CS{i:03d},Bench Student {i},bench{i}@reva.in,CSE,5,8.25")
    csv_content = "\n".join(csv_rows).encode("utf-8")

    t0 = time.perf_counter()
    imp_res = client.post(
        "/api/v1/imports/preview",
        files={"file": ("bench_100_students.csv", io.BytesIO(csv_content), "text/csv")},
        data={"import_type": "students"},
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    )
    t1 = time.perf_counter()
    import_ms = round((t1 - t0) * 1000, 2)
    assert imp_res.status_code == 200
    report["CSV 100-Row Preview"] = {"avg_ms": import_ms, "status": imp_res.status_code}
    print(f"  ✓ CSV 100-Row Preview   : {import_ms} ms (Status: {imp_res.status_code})")

    # 4. Conversational AI Assistant & Grounding
    print("\n[4/5] Benchmarking Conversational AI Assistant...")
    # Mode A Public
    conv_a = client.post("/api/v1/ai/conversations", json={
        "mode": "PUBLIC_MODE_A",
        "title": "Bench Conversation",
        "session_id": "bench-perf-session-001"
    }).json()
    conv_a_id = conv_a["id"]

    t0 = time.perf_counter()
    msg_a = client.post(f"/api/v1/ai/conversations/{conv_a_id}/messages", json={
        "content": "What are the rules regarding minimum attendance requirement for semester exams?"
    })
    t1 = time.perf_counter()
    ai_a_ms = round((t1 - t0) * 1000, 2)
    report["Chatbot Public Mode A"] = {"avg_ms": ai_a_ms, "status": msg_a.status_code}
    print(f"  ✓ Chatbot Mode A (RAG)  : {ai_a_ms} ms (Status: {msg_a.status_code})")

    # Mode B Grounded Student
    conv_b = client.post("/api/v1/ai/conversations", json={
        "mode": "PERSONAL_MODE_B",
        "title": "Bench Mode B",
        "session_id": "bench-perf-session-002"
    }, headers={"Authorization": f"Bearer {tokens['student']}"}).json()
    conv_b_id = conv_b["id"]

    t0 = time.perf_counter()
    msg_b = client.post(f"/api/v1/ai/conversations/{conv_b_id}/messages", json={
        "content": "Summarize my current semester academic progress and attendance status."
    }, headers={"Authorization": f"Bearer {tokens['student']}"})
    t1 = time.perf_counter()
    ai_b_ms = round((t1 - t0) * 1000, 2)
    report["Chatbot Grounded Mode B"] = {"avg_ms": ai_b_ms, "status": msg_b.status_code}
    print(f"  ✓ Chatbot Mode B (Personal): {ai_b_ms} ms (Status: {msg_b.status_code})")

    # 5. Document Ingestion & RAG Indexing
    print("\n[5/5] Benchmarking Document Text Ingestion...")
    t0 = time.perf_counter()
    doc_res = client.post("/api/v1/ai/documents/text", json={
        "title": "Benchmark University Handbook Section",
        "category": "academic_regulations",
        "access_level": "public",
        "content": (
            "Section 8.4 Academic Grievances and Appeal Board. Students contesting internal continuous evaluation "
            "marks or semester evaluation results may file a formal grievance within seven working days of notification. "
            "A review committee comprising the Dean of Academics and Senior Professors evaluates the re-tabulation."
        ),
    }, headers={"Authorization": f"Bearer {tokens['admin']}"})
    t1 = time.perf_counter()
    doc_ms = round((t1 - t0) * 1000, 2)
    report["Document Text Ingestion"] = {"avg_ms": doc_ms, "status": doc_res.status_code}
    print(f"  ✓ Doc Ingestion & Chunking : {doc_ms} ms (Status: {doc_res.status_code})")

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY & SLA COMPLIANCE VERIFICATION")
    print("=" * 70)
    sla_passed = True
    for metric, data in report.items():
        avg = data.get("avg_ms", 0)
        sla_limit = 2000 if "Chatbot" in metric else 500
        passed = avg < sla_limit
        if not passed:
            sla_passed = False
        mark = "PASS" if passed else "WARN"
        print(f"  [{mark}] {metric:<28} : {avg:>6.2f} ms (SLA: <{sla_limit} ms)")

    print("-" * 70)
    print(f"OVERALL PERFORMANCE STATUS: {'ALL SLAs SATISFIED' if sla_passed else 'REVIEW REQUIRED'}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmarks()

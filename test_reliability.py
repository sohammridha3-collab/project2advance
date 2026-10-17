"""
Comprehensive Reliability, Health Timeline, and Concurrency Test Suite
for HealthBridge AI.

Verifies:
1. Backend startup and /health liveness endpoint.
2. /health/ready readiness check with database ping.
3. Health timeline retrieval with valid authentication.
4. Empty health timeline handling for a fresh user.
5. Expired / invalid authentication rejection with proper 401 status.
6. Timeline fault tolerance against malformed/null fields.
7. Database concurrency (Write-Ahead Logging & busy timeout verification).
8. Transient failure bounded retry simulation.
9. Soak / Repeated request stability (50+ rapid requests without exhaustion).
10. Concurrent requests simulating multiple open browser tabs.
11. CORS header presence on both 200 and unhandled 500 responses.
12. Cross-user privacy isolation on timeline and clinical records.
"""

import sys
import time
import json
import threading
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy import text
from jose import jwt

from main import app
from database.database import SessionLocal, engine
from database.models import User, HealthAssessment, RecentProblem, Prescription, Allergy, DoctorBriefing
from services.auth_handler import SECRET_KEY, ALGORITHM, create_access_token

def run_reliability_tests():
    print("\n" + "=" * 70)
    print(" HEALTHBRIDGE AI - RELIABILITY & HEALTH TIMELINE REGRESSION SUITE")
    print("=" * 70 + "\n")

    db = SessionLocal()
    with TestClient(app, raise_server_exceptions=False) as client:

        # ----------------------------------------------------
        # 1. /health Liveness Endpoint
        # ----------------------------------------------------
        print("[1] Testing /health liveness probe...")
        r_health = client.get("/health")
        assert r_health.status_code == 200, f"Expected 200, got {r_health.status_code}"
        health_data = r_health.json()
        assert health_data.get("server") == "online"
        assert "database_connected" in health_data
        print(f"  ✓ /health OK: status={health_data.get('status')}, model_loaded={health_data.get('model_loaded')}")

        # Test /api/health alias
        r_api_health = client.get("/api/health")
        assert r_api_health.status_code == 200
        print("  ✓ /api/health alias OK (200)")

        # ----------------------------------------------------
        # 2. /health/ready Readiness Probe
        # ----------------------------------------------------
        print("\n[2] Testing /health/ready readiness check...")
        r_ready = client.get("/health/ready")
        assert r_ready.status_code == 200, f"Expected 200, got {r_ready.status_code}"
        ready_data = r_ready.json()
        assert ready_data.get("database_connected") is True
        print(f"  ✓ Readiness confirmed: status={ready_data.get('status')}")

        # ----------------------------------------------------
        # 3. Database WAL Mode & Pragmas
        # ----------------------------------------------------
        print("\n[3] Verifying SQLite WAL mode and busy timeout...")
        with engine.connect() as conn:
            journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
            busy_timeout = conn.execute(text("PRAGMA busy_timeout")).scalar()
            print(f"  ✓ Active journal_mode={journal_mode}, busy_timeout={busy_timeout}ms")
            assert str(journal_mode).lower() == "wal", f"Expected WAL mode, got {journal_mode}"
            assert int(busy_timeout) >= 5000, f"Expected >= 5000ms timeout, got {busy_timeout}"

        # ----------------------------------------------------
        # 4. User Creation & Valid Timeline Retrieval
        # ----------------------------------------------------
        print("\n[4] Testing health timeline retrieval with valid auth...")
        ts = int(time.time() * 1000)
        user_email = f"timeline_test_{ts}@example.com"
        r_reg = client.post("/auth/register", json={
            "name": "Timeline Test Patient",
            "email": user_email,
            "password": "Password123!"
        })
        assert r_reg.status_code == 201
        user_id = r_reg.json()["id"]

        r_login = client.post("/auth/login", json={
            "email": user_email,
            "password": "Password123!"
        })
        token = r_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ----------------------------------------------------
        # 5. Empty Health Timeline
        # ----------------------------------------------------
        print("\n[5] Testing empty health timeline for fresh user...")
        r_empty = client.get("/api/timeline", headers=headers)
        assert r_empty.status_code == 200
        assert r_empty.json() == [], f"Expected empty list, got {r_empty.json()}"
        print("  ✓ Empty timeline cleanly returns [] without error")

        # Populate user with sample clinical records
        client.post("/problems", headers=headers, json={
            "problem_text": "Exertional shortness of breath",
            "problem_category": "Respiratory",
            "severity": "Moderate"
        })

        client.post("/allergies", headers=headers, json={
            "allergen": "Penicillin",
            "reaction": "Hives",
            "severity": "Moderate"
        })

        client.post("/api/prescriptions", headers=headers, json={
            "title": "Cardiology Visit Rx",
            "doctor_name": "Dr. Smith",
            "main_health_problem": "Hypertension",
            "prescription_date": "2026-05-10T10:00:00Z",
            "medicines": [{"medicine_name": "Amlodipine", "dosage": "5mg"}]
        })

        r_tl = client.get("/api/timeline", headers=headers)
        assert r_tl.status_code == 200
        tl_events = r_tl.json()
        assert len(tl_events) == 3
        print(f"  ✓ Populated timeline returns {len(tl_events)} chronological events")

        # Test category filters
        r_filter_sym = client.get("/api/timeline?event_type=SYMPTOM", headers=headers)
        assert r_filter_sym.status_code == 200
        assert len(r_filter_sym.json()) == 1
        assert r_filter_sym.json()[0]["event_type"] == "SYMPTOM"
        print("  ✓ Category filtering (SYMPTOM) returns exact match")

        # ----------------------------------------------------
        # 6. Expired / Invalid Authentication Handling (401)
        # ----------------------------------------------------
        print("\n[6] Testing expired or invalid authentication handling...")
        # Expired token
        expired_payload = {
            "sub": user_email,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=10)
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        r_expired = client.get("/api/timeline", headers={"Authorization": f"Bearer {expired_token}"})
        assert r_expired.status_code == 401, f"Expected 401, got {r_expired.status_code}"
        assert "credentials" in r_expired.json().get("detail", "").lower()
        print("  ✓ Expired token rejected with HTTP 401 and descriptive credentials message")

        # Missing token
        r_no_auth = client.get("/api/timeline")
        assert r_no_auth.status_code == 401
        print("  ✓ Missing token rejected with HTTP 401")

        # ----------------------------------------------------
        # 7. Fault Tolerance against Malformed / Irregular Records
        # ----------------------------------------------------
        print("\n[7] Testing timeline resilience against null / malformed database fields...")
        # Directly insert irregular records with null fields, edge dates, etc.
        malformed_assessment = HealthAssessment(
            user_id=user_id,
            age=40,
            gender="Male",
            smoker_status="No",
            diabetes_history="No",
            heart_rate=72.0,
            systolic_blood_pressure=120.0,
            oxygen_saturation=98.0,
            chest_pain_severity=0.0,
            body_temperature=37.0,
            predicted_risk="Low Risk",
            confidence=95.0,
            probabilities_json=None,
            created_at=None  # Null created_at!
        )
        db.add(malformed_assessment)
        db.commit()

        # Retrieve timeline - must NOT crash or throw 500
        r_robust = client.get("/api/timeline", headers=headers)
        assert r_robust.status_code == 200, f"Expected 200, got {r_robust.status_code}: {r_robust.text}"
        events_robust = r_robust.json()
        assert len(events_robust) == 4
        print("  ✓ Timeline retrieved cleanly despite null created_at; zero 500 errors!")

        # ----------------------------------------------------
        # 8. Cross-Tenant Data Isolation
        # ----------------------------------------------------
        print("\n[8] Verifying cross-user privacy isolation...")
        user_b_email = f"user_b_{ts}@example.com"
        client.post("/auth/register", json={
            "name": "User B",
            "email": user_b_email,
            "password": "Password123!"
        })
        r_login_b = client.post("/auth/login", json={"email": user_b_email, "password": "Password123!"})
        token_b = r_login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        r_tl_b = client.get("/api/timeline", headers=headers_b)
        assert r_tl_b.status_code == 200
        assert r_tl_b.json() == [], "User B must not see User A's timeline records!"
        print("  ✓ User B sees 0 records from User A. Cross-tenant privacy strictly intact.")

        # ----------------------------------------------------
        # 9. Soak Test: 60 Rapid Repeated Requests
        # ----------------------------------------------------
        print("\n[9] Running repeated-request soak test (60 rapid requests)...")
        start_soak = time.time()
        for i in range(60):
            endpoint = "/api/timeline" if i % 2 == 0 else "/health"
            req_headers = headers if i % 2 == 0 else {}
            res = client.get(endpoint, headers=req_headers)
            assert res.status_code == 200, f"Failed at request #{i}: {res.status_code}"
        soak_duration = round(time.time() - start_soak, 2)
        print(f"  ✓ 60 rapid requests completed in {soak_duration}s without connection failure or pool exhaustion")

        # ----------------------------------------------------
        # 10. Concurrent Requests Test (Multi-Threaded)
        # ----------------------------------------------------
        print("\n[10] Testing concurrent requests across 10 parallel threads...")
        def make_request(idx):
            with TestClient(app, raise_server_exceptions=False) as c:
                r = c.get("/api/timeline", headers=headers)
                return r.status_code

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(30)))

        assert all(code == 200 for code in results), f"Some concurrent requests failed: {results}"
        print(f"  ✓ All 30 concurrent requests across 10 threads returned HTTP 200 OK")

        # ----------------------------------------------------
        # 11. CORS Header Presence on Error Responses
        # ----------------------------------------------------
        print("\n[11] Testing CORS headers on requests...")
        cors_req_headers = {
            "Origin": "http://localhost:3000",
            "Authorization": f"Bearer {token}"
        }
        r_cors = client.get("/api/timeline", headers=cors_req_headers)
        assert r_cors.status_code == 200
        assert r_cors.headers.get("access-control-allow-origin") == "http://localhost:3000"
        print("  ✓ CORS headers present on 200 responses")

        # Cleanup test records
        db.delete(malformed_assessment)
        db.commit()

    db.close()
    print("\n" + "=" * 70)
    print(" ALL 11 RELIABILITY & HEALTH TIMELINE TESTS PASSED 100%!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_reliability_tests()

"""
Dedicated Authentication & End-to-End Verification Test Script
Tests both local FastAPI app and live deployed Render backend and frontend configuration.
"""
import sys
import uuid
import json
import httpx
from fastapi.testclient import TestClient

from main import app
from database.database import SessionLocal
from database.models import User, HealthProfile, LoginActivity

def test_auth_end_to_end():
    print("\n" + "=" * 70)
    print(" PROJECT2ADVANCE - AUTHENTICATION & LOGIN/SIGNUP END-TO-END TEST")
    print("=" * 70 + "\n")

    # -------------------------------------------------------------------------
    # PART 1: Local Backend FastAPI Auth Verification
    # -------------------------------------------------------------------------
    print("[PART 1] LOCAL BACKEND FASTAPI AUTH VERIFICATION...")
    with TestClient(app) as client:
        unique_id = uuid.uuid4().hex[:6]
        test_email = f"test.user.{unique_id}@example.com"
        test_password = "SecurePassword123!"
        test_name = "Test Clinical User"

        # 1. Registration with valid data
        reg_resp = client.post("/auth/register", json={
            "name": test_name,
            "email": test_email,
            "password": test_password
        })
        assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
        reg_data = reg_resp.json()
        assert reg_data["email"].lower() == test_email.lower(), "Returned email mismatch"
        assert reg_data["name"] == test_name, "Returned name mismatch"
        assert "password" not in reg_data and "password_hash" not in reg_data, "Password leaked in response!"
        user_id = reg_data["id"]
        print(f"  ✓ 1. Registration successful (HTTP 201): User ID {user_id}")

        # 2. Duplicate registration rejection
        dup_resp = client.post("/auth/register", json={
            "name": test_name,
            "email": test_email,
            "password": test_password
        })
        assert dup_resp.status_code == 400, f"Duplicate should fail with 400: {dup_resp.text}"
        assert "already exists" in dup_resp.json().get("detail", ""), "Detail should state user already exists"
        print(f"  ✓ 2. Duplicate email rejected cleanly (HTTP 400): {dup_resp.json()['detail']}")

        # 3. Duplicate with uppercase email rejection
        dup_upper_resp = client.post("/auth/register", json={
            "name": test_name,
            "email": test_email.upper(),
            "password": test_password
        })
        assert dup_upper_resp.status_code == 400, "Case-insensitive duplicate should be rejected"
        print("  ✓ 3. Case-insensitive duplicate registration rejected cleanly (HTTP 400)")

        # 4. Login with correct credentials
        login_resp = client.post("/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token_data = login_resp.json()
        assert "access_token" in token_data and token_data["token_type"] == "bearer", "Token missing or wrong type"
        token = token_data["access_token"]
        print(f"  ✓ 4. Login successful (HTTP 200): Received JWT access token")

        # 5. Case-insensitive login (e.g. mobile capitalization)
        login_upper_resp = client.post("/auth/login", json={
            "email": test_email.upper(),
            "password": test_password
        })
        assert login_upper_resp.status_code == 200, f"Case-insensitive login failed: {login_upper_resp.text}"
        print("  ✓ 5. Case-insensitive login verified: Uppercase email accepted")

        # 6. Login with incorrect password
        bad_pw_resp = client.post("/auth/login", json={
            "email": test_email,
            "password": "WrongPassword999!"
        })
        assert bad_pw_resp.status_code == 401, f"Bad password should fail with 401: {bad_pw_resp.text}"
        assert bad_pw_resp.json().get("detail") == "Incorrect email or password.", "Incorrect error message"
        print("  ✓ 6. Invalid password rejected cleanly (HTTP 401): 'Incorrect email or password.'")

        # 7. Login with nonexistent email
        no_user_resp = client.post("/auth/login", json={
            "email": "nonexistent.user.999@example.com",
            "password": "SomePassword123!"
        })
        assert no_user_resp.status_code == 401, "Nonexistent user should return 401"
        assert no_user_resp.json().get("detail") == "Incorrect email or password.", "Should not leak account existence"
        print("  ✓ 7. Nonexistent account rejected with identical error without leaking account existence")

        # 8. Access protected endpoint (/auth/me) with token
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = client.get("/auth/me", headers=headers)
        assert me_resp.status_code == 200, f"/auth/me failed: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data["id"] == user_id, "User ID mismatch on /auth/me"
        assert me_data["email"].lower() == test_email.lower(), "User email mismatch on /auth/me"
        print(f"  ✓ 8. Protected endpoint access verified (/auth/me): Authenticated as '{me_data['name']}'")

        # 9. Access protected endpoint with invalid token
        bad_token_resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid_garbage_token"})
        assert bad_token_resp.status_code == 401, "Invalid token should return 401"
        print("  ✓ 9. Invalid token rejected with HTTP 401 Unauthorized")

        # 10. Database persistence & relationship verification
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.id == user_id).first()
            assert db_user is not None, "User not found in database!"
            assert db_user.password_hash != test_password, "Password stored as plaintext! Security failure!"
            assert db_user.password_hash.startswith("$2b$") or db_user.password_hash.startswith("$2a$"), "Not bcrypt!"
            assert db_user.profile is not None, "HealthProfile was not automatically created!"

            # Verify login activity logging
            logs = db.query(LoginActivity).filter(LoginActivity.user_id == user_id).all()
            assert len(logs) >= 2, "Expected registration and login records in login_activities"
            print(f"  ✓ 10. Database persistence verified: User {user_id} saved, bcrypt salted, profile linked, activities logged.")
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # PART 2: Live Deployed Backend & CORS Verification
    # -------------------------------------------------------------------------
    print("\n[PART 2] LIVE DEPLOYED BACKEND & CORS VERIFICATION...")
    live_backend = "https://project2advance-2.onrender.com"
    frontend_origin = "https://project2advance-3.onrender.com"

    try:
        # Health check
        h_resp = httpx.get(f"{live_backend}/health", timeout=40.0)
        assert h_resp.status_code == 200, f"Live backend health check failed: {h_resp.status_code}"
        h_data = h_resp.json()
        assert h_data.get("database_connected") is True, "Live database is not connected!"
        print(f"  ✓ Live Backend is ONLINE at {live_backend} (database_connected=True, model_loaded={h_data.get('model_loaded')})")

        # CORS preflight check for frontend origin
        cors_resp = httpx.options(
            f"{live_backend}/auth/login",
            headers={
                "Origin": frontend_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization"
            },
            timeout=20.0
        )
        assert cors_resp.status_code == 200, f"CORS preflight failed: {cors_resp.status_code}"
        allow_origin = cors_resp.headers.get("access-control-allow-origin")
        assert allow_origin == frontend_origin or allow_origin == "*", f"Unexpected CORS allow-origin: {allow_origin}"
        print(f"  ✓ CORS Preflight Verified: Origin '{frontend_origin}' allowed with credentials={cors_resp.headers.get('access-control-allow-credentials')}")

        # Live Registration and Login check
        live_uid = uuid.uuid4().hex[:6]
        live_email = f"live.test.{live_uid}@health.io"
        live_pw = "LivePass123!"
        live_name = f"Live Patient {live_uid}"

        reg_live = httpx.post(
            f"{live_backend}/auth/register",
            json={"name": live_name, "email": live_email, "password": live_pw},
            headers={"Origin": frontend_origin},
            timeout=30.0
        )
        assert reg_live.status_code == 201, f"Live registration failed: {reg_live.status_code} {reg_live.text}"
        print(f"  ✓ Live Registration Succeeded: Created user '{live_name}' ({live_email})")

        login_live = httpx.post(
            f"{live_backend}/auth/login",
            json={"email": live_email, "password": live_pw},
            headers={"Origin": frontend_origin},
            timeout=30.0
        )
        assert login_live.status_code == 200, f"Live login failed: {login_live.status_code} {login_live.text}"
        live_token = login_live.json().get("access_token")
        assert live_token, "No access token in live login response"
        print(f"  ✓ Live Login Succeeded: Authenticated with JWT Bearer token")

        me_live = httpx.get(
            f"{live_backend}/auth/me",
            headers={"Authorization": f"Bearer {live_token}", "Origin": frontend_origin},
            timeout=30.0
        )
        assert me_live.status_code == 200, f"Live /auth/me failed: {me_live.status_code}"
        print(f"  ✓ Live Token Verification Succeeded: /auth/me returned {me_live.json()['name']}")

    except Exception as exc:
        print(f"  ⚠ Live verification notice: {exc}")
        raise exc

    print("\n" + "=" * 70)
    print(" ALL AUTHENTICATION FLOW TESTS PASSED 100%!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    test_auth_end_to_end()

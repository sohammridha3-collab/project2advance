"""
Test Suite for HealthBridge AI - Enhanced Personalized Exercise Recommendations
Verifies:
1. Low-risk profile -> Graduated Aerobic Cleared
2. Intermediate-risk profile -> Conservative Supervised Conditioning
3. High-risk profile -> Cautionary review & specialist guidance
4. Red Flag (Chest Pain >= 3) -> Exercise Contraindicated, Workouts Suppressed
5. Red Flag (Hypoxia O2 < 94) -> Exercise Contraindicated, Workouts Suppressed
6. Red Flag (Syncope / Fainting in Recent Problems) -> Exercise Contraindicated
7. Red Flag (Severe Hypertensive SBP >= 160) -> Exercise Contraindicated
8. Special Condition (Diabetes) -> Foot care & glucose checks attached
9. Dedicated Endpoint GET /api/recommendations/exercise -> Validated
10. Missing / Invalid Inputs -> 422 Unprocessable Entity
"""
import httpx
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 70)
    print("HEALTHBRIDGE AI - ENHANCED EXERCISE RECOMMENDATIONS TEST SUITE")
    print("=" * 70)
    
    with httpx.Client(base_url=BASE_URL, timeout=20.0) as client:
        # Register test user
        ts = int(time.time())
        username = f"ex_test_{ts}"
        password = "Password123!"
        
        reg_res = client.post("/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "name": "Exercise Test Patient",
            "password": password
        })
        assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
        
        login_res = client.post("/auth/login", json={
            "email": f"{username}@example.com",
            "password": password
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        print("✓ Test user registered & authenticated")

        # -------------------------------------------------------------
        # TEST 1: Low-Risk Profile
        # -------------------------------------------------------------
        print("\n[Test 1] Testing Low-Risk Stable Patient Profile...")
        low_input = {
            "age": 32,
            "gender": "Female",
            "smoker_status": "No",
            "diabetes_history": "No",
            "heart_rate": 68.0,
            "systolic_blood_pressure": 115.0,
            "oxygen_saturation": 99.0,
            "chest_pain_severity": 0.0,
            "body_temperature": 36.7
        }
        r1 = client.post("/api/recommendations", json=low_input)
        assert r1.status_code == 200, f"Test 1 failed: {r1.text}"
        d1 = r1.json()
        ep1 = d1["exercise_plan"]
        assert ep1 is not None, "exercise_plan is missing in response"
        assert ep1["safety_status"]["is_exercise_cleared"] is True
        assert ep1["safety_status"]["status_level"] == "Cleared"
        assert len(ep1["exercises"]) >= 3
        print(f"  ✓ Status Level: {ep1['safety_status']['status_level']}")
        print(f"  ✓ Recommendation Band: {ep1['recommendation_band']}")
        print(f"  ✓ Exercises Selected ({len(ep1['exercises'])}): {[e['name'] for e in ep1['exercises']]}")
        print(f"  ✓ Risk Influence Explanation: {ep1['risk_influence_explanation'][:120]}...")

        # -------------------------------------------------------------
        # TEST 2: Intermediate-Risk Profile (Moderate Risk)
        # -------------------------------------------------------------
        print("\n[Test 2] Testing Intermediate-Risk Profile (Moderate Risk vitals)...")
        mod_input = {
            "age": 58,
            "gender": "Male",
            "smoker_status": "Yes",
            "diabetes_history": "Yes",
            "heart_rate": 88.0,
            "systolic_blood_pressure": 145.0,
            "oxygen_saturation": 96.0,
            "chest_pain_severity": 0.0,
            "body_temperature": 37.1
        }
        r2 = client.post("/api/recommendations", json=mod_input)
        assert r2.status_code == 200, f"Test 2 failed: {r2.text}"
        d2 = r2.json()
        ep2 = d2["exercise_plan"]
        assert ep2["safety_status"]["is_exercise_cleared"] is True
        assert ep2["safety_status"]["status_level"] == "Cautionary_Supervised"
        assert "Conservative" in ep2["recommendation_band"]
        # Confirm diabetes precaution is included
        assert any("Diabetes" in g for g in ep2["general_guidelines"])
        print(f"  ✓ Status Level: {ep2['safety_status']['status_level']}")
        print(f"  ✓ Recommendation Band: {ep2['recommendation_band']}")
        print(f"  ✓ Cautionary Triggers: {ep2['safety_status']['trigger_factors']}")
        print(f"  ✓ Diabetes safety guideline included: True")

        # -------------------------------------------------------------
        # TEST 3: High-Risk Profile without acute red flags
        # -------------------------------------------------------------
        print("\n[Test 3] Testing High-Risk Profile (Senior, Elevated Vitals)...")
        high_input = {
            "age": 68,
            "gender": "Male",
            "smoker_status": "Yes",
            "diabetes_history": "Yes",
            "heart_rate": 96.0,
            "systolic_blood_pressure": 150.0,
            "oxygen_saturation": 95.0,
            "chest_pain_severity": 1.0,
            "body_temperature": 37.0
        }
        r3 = client.post("/api/recommendations", json=high_input)
        assert r3.status_code == 200, f"Test 3 failed: {r3.text}"
        ep3 = r3.json()["exercise_plan"]
        assert ep3["safety_status"]["status_level"] in ["Cautionary_Supervised", "Contraindicated_Urgent"]
        print(f"  ✓ High risk handled safely: Status={ep3['safety_status']['status_level']}")
        print(f"  ✓ Triggers: {ep3['safety_status']['trigger_factors']}")

        # -------------------------------------------------------------
        # TEST 4: Red Flag - Active Chest Pain Severity >= 3
        # -------------------------------------------------------------
        print("\n[Test 4] Testing Safety Suppression: Active Chest Pain (Severity 5.0/10)...")
        chest_pain_input = {
            "age": 52,
            "gender": "Male",
            "smoker_status": "No",
            "diabetes_history": "No",
            "heart_rate": 84.0,
            "systolic_blood_pressure": 130.0,
            "oxygen_saturation": 98.0,
            "chest_pain_severity": 5.0,
            "body_temperature": 36.9
        }
        r4 = client.post("/api/recommendations", json=chest_pain_input)
        assert r4.status_code == 200
        ep4 = r4.json()["exercise_plan"]
        assert ep4["safety_status"]["is_exercise_cleared"] is False
        assert ep4["safety_status"]["status_level"] == "Contraindicated_Urgent"
        assert any("chest pain" in t.lower() for t in ep4["safety_status"]["trigger_factors"])
        # Confirm workouts are strictly suppressed (0 workout prescriptions)
        assert len(ep4["exercises"]) == 0, f"Expected 0 routine exercises when contraindicated, got {len(ep4['exercises'])}"
        print(f"  ✓ Safety Layer Active: is_exercise_cleared={ep4['safety_status']['is_exercise_cleared']}")
        print(f"  ✓ Routine workouts strictly suppressed: True (0 exercises)")
        print(f"  ✓ Headline: {ep4['safety_status']['headline']}")

        # -------------------------------------------------------------
        # TEST 5: Red Flag - Severe Hypoxia (O2 < 94%)
        # -------------------------------------------------------------
        print("\n[Test 5] Testing Safety Suppression: Hypoxia (Oxygen Saturation 91%)...")
        hypoxia_input = {
            "age": 50,
            "gender": "Female",
            "smoker_status": "No",
            "diabetes_history": "No",
            "heart_rate": 78.0,
            "systolic_blood_pressure": 120.0,
            "oxygen_saturation": 91.0,
            "chest_pain_severity": 0.0,
            "body_temperature": 36.8
        }
        r5 = client.post("/api/recommendations", json=hypoxia_input)
        assert r5.status_code == 200
        ep5 = r5.json()["exercise_plan"]
        assert ep5["safety_status"]["is_exercise_cleared"] is False
        assert ep5["safety_status"]["status_level"] == "Contraindicated_Urgent"
        assert any("oxygen" in t.lower() for t in ep5["safety_status"]["trigger_factors"])
        print(f"  ✓ Hypoxia caught: is_exercise_cleared=False, Triggers={ep5['safety_status']['trigger_factors']}")

        # -------------------------------------------------------------
        # TEST 6: Red Flag - Syncope / Fainting Symptom in DB Recent Problems
        # -------------------------------------------------------------
        print("\n[Test 6] Testing Red Flag in User Database: Syncope / Fainting Complaint...")
        prob_res = client.post("/problems", headers=auth_headers, json={
            "problem_text": "Experienced sudden fainting and blackout episode after climbing a flight of stairs",
            "problem_category": "Cardiovascular",
            "severity": "Severe"
        })
        assert prob_res.status_code == 201
        
        # Now run recommendation for this authenticated user
        r6 = client.post("/api/recommendations", headers=auth_headers, json=low_input)
        assert r6.status_code == 200
        ep6 = r6.json()["exercise_plan"]
        assert ep6["safety_status"]["is_exercise_cleared"] is False
        assert ep6["safety_status"]["status_level"] == "Contraindicated_Urgent"
        assert any("syncope" in t.lower() or "faint" in t.lower() for t in ep6["safety_status"]["trigger_factors"])
        print(f"  ✓ Syncope DB history triggered contraindication: {ep6['safety_status']['trigger_factors']}")

        # -------------------------------------------------------------
        # TEST 7: Red Flag - Stage 2 Hypertensive Crisis (SBP >= 160)
        # -------------------------------------------------------------
        print("\n[Test 7] Testing Safety Suppression: Severe Hypertension (SBP 170 mmHg)...")
        htn_input = {
            "age": 55,
            "gender": "Male",
            "smoker_status": "No",
            "diabetes_history": "No",
            "heart_rate": 80.0,
            "systolic_blood_pressure": 170.0,
            "oxygen_saturation": 98.0,
            "chest_pain_severity": 0.0,
            "body_temperature": 36.8
        }
        r7 = client.post("/api/recommendations", json=htn_input)
        assert r7.status_code == 200
        ep7 = r7.json()["exercise_plan"]
        assert ep7["safety_status"]["is_exercise_cleared"] is False
        assert any("hypertensive" in t.lower() or "170" in t for t in ep7["safety_status"]["trigger_factors"])
        print(f"  ✓ SBP 170 mmHg triggered contraindication: {ep7['safety_status']['trigger_factors']}")

        # -------------------------------------------------------------
        # TEST 8: Dedicated Authenticated Endpoint GET /api/recommendations/exercise
        # -------------------------------------------------------------
        print("\n[Test 8] Testing Dedicated Endpoint GET /api/recommendations/exercise...")
        # Save a clean assessment first for this user
        save_res = client.post("/predict", headers=auth_headers, json=mod_input)
        assert save_res.status_code == 200
        
        r8 = client.get("/api/recommendations/exercise", headers=auth_headers)
        assert r8.status_code == 200, f"GET /api/recommendations/exercise failed: {r8.text}"
        ep8 = r8.json()
        assert "safety_status" in ep8
        assert "exercises" in ep8
        assert "risk_influence_explanation" in ep8
        print(f"  ✓ Dedicated endpoint returned valid plan: Headline='{ep8['safety_status']['headline']}'")

        # -------------------------------------------------------------
        # TEST 9: Missing / Invalid Inputs
        # -------------------------------------------------------------
        print("\n[Test 9] Testing Validation on Missing & Invalid Inputs...")
        # Missing required systolic_blood_pressure
        r9_missing = client.post("/api/recommendations", json={
            "age": 45,
            "gender": "Male"
        })
        assert r9_missing.status_code == 422, f"Expected 422 for missing inputs, got {r9_missing.status_code}"
        
        # Out-of-bounds heart rate
        r9_invalid = client.post("/api/recommendations", json={
            "age": 45,
            "gender": "Male",
            "smoker_status": "No",
            "diabetes_history": "No",
            "heart_rate": 500.0,  # Invalid (>250)
            "systolic_blood_pressure": 120.0,
            "oxygen_saturation": 98.0,
            "chest_pain_severity": 0.0,
            "body_temperature": 36.8
        })
        assert r9_invalid.status_code == 422, f"Expected 422 for invalid vital, got {r9_invalid.status_code}"
        print("  ✓ Schema validation correctly returned 422 for missing and out-of-range inputs")

        # -------------------------------------------------------------
        # TEST 10: Unauthorized Access to Protected Route
        # -------------------------------------------------------------
        print("\n[Test 10] Testing Unauthorized Access Protection...")
        r10_unauth = client.get("/api/recommendations/exercise")
        assert r10_unauth.status_code == 401
        print("  ✓ Protected exercise endpoint correctly rejects unauthenticated requests (HTTP 401)")

        # -------------------------------------------------------------
        # TEST 11: Direct Input Exercise Plan via POST /api/recommendations/exercise
        # -------------------------------------------------------------
        print("\n[Test 11] Testing Direct Input Exercise Evaluation (POST /api/recommendations/exercise)...")
        r11_direct = client.post("/api/recommendations/exercise", json=low_input)
        assert r11_direct.status_code == 200, f"POST /api/recommendations/exercise failed: {r11_direct.text}"
        ep11 = r11_direct.json()
        assert ep11["safety_status"]["is_exercise_cleared"] is True
        assert len(ep11["exercises"]) >= 3
        print(f"  ✓ Direct input endpoint returned {len(ep11['exercises'])} exercises for low-risk inputs")

    print("\n" + "=" * 70)
    print("ALL 11 EXERCISE RECOMMENDATION & SAFETY TESTS PASSED 100%!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

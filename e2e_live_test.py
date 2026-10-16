import httpx
import time
import json
import io

BASE_URL = "http://127.0.0.1:8000"

def run_live_e2e_journey():
    print("=" * 65)
    print("RUNNING LIVE END-TO-END 17-STEP VERIFICATION")
    print("=" * 65)
    
    timestamp = int(time.time())
    username_a = f"testuser_{timestamp}"
    password = "SecurePassword123!"
    
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Step 1: Register and login User A
        print("\n[Step 1] Registering and logging in User A...")
        r_reg = client.post("/auth/register", json={
            "username": username_a,
            "email": f"{username_a}@example.com",
            "name": "Dr. E2E Test Patient",
            "password": password
        })
        assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"
        
        r_login = client.post("/auth/login", json={
            "email": f"{username_a}@example.com",
            "password": password
        })
        assert r_login.status_code == 200, f"Login failed: {r_login.text}"
        token_a = r_login.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        print(f"  ✓ User A registered & authenticated (token: {token_a[:15]}...)")

        # Step 2 & 3: Enter health information and run ML prediction
        print("\n[Step 2 & 3] Enter health information & run ML prediction...")
        health_input = {
            "age": 58,
            "gender": "Male",
            "smoker_status": "Yes",
            "diabetes_history": "Yes",
            "heart_rate": 88.0,
            "systolic_blood_pressure": 155.0,
            "oxygen_saturation": 96.0,
            "chest_pain_severity": 4.5,
            "body_temperature": 37.1
        }
        r_pred = client.post("/predict", headers=headers_a, json=health_input)
        assert r_pred.status_code == 200, f"Prediction failed: {r_pred.text}"
        pred_res = r_pred.json()
        risk_level = pred_res["risk_level"]
        confidence = pred_res["confidence"]
        probabilities = pred_res["probabilities"]
        print(f"  ✓ ML inference output: Risk='{risk_level}', Confidence={confidence}%, Probabilities={probabilities}")

        # Step 4 & 5: View prediction results and confirm assessment is saved
        print("\n[Step 4 & 5] Confirm assessment is saved in database history...")
        r_hist = client.get("/predict/history", headers=headers_a)
        assert r_hist.status_code == 200
        history = r_hist.json()
        assert len(history) >= 1
        latest_hist = history[0]
        assert latest_hist["predicted_risk"] == risk_level
        print(f"  ✓ Assessment successfully persisted to database history with ID #{latest_hist['id']}")

        # Step 6: Add a recent health problem
        print("\n[Step 6] Adding a recent health problem...")
        r_prob = client.post("/problems", headers=headers_a, json={
            "problem_text": "Exertional chest tightness radiating to shoulder during moderate walking",
            "severity": "Moderate",
            "duration": "3 weeks"
        })
        assert r_prob.status_code == 201, f"Failed to add problem: {r_prob.text}"
        problem_id = r_prob.json()["id"]
        print(f"  ✓ Recent health problem logged to DB with ID #{problem_id} (Category: {r_prob.json().get('problem_category')})")

        # Step 7: Upload and save a prescription
        print("\n[Step 7] Upload and save prescription document...")
        sample_file = io.BytesIO(b"%PDF-1.4 Clinical Prescription Document Sample for Heart Risk System Test")
        files = {"file": ("cardiologist_rx.pdf", sample_file, "application/pdf")}
        data = {
            "prescription_date": "2026-09-15",
            "main_health_problem": "Hypertension and Angina Pectoris",
            "doctor_name": "Dr. Sarah Jenkins, MD",
            "hospital_name": "Metropolitan Cardiology Clinic",
            "diagnosis": "Essential Hypertension Stage 2",
            "notes": "Take morning dose after meal. Regular BP monitoring advised.",
            "medicines": json.dumps([
                {"medicine_name": "Amlodipine", "dosage": "5 mg", "frequency": "Once daily", "duration": "30 days"}
            ])
        }
        r_presc = client.post("/api/prescriptions", headers=headers_a, data=data, files=files)
        assert r_presc.status_code == 201, f"Prescription upload failed: {r_presc.text}"
        presc = r_presc.json()
        presc_id = presc["id"]
        print(f"  ✓ Prescription #{presc_id} created with secure file storage & 1 initial medicine")

        # Step 8: Add structured medicine details
        print("\n[Step 8] Add additional structured medicine details...")
        r_med = client.post(f"/api/prescriptions/{presc_id}/medicines", headers=headers_a, json={
            "medicine_name": "Atorvastatin",
            "dosage": "20 mg",
            "frequency": "Once at bedtime",
            "duration": "90 days",
            "instructions": "Lipid lowering therapy"
        })
        assert r_med.status_code == 201, f"Failed to add medicine: {r_med.text}"
        added_med_id = r_med.json()["id"]
        print(f"  ✓ Medicine #{added_med_id} (Atorvastatin) added to prescription #{presc_id}")

        # Step 9: Open and edit prescription details
        print("\n[Step 9] Open and edit prescription details & medicine details...")
        r_edit_presc = client.put(f"/api/prescriptions/{presc_id}", headers=headers_a, json={
            "main_health_problem": "Hypertension, Angina, and Hyperlipidemia",
            "doctor_name": "Dr. Sarah Jenkins, FACC",
            "notes": "Updated instructions: strictly monitor sodium intake."
        })
        assert r_edit_presc.status_code == 200, f"Edit prescription failed: {r_edit_presc.text}"
        assert r_edit_presc.json()["main_health_problem"] == "Hypertension, Angina, and Hyperlipidemia"
        
        r_edit_med = client.put(f"/api/prescriptions/{presc_id}/medicines/{added_med_id}", headers=headers_a, json={
            "medicine_name": "Atorvastatin",
            "dosage": "40 mg",
            "frequency": "Once at bedtime"
        })
        assert r_edit_med.status_code == 200, f"Edit medicine failed: {r_edit_med.text}"
        assert r_edit_med.json()["dosage"] == "40 mg"
        print(f"  ✓ Prescription details and medicine #{added_med_id} edited successfully")

        # Step 10: Add an allergy
        print("\n[Step 10] Add an allergy...")
        r_allergy = client.post("/allergies", headers=headers_a, json={
            "allergen": "Aspirin",
            "reaction": "Acute urticaria and bronchospasm",
            "severity": "Severe"
        })
        assert r_allergy.status_code == 201, f"Failed to add allergy: {r_allergy.text}"
        allergy_id = r_allergy.json()["id"]
        print(f"  ✓ Allergy logged with ID #{allergy_id} (Aspirin - Severe)")

        # Step 11 & 12: Open Recommended endpoint & confirm it uses actual stored records
        print("\n[Step 11 & 12] Open Recommendations API and confirm real stored records are evaluated...")
        r_rec = client.get("/api/recommendations", headers=headers_a)
        assert r_rec.status_code == 200, f"Recommendations failed: {r_rec.text}"
        rec_data = r_rec.json()
        
        context_used = rec_data.get("patient_context_used", {})
        assert context_used.get("recent_problems_count", 0) >= 1, "Recent problems not reflected in context"
        assert context_used.get("previous_prescriptions_count", 0) >= 1, "Prescriptions not reflected in context"
        assert context_used.get("active_allergies_count", 0) >= 1, "Allergies not reflected in context"
        print(f"  ✓ Stored database records confirmed in context:")
        print(f"    - Recent problems considered: {context_used.get('recent_problems_count')}")
        print(f"    - Prescriptions in vault considered: {context_used.get('previous_prescriptions_count')}")
        print(f"    - Active allergies considered: {context_used.get('active_allergies_count')}")
        print(f"    - Historical medicines considered: {context_used.get('historical_medicines_considered')}")

        # Step 13: Verify applicable safety warnings
        print("\n[Step 13] Verify applicable safety warnings (Allergy conflict on Aspirin)...")
        med_infos = rec_data.get("medicine_information", [])
        aspirin_screened = next((m for m in med_infos if m["medicine_name"].lower() == "aspirin"), None)
        assert aspirin_screened is not None, "Aspirin candidate was not screened"
        assert aspirin_screened["potential_conflict"] is True, "Allergy conflict was not flagged on Aspirin"
        assert "allergy" in (aspirin_screened["warning"] or "").lower(), "Allergy warning text missing"
        print(f"  ✓ Allergy conflict verified: {aspirin_screened['warning']}")

        # Step 14: Delete a test record after confirmation
        print("\n[Step 14] Delete a test record (the allergy)...")
        r_del_al = client.delete(f"/allergies/{allergy_id}", headers=headers_a)
        assert r_del_al.status_code == 204, f"Delete allergy failed: {r_del_al.status_code}"
        
        r_check_al = client.get("/allergies", headers=headers_a)
        assert all(a["id"] != allergy_id for a in r_check_al.json()), "Deleted allergy still in DB"
        print(f"  ✓ Allergy #{allergy_id} successfully deleted from database")

        # Step 15: Refresh application and verify persistence
        print("\n[Step 15] Verify persistence of remaining records...")
        r_presc_list = client.get("/api/prescriptions", headers=headers_a)
        assert any(p["id"] == presc_id for p in r_presc_list.json()), "Prescription not persisted"
        
        r_prob_list = client.get("/problems", headers=headers_a)
        assert any(p["id"] == problem_id for p in r_prob_list.json()), "Problem not persisted"
        print(f"  ✓ Data persistence verified across requests")

        # Step 16: Verify that another user's records cannot be accessed (Isolation)
        print("\n[Step 16] Verify cross-user security isolation...")
        username_b = f"intruder_{timestamp}"
        client.post("/auth/register", json={
            "username": username_b,
            "email": f"{username_b}@example.com",
            "name": "Intruder User",
            "password": password
        })
        r_login_b = client.post("/auth/login", json={"email": f"{username_b}@example.com", "password": password})
        headers_b = {"Authorization": f"Bearer {r_login_b.json()['access_token']}"}
        
        # User B attempts to access User A's prescription
        r_sec_p = client.get(f"/api/prescriptions/{presc_id}", headers=headers_b)
        assert r_sec_p.status_code in [403, 404], f"Cross-user isolation breach on prescription: {r_sec_p.status_code}"
        
        # User B attempts to access User A's prescription file
        r_sec_f = client.get(f"/api/prescriptions/{presc_id}/file", headers=headers_b)
        assert r_sec_f.status_code in [403, 404], f"Cross-user file download breach: {r_sec_f.status_code}"

        # User B attempts to edit User A's prescription
        r_sec_edit = client.put(f"/api/prescriptions/{presc_id}", headers=headers_b, json={"doctor_name": "Hacked"})
        assert r_sec_edit.status_code in [403, 404], f"Cross-user edit breach: {r_sec_edit.status_code}"
        print(f"  ✓ User isolation verified: 404/403 returned, cross-user data strictly inaccessible")

        # Clean up test prescription
        client.delete(f"/api/prescriptions/{presc_id}", headers=headers_a)
        client.delete(f"/problems/{problem_id}", headers=headers_a)
        print(f"  ✓ Test cleanup completed")

    print("\n" + "=" * 65)
    print("ALL 16 LIVE API & DATA INTEGRATION STEPS PASSED 100%!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_live_e2e_journey()

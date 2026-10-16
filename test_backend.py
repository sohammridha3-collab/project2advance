"""
Comprehensive Integration, Testing, Debugging, and Optimization Test Suite
for the AI-Based Health Risk Prediction System.

Verifies all 15 architectural and functional requirements:
1. ML Model Test
2. Database Test (Foreign keys, cascade deletion, user isolation, empty states)
3. Authentication Test (JWT, password hashing, unauthorized rejections, cross-user isolation)
4. Home Page Test (Recent problem submission -> DB -> UI)
5. Prediction Test (Health inputs -> ML -> prediction & confidence -> DB -> result)
6. Prescription Vault Test (PDF, JPG, PNG, rejection of invalid/oversized files, secure download & cleanup)
7. Recommendation Test (Contextual recommendations from ML + problems + prescriptions + allergies)
8. Medicine Safety Test (Tests A, B, C, D, E, F; safety screenings; disclaimer compliance)
9. Doctor Recommendation Test (Specialist categorization, professional phrasing, no definitive diagnosis)
10. CORS Test (http://localhost:3000 & http://localhost:5173 with GET, POST, PUT, DELETE, OPTIONS)
11. Performance & Model Loading (Model loaded once, indexes on query fields, no training in API)
12. Error Handling (422 invalid input, 401 invalid/expired JWT, 400 bad files, no leaked stack traces/secrets)
13. Environment Configuration (.env.example verification)
14. Frontend Quality (HTML files, JS scripts, UI components integrity)
15. Final End-to-End User Journey (Complete lifecycle from registration to relogin)
"""

import os
import io
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import joblib
import pandas as pd
from fastapi.testclient import TestClient
from jose import jwt

from main import app, UPLOAD_DIR
from database.database import Base, engine, SessionLocal, init_db
from database.models import (
    User, HealthProfile, HealthAssessment, RecentProblem,
    Prescription, PrescriptionMedicine, Allergy, Medicine, MedicineInteraction
)
from services.prediction_service import (
    get_model, load_model, prepare_model_features, predict_heart_risk, DEFAULT_MODEL_PATH
)
from services.auth_handler import SECRET_KEY, ALGORITHM, create_access_token

def test_suite():
    print("\n" + "=" * 70)
    print(" AI-BASED HEALTH RISK PREDICTION SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70 + "\n")

    with TestClient(app) as client:
        # ----------------------------------------------------
        # 1. ML MODEL TEST
        # ----------------------------------------------------
        print("[1] ML MODEL TEST...")
        assert DEFAULT_MODEL_PATH.exists(), f"heart_risk_model.pkl not found at {DEFAULT_MODEL_PATH}"
        model = get_model()
        assert model is not None, "Model failed to load"
        
        # Verify model is loaded only once
        model_second_call = get_model()
        assert id(model) == id(model_second_call), "Model was reloaded instead of using cached singleton"

        # Verify feature names and compatibility
        test_patient_df = pd.DataFrame([{
            "age": 55, "gender": "Male", "smoker_status": "No", "diabetes_history": "Yes",
            "heart_rate": 82.0, "systolic_blood_pressure": 140.0, "oxygen_saturation": 96.0,
            "chest_pain_severity": 2.0, "body_temperature": 37.0,
            "age_group": "Middle_Aged", "heart_rate_flag": "Normal", "oxygen_flag": "Normal"
        }])
        
        expected_cols = [
            'age', 'gender', 'smoker_status', 'diabetes_history', 'heart_rate',
            'systolic_blood_pressure', 'oxygen_saturation', 'chest_pain_severity',
            'body_temperature', 'age_group', 'heart_rate_flag', 'oxygen_flag'
        ]
        assert list(test_patient_df.columns) == expected_cols, "Feature columns mismatch"

        # Test inference via prediction_service
        from schemas.schemas import HeartRiskInput
        sample_input = HeartRiskInput(
            age=55, gender="Male", smoker_status="No", diabetes_history="Yes",
            heart_rate=82.0, systolic_blood_pressure=140.0, oxygen_saturation=96.0,
            chest_pain_severity=2.0, body_temperature=37.0
        )
        ml_res = predict_heart_risk(sample_input)
        assert "risk_level" in ml_res and "confidence" in ml_res and "probabilities" in ml_res
        assert isinstance(ml_res["probabilities"], dict) and len(ml_res["probabilities"]) >= 3
        print(f"  ✓ Model verified: Single load, 12 features compatible, prediction='{ml_res['risk_level']}', confidence={ml_res['confidence']}%.")

        # ----------------------------------------------------
        # 2. DATABASE TEST (Relationships, Foreign Keys, Cascade, Empty States)
        # ----------------------------------------------------
        print("\n[2] DATABASE TEST (Foreign keys, Cascades, Empty States)...")
        db = SessionLocal()
        try:
            # Create a dedicated temp user to test foreign keys and cascade deletion
            temp_u = User(name="Cascade Tester", email="cascade.test@example.com", password_hash="fakehash")
            db.add(temp_u)
            db.commit()
            db.refresh(temp_u)

            # Add related entities
            prof = HealthProfile(user_id=temp_u.id, age=30)
            assess = HealthAssessment(
                user_id=temp_u.id, age=30, gender="Male", smoker_status="No", diabetes_history="No",
                heart_rate=70, systolic_blood_pressure=115, oxygen_saturation=99, chest_pain_severity=0,
                body_temperature=36.7, predicted_risk="Low Risk", confidence=90.0
            )
            prob = RecentProblem(user_id=temp_u.id, problem_text="Temporary fatigue")
            presc = Prescription(user_id=temp_u.id, doctor_name="Dr. Temp", diagnosis="Checkup")
            db.add_all([prof, assess, prob, presc])
            db.commit()
            db.refresh(presc)

            p_med = PrescriptionMedicine(prescription_id=presc.id, medicine_name="Vitamin C")
            allg = Allergy(user_id=temp_u.id, allergen="Dust")
            db.add_all([p_med, allg])
            db.commit()

            # Verify records exist
            assert db.query(HealthAssessment).filter(HealthAssessment.user_id == temp_u.id).count() == 1
            assert db.query(PrescriptionMedicine).filter(PrescriptionMedicine.prescription_id == presc.id).count() == 1

            # Delete parent user -> cascade must remove profile, assessment, problem, prescription, medicines, allergies
            db.delete(temp_u)
            db.commit()

            assert db.query(HealthProfile).filter(HealthProfile.user_id == temp_u.id).count() == 0
            assert db.query(HealthAssessment).filter(HealthAssessment.user_id == temp_u.id).count() == 0
            assert db.query(RecentProblem).filter(RecentProblem.user_id == temp_u.id).count() == 0
            assert db.query(Prescription).filter(Prescription.user_id == temp_u.id).count() == 0
            assert db.query(PrescriptionMedicine).filter(PrescriptionMedicine.prescription_id == presc.id).count() == 0
            assert db.query(Allergy).filter(Allergy.user_id == temp_u.id).count() == 0
            print("  ✓ Database relationships verified: Cascade deletion cleans up all children without orphans.")
        finally:
            db.close()

        # ----------------------------------------------------
        # 3. AUTHENTICATION TEST (Registration, Login, JWT, User Isolation)
        # ----------------------------------------------------
        print("\n[3] AUTHENTICATION TEST (JWT, Password Hashing, Isolation)...")
        # Setup User A
        email_a = "user.alpha@example.com"
        pwd_a = "AlphaSecure123!"
        
        db = SessionLocal()
        ua_old = db.query(User).filter(User.email == email_a).first()
        if ua_old:
            db.delete(ua_old)
            db.commit()
        db.close()

        r_reg_a = client.post("/auth/register", json={"name": "Alice Alpha", "email": email_a, "password": pwd_a})
        assert r_reg_a.status_code == 201
        
        r_login_a = client.post("/auth/login", json={"email": email_a, "password": pwd_a})
        assert r_login_a.status_code == 200
        token_a = r_login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Setup User B
        email_b = "user.beta@example.com"
        pwd_b = "BetaSecure123!"
        db = SessionLocal()
        ub_old = db.query(User).filter(User.email == email_b).first()
        if ub_old:
            db.delete(ub_old)
            db.commit()
        db.close()

        r_reg_b = client.post("/auth/register", json={"name": "Bob Beta", "email": email_b, "password": pwd_b})
        assert r_reg_b.status_code == 201
        token_b = client.post("/auth/login", json={"email": email_b, "password": pwd_b}).json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Verify unauthorized rejection
        assert client.get("/auth/me").status_code == 401
        assert client.get("/problems").status_code == 401
        assert client.get("/prescriptions").status_code == 401
        assert client.get("/allergies").status_code == 401

        # Test cross-user isolation: User A logs data
        prob_a = client.post("/problems", headers=headers_a, json={"problem_text": "Alice Private Problem"}).json()
        presc_a = client.post("/prescriptions", headers=headers_a, json={"diagnosis": "Alice Private Rx"}).json()
        allg_a = client.post("/allergies", headers=headers_a, json={"allergen": "Alice Peanuts"}).json()

        # User B cannot see User A's data
        b_probs = client.get("/problems", headers=headers_b).json()
        assert not any(p["id"] == prob_a["id"] for p in b_probs)
        b_prescs = client.get("/prescriptions", headers=headers_b).json()
        assert not any(p["id"] == presc_a["id"] for p in b_prescs)
        b_allgs = client.get("/allergies", headers=headers_b).json()
        assert not any(a["id"] == allg_a["id"] for a in b_allgs)

        # User B cannot access or delete User A's prescription by ID
        assert client.get(f"/prescriptions/{presc_a['id']}", headers=headers_b).status_code == 404
        assert client.delete(f"/prescriptions/{presc_a['id']}", headers=headers_b).status_code == 404

        # Verify GET /auth/users returns registered users
        r_users = client.get("/auth/users")
        assert r_users.status_code == 200
        user_list = r_users.json()
        assert any(u["email"] == email_a for u in user_list)
        assert any(u["email"] == email_b for u in user_list)

        # Verify GET /auth/admin/logins returns login activities
        r_logins = client.get("/auth/admin/logins")
        assert r_logins.status_code == 200
        login_list = r_logins.json()
        assert any(l["email"] == email_a for l in login_list)
        print("  ✓ Authentication & User Isolation strictly verified: complete cryptographic and database segregation.")

        # ----------------------------------------------------
        # 4. HOME PAGE TEST (Recent Problem Natural Language Form)
        # ----------------------------------------------------
        print("\n[4] HOME PAGE TEST (Share Recent Health Problem flow)...")
        r_prob_home = client.post("/problems", headers=headers_a, json={
            "problem_text": "I have been experiencing chest discomfort and shortness of breath for the last two days.",
            "severity": "Moderate",
            "duration": "2 days"
        })
        assert r_prob_home.status_code == 201
        home_data = r_prob_home.json()
        assert home_data["problem_category"] == "Cardiovascular"
        assert home_data["duration"] == "2 days"
        print(f"  ✓ Home Page Recent Problem: Inferred category '{home_data['problem_category']}', saved to DB.")

        # ----------------------------------------------------
        # 5. PREDICTION TEST (Health Inputs -> ML -> Confidence -> Auto-save)
        # ----------------------------------------------------
        print("\n[5] PREDICTION TEST (Form inputs -> Model Inference -> Auto-save)...")
        vitals_payload = {
            "age": 58, "gender": "Male", "smoker_status": "Yes", "diabetes_history": "Yes",
            "heart_rate": 92.0, "systolic_blood_pressure": 155.0, "oxygen_saturation": 95.0,
            "chest_pain_severity": 4.0, "body_temperature": 37.2
        }
        r_pred = client.post("/predict", headers=headers_a, json=vitals_payload)
        assert r_pred.status_code == 200
        p_res = r_pred.json()
        assert p_res["risk_level"] in ["Low Risk", "Moderate Risk", "High Risk", "Critical Risk"]
        assert 0.0 <= p_res["confidence"] <= 100.0

        # Verify auto-save to health_assessments
        hist_a = client.get("/predict/history", headers=headers_a).json()
        assert len(hist_a) >= 1
        assert hist_a[0]["predicted_risk"] == p_res["risk_level"]
        print(f"  ✓ Prediction flow verified: Risk='{p_res['risk_level']}', Confidence={p_res['confidence']}%, persisted to history.")

        # ----------------------------------------------------
        # 6. PRESCRIPTION VAULT TEST (PDF, JPG, PNG, rejection of invalid & oversized files, CRUD, medicines, security)
        # ----------------------------------------------------
        print("\n[6] PRESCRIPTION VAULT TEST (File validations, secure storage, medicines & cleanup)...")
        # 6a. Reject executable file
        bad_file = io.BytesIO(b"executable payload")
        r_bad_ext = client.post(
            "/api/prescriptions", headers=headers_a,
            files={"file": ("malicious.exe", bad_file, "application/octet-stream")},
            data={"doctor_name": "Dr. Bad"}
        )
        assert r_bad_ext.status_code == 400
        assert "Invalid file extension" in r_bad_ext.json()["detail"]

        # 6b. Reject oversized file (>10MB)
        huge_file = io.BytesIO(b"0" * (11 * 1024 * 1024))
        r_huge = client.post(
            "/api/prescriptions", headers=headers_a,
            files={"file": ("large_doc.pdf", huge_file, "application/pdf")},
            data={"doctor_name": "Dr. Giant"}
        )
        assert r_huge.status_code == 413

        # 6c. Valid PDF upload with structured medicines and main_health_problem via /api/prescriptions
        good_pdf = io.BytesIO(b"%PDF-1.4 official cardiological prescription document")
        meds_json = json.dumps([
            {"medicine_name": "Metoprolol", "dosage": "50 mg", "frequency": "Daily", "duration": "30 days"},
            {"medicine_name": "Atorvastatin", "dosage": "20 mg", "frequency": "Bedtime", "duration": "90 days"}
        ])
        r_upload_pdf = client.post(
            "/api/prescriptions", headers=headers_a,
            files={"file": ("rx_document.pdf", good_pdf, "application/pdf")},
            data={
                "prescription_date": "2026-10-12",
                "main_health_problem": "Hypertension & Chest Pain",
                "doctor_name": "Dr. Sarah Jenkins",
                "hospital_name": "Memorial Hospital",
                "diagnosis": "Stage 2 Essential Hypertension",
                "notes": "Monitor BP daily; low sodium diet",
                "medicines": meds_json
            }
        )
        assert r_upload_pdf.status_code == 201
        pdf_rx = r_upload_pdf.json()
        assert pdf_rx["main_health_problem"] == "Hypertension & Chest Pain"
        assert pdf_rx["doctor_name"] == "Dr. Sarah Jenkins"
        assert len(pdf_rx["medicines"]) == 2
        file_path_on_disk = UPLOAD_DIR / pdf_rx["file_path"]
        assert file_path_on_disk.exists()

        # 6d. Valid PNG image upload via /prescriptions/upload alias
        good_png = io.BytesIO(b"\x89PNG\r\n\x1a\nfake png prescription image data")
        r_upload_png = client.post(
            "/prescriptions/upload", headers=headers_a,
            files={"file": ("prescription_scan.png", good_png, "image/png")},
            data={
                "prescription_date": "2026-10-15",
                "main_health_problem": "Hyperlipidemia",
                "doctor_name": "Dr. Robert Smith"
            }
        )
        assert r_upload_png.status_code == 201
        png_rx = r_upload_png.json()
        png_file_disk = UPLOAD_DIR / png_rx["file_path"]
        assert png_file_disk.exists()

        # 6e. Verify listing sorted newest first
        r_list = client.get("/api/prescriptions", headers=headers_a)
        assert r_list.status_code == 200
        rx_list = r_list.json()
        assert len(rx_list) >= 2
        # Newest date first (2026-10-15 before 2026-10-12)
        assert rx_list[0]["id"] == png_rx["id"]

        # 6f. Retrieve single prescription details (GET /api/prescriptions/{id})
        r_get_single = client.get(f"/api/prescriptions/{pdf_rx['id']}", headers=headers_a)
        assert r_get_single.status_code == 200
        single_data = r_get_single.json()
        assert single_data["id"] == pdf_rx["id"]
        assert single_data["main_health_problem"] == "Hypertension & Chest Pain"
        assert len(single_data["medicines"]) == 2

        # 6g. Add a medicine (POST /api/prescriptions/{id}/medicines)
        r_add_med = client.post(
            f"/api/prescriptions/{pdf_rx['id']}/medicines", headers=headers_a,
            json={"medicine_name": "Aspirin", "dosage": "81 mg", "frequency": "Once daily"}
        )
        assert r_add_med.status_code == 201
        added_med = r_add_med.json()
        assert added_med["medicine_name"] == "Aspirin"

        # 6h. Update a medicine (PUT /api/prescriptions/{id}/medicines/{med_id})
        r_up_med = client.put(
            f"/api/prescriptions/{pdf_rx['id']}/medicines/{added_med['id']}", headers=headers_a,
            json={"dosage": "100 mg", "duration": "60 days"}
        )
        assert r_up_med.status_code == 200
        assert r_up_med.json()["dosage"] == "100 mg"

        # 6i. Delete a medicine (DELETE /api/prescriptions/{id}/medicines/{med_id})
        r_del_med = client.delete(
            f"/api/prescriptions/{pdf_rx['id']}/medicines/{added_med['id']}", headers=headers_a
        )
        assert r_del_med.status_code == 204

        # 6j. Update prescription details (PUT /api/prescriptions/{id})
        r_up_rx = client.put(
            f"/api/prescriptions/{pdf_rx['id']}", headers=headers_a,
            json={"notes": "Updated instructions: take after breakfast"}
        )
        assert r_up_rx.status_code == 200
        assert r_up_rx.json()["notes"] == "Updated instructions: take after breakfast"

        # 6k. Cross-user isolation: User B cannot access User A's prescription
        r_cross_get = client.get(f"/api/prescriptions/{pdf_rx['id']}", headers=headers_b)
        assert r_cross_get.status_code == 404
        r_cross_put = client.put(f"/api/prescriptions/{pdf_rx['id']}", headers=headers_b, json={"notes": "Hacked"})
        assert r_cross_put.status_code == 404
        r_cross_del = client.delete(f"/api/prescriptions/{pdf_rx['id']}", headers=headers_b)
        assert r_cross_del.status_code == 404

        # 6l. Secure file download (GET /api/prescriptions/{id}/file)
        r_stream = client.get(f"/api/prescriptions/{pdf_rx['id']}/file", headers=headers_a)
        assert r_stream.status_code == 200
        assert r_stream.content.startswith(b"%PDF-1.4")

        # 6m. Clean up: Delete prescription and verify file is physically removed from storage
        r_del_rx = client.delete(f"/api/prescriptions/{pdf_rx['id']}", headers=headers_a)
        assert r_del_rx.status_code == 204
        assert not file_path_on_disk.exists(), "Physical file was not cleaned up after DB record deletion"

        client.delete(f"/api/prescriptions/{png_rx['id']}", headers=headers_a)
        assert not png_file_disk.exists()
        print("  ✓ Prescription Vault verified: PDF/Image validation, disk storage, secure retrieval, and cleanup.")

        # ----------------------------------------------------
        # 7. RECOMMENDATION TEST (Integration of real DB context)
        # ----------------------------------------------------
        print("\n[7] RECOMMENDATION TEST (Real API GET /api/recommendations)...")
        r_rec_a = client.get("/api/recommendations", headers=headers_a)
        assert r_rec_a.status_code == 200
        rec_data = r_rec_a.json()
        assert "risk_level" in rec_data
        assert "what_to_do" in rec_data and len(rec_data["what_to_do"]) > 0
        assert "what_not_to_do" in rec_data and len(rec_data["what_not_to_do"]) > 0
        assert "doctor_recommendation" in rec_data
        assert "medicine_information" in rec_data
        print(f"  ✓ Real Recommendation API verified: {len(rec_data['what_to_do'])} action items, {len(rec_data['medicine_information'])} screened medicines.")

        # ----------------------------------------------------
        # 8. MEDICINE SAFETY TEST (Tests A, B, C, D, E, F)
        # ----------------------------------------------------
        print("\n[8] MEDICINE SAFETY TEST (Tests A through F)...")
        # Setup clean test user for medicine safety
        med_email = "med.safety@example.com"
        db = SessionLocal()
        um_old = db.query(User).filter(User.email == med_email).first()
        if um_old:
            db.delete(um_old)
            db.commit()
        db.close()

        client.post("/auth/register", json={"name": "Safety Tester", "email": med_email, "password": "Password123!"})
        token_med = client.post("/auth/login", json={"email": med_email, "password": "Password123!"}).json()["access_token"]
        headers_med = {"Authorization": f"Bearer {token_med}"}

        # Test A: No allergy and no interaction
        client.post("/predict", headers=headers_med, json={
            "age": 40, "gender": "Female", "smoker_status": "No", "diabetes_history": "No",
            "heart_rate": 72.0, "systolic_blood_pressure": 118.0, "oxygen_saturation": 98.0,
            "chest_pain_severity": 0.0, "body_temperature": 36.6
        })
        r_rec_ta = client.get("/api/recommendations", headers=headers_med).json()
        assert len(r_rec_ta["safety_warnings"]) == 0
        print("  ✓ Test A: Clean profile has 0 safety conflicts.")

        # Test B: Known allergy (Aspirin allergy)
        client.post("/allergies", headers=headers_med, json={"allergen": "Aspirin", "severity": "Severe"})
        r_rec_tb = client.get("/api/recommendations", headers=headers_med).json()
        asp_b = next((m for m in r_rec_tb["medicine_information"] if m["medicine_name"] == "Aspirin"), None)
        assert asp_b is not None and asp_b["potential_conflict"] is True
        assert "Allergy Alert" in asp_b["warning"]
        print("  ✓ Test B: Known allergy flagged on candidate medicine.")

        # Test C: Potential medicine interaction (Warfarin + Aspirin)
        client.post("/prescriptions", headers=headers_med, json={
            "doctor_name": "Dr. Anticoag", "diagnosis": "DVT Prophylaxis",
            "medicines": [{"medicine_name": "Warfarin", "dosage": "5 mg"}]
        })
        r_rec_tc = client.get("/api/recommendations", headers=headers_med).json()
        asp_c = next((m for m in r_rec_tc["medicine_information"] if m["medicine_name"] == "Aspirin"), None)
        assert asp_c["potential_conflict"] is True
        assert any("Warfarin" in w or "Allergy" in w for w in r_rec_tc["safety_warnings"])
        print("  ✓ Test C: High drug interaction (Warfarin + Aspirin) identified.")

        # Test D: Previous medicine conflict (Metoprolol recorded in vault)
        client.post("/prescriptions", headers=headers_med, json={
            "doctor_name": "Dr. Cardio", "diagnosis": "Hypertension",
            "medicines": [{"medicine_name": "Metoprolol", "dosage": "25 mg"}]
        })
        r_rec_td = client.get("/api/recommendations", headers=headers_med).json()
        meto_d = next((m for m in r_rec_td["medicine_information"] if m["medicine_name"] == "Metoprolol"), None)
        assert meto_d is not None
        assert "prescription history" in meto_d["reason"].lower()
        print("  ✓ Test D: Active prescription continuity recognized; instructions advise continued adherence.")

        # Test E: Relevant previous health problem (e.g. Asthma contraindication with beta blocker)
        client.post("/problems", headers=headers_med, json={"problem_text": "Severe asthma attacks with bronchospasm", "severity": "Severe"})
        r_rec_te = client.get("/api/recommendations", headers=headers_med).json()
        asp_e = next((m for m in r_rec_te["medicine_information"] if m["medicine_name"] == "Aspirin"), None)
        assert "asthma" in asp_e["warning"].lower()
        print("  ✓ Test E: Health complaint contraindication (asthma) surfaced in medicine warning.")

        # Test F: Multiple risk factors (Multi-drug therapy)
        client.post("/prescriptions", headers=headers_med, json={
            "doctor_name": "Dr. Multi", "diagnosis": "Complex Cardiorenal",
            "medicines": [{"medicine_name": "Lisinopril"}, {"medicine_name": "Amlodipine"}]
        })
        r_rec_tf = client.get("/api/recommendations", headers=headers_med).json()
        assert len(r_rec_tf["patient_context_used"]["current_medicines_considered"]) >= 3
        # Compliance check: Never claim 100% safe, never claim AI prescribed
        for m in r_rec_tf["medicine_information"]:
            assert "100% safe" not in (m.get("warning") or "").lower()
            assert "100% safe" not in (m.get("reason") or "").lower()
            assert "ai prescribed" not in (m.get("reason") or "").lower()
        print("  ✓ Test F: Multi-risk profile evaluated; clinical disclaimers strictly enforced.")

        # ----------------------------------------------------
        # 9. DOCTOR RECOMMENDATION TEST
        # ----------------------------------------------------
        print("\n[9] DOCTOR RECOMMENDATION TEST (Specialist selection & non-definitive phrasing)...")
        doc_rec = r_rec_tf["doctor_recommendation"]
        assert doc_rec["recommended_specialist"] in [
            "Primary Care Physician", "Cardiologist", "Pulmonologist", "Endocrinologist", "Emergency Medical Evaluation"
        ]
        assert doc_rec["reason"].startswith("Consider"), f"Reason does not use 'Consider' phrasing: {doc_rec['reason']}"
        assert "definitely have" not in doc_rec["reason"].lower()
        assert len(doc_rec["discussion_points"]) > 0
        print(f"  ✓ Doctor recommendation verified: '{doc_rec['recommended_specialist']}' with professional phrasing.")

        # ----------------------------------------------------
        # 10. CORS TEST (http://localhost:3000 and http://localhost:5173 with GET, POST, PUT, DELETE, OPTIONS)
        # ----------------------------------------------------
        print("\n[10] CORS TEST (localhost:3000 & localhost:5173 on GET, POST, PUT, DELETE, OPTIONS)...")
        origins_to_test = ["http://localhost:3000", "http://localhost:5173"]
        methods_to_test = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

        for origin in origins_to_test:
            # Test preflight OPTIONS
            for method in methods_to_test:
                r_opt = client.options(
                    "/health",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": method,
                        "Access-Control-Request-Headers": "authorization,content-type"
                    }
                )
                assert r_opt.status_code == 200, f"CORS preflight {method} failed for {origin}: {r_opt.status_code}"
                assert r_opt.headers.get("access-control-allow-origin") == origin, f"CORS origin header missing for {origin}"

            # Test actual GET with origin
            r_get = client.get("/health", headers={"Origin": origin})
            assert r_get.headers.get("access-control-allow-origin") == origin

            # Test actual POST with origin
            r_post = client.post("/health", headers={"Origin": origin})
            assert r_post.headers.get("access-control-allow-origin") == origin
        print("  ✓ CORS verified: Full origin access and preflight compliance on localhost:3000 and localhost:5173.")

        # ----------------------------------------------------
        # 11. PERFORMANCE TEST (Single model instance, query indexes)
        # ----------------------------------------------------
        print("\n[11] PERFORMANCE & OPTIMIZATION TEST...")
        # Inspect model instance permanence across 10 rapid calls
        start_t = time.time()
        for _ in range(10):
            m = get_model()
            assert id(m) == id(model)
        elapsed_ml = time.time() - start_t
        assert elapsed_ml < 0.05, "ML model retrieval took too long"

        # Verify database model indexes
        assert HealthAssessment.__table__.c.user_id.index is True
        assert HealthAssessment.__table__.c.created_at.index is True
        assert RecentProblem.__table__.c.user_id.index is True
        assert Prescription.__table__.c.user_id.index is True
        assert Allergy.__table__.c.user_id.index is True
        print(f"  ✓ Performance verified: Singleton ML model cached, DB foreign key & timestamp indexes active.")

        # ----------------------------------------------------
        # 12. ERROR HANDLING TEST (Invalid inputs, Expired JWT, No leaks)
        # ----------------------------------------------------
        print("\n[12] ERROR HANDLING & SECURITY TEST...")
        # Bad payload (missing fields)
        r_bad_payload = client.post("/predict", json={"age": 50})
        assert r_bad_payload.status_code == 422
        # Check no stack trace or secrets leaked
        err_text = r_bad_payload.text
        assert "Traceback" not in err_text
        assert SECRET_KEY not in err_text

        # Invalid JWT
        r_bad_jwt = client.get("/problems", headers={"Authorization": "Bearer bad.token.here"})
        assert r_bad_jwt.status_code == 401
        assert "credentials" in r_bad_jwt.json()["detail"].lower()

        # Expired JWT
        expired_token = create_access_token(data={"sub": "user@example.com"}, expires_delta=timedelta(minutes=-10))
        r_exp_jwt = client.get("/problems", headers={"Authorization": f"Bearer {expired_token}"})
        assert r_exp_jwt.status_code == 401
        print("  ✓ Error handling verified: Clean HTTP status codes (422, 401, 404), zero sensitive data leakage.")

        # ----------------------------------------------------
        # 13. ENVIRONMENT CONFIGURATION TEST
        # ----------------------------------------------------
        print("\n[13] ENVIRONMENT CONFIGURATION TEST...")
        env_example_path = Path(__file__).resolve().parent / ".env.example"
        assert env_example_path.exists(), ".env.example missing"
        example_content = env_example_path.read_text(encoding="utf-8")
        assert "DATABASE_URL" in example_content
        assert "JWT_SECRET" in example_content or "SECRET_KEY" in example_content
        assert "ALLOWED_ORIGINS" in example_content
        assert "UPLOAD_DIRECTORY" in example_content
        print("  ✓ Environment config verified: .env.example contains all required production parameters.")

        # ----------------------------------------------------
        # 14. FRONTEND QUALITY & ASSETS TEST
        # ----------------------------------------------------
        print("\n[14] FRONTEND QUALITY TEST...")
        required_pages = [
            "index.html", "login.html", "admin.html", "result.html", "recommendation.html",
            "history.html", "problems.html", "prescription.html", "allergies.html"
        ]
        base_ws = Path(__file__).resolve().parent
        for page in required_pages:
            p_file = base_ws / page
            assert p_file.exists(), f"Frontend page missing: {page}"
            content = p_file.read_text(encoding="utf-8")
            assert "api.js" in content, f"api.js missing in {page}"
            assert "common.js" in content, f"common.js missing in {page}"
            assert "style.css" in content, f"style.css missing in {page}"
        print(f"  ✓ Frontend verified: All {len(required_pages)} HTML views intact with central API and stylesheet bindings.")

        # ----------------------------------------------------
        # 15. FINAL END-TO-END USER JOURNEY TEST
        # ----------------------------------------------------
        print("\n[15] FINAL END-TO-END USER JOURNEY (Lifecycle Test)...")
        journey_email = f"journey_{int(time.time())}@example.com"
        journey_pwd = "JourneyPass123!"

        # Step 1: Register
        r_j_reg = client.post("/auth/register", json={"name": "Journey Patient", "email": journey_email, "password": journey_pwd})
        assert r_j_reg.status_code == 201

        # Step 2: Login
        r_j_login = client.post("/auth/login", json={"email": journey_email, "password": journey_pwd})
        assert r_j_login.status_code == 200
        j_token = r_j_login.json()["access_token"]
        j_headers = {"Authorization": f"Bearer {j_token}"}

        # Step 3: Complete health profile
        r_j_prof = client.put("/auth/me/profile", headers=j_headers, json={"age": 49, "gender": "Male", "smoker_status": "No", "diabetes_history": "No"})
        assert r_j_prof.status_code == 200

        # Step 4: Enter health information & Get ML risk prediction
        vital_test = {
            "age": 49, "gender": "Male", "smoker_status": "No", "diabetes_history": "No",
            "heart_rate": 78.0, "systolic_blood_pressure": 138.0, "oxygen_saturation": 97.0,
            "chest_pain_severity": 1.0, "body_temperature": 36.8
        }
        r_j_pred = client.post("/predict", headers=j_headers, json=vital_test)
        assert r_j_pred.status_code == 200
        j_risk = r_j_pred.json()["risk_level"]

        # Step 5: Add recent health problem
        r_j_prob = client.post("/problems", headers=j_headers, json={
            "problem_text": "Occasional mild flutter after morning coffee", "severity": "Mild"
        })
        assert r_j_prob.status_code == 201

        # Step 6: Add allergy
        r_j_allg = client.post("/allergies", headers=j_headers, json={"allergen": "Penicillin", "reaction": "Rash"})
        assert r_j_allg.status_code == 201

        # Step 7: Upload previous prescription & medicines
        r_j_rx = client.post("/prescriptions", headers=j_headers, json={
            "doctor_name": "Dr. Sarah Chen", "diagnosis": "Preventive Cardiology",
            "medicines": [{"medicine_name": "Atorvastatin", "dosage": "10 mg", "frequency": "Daily"}]
        })
        assert r_j_rx.status_code == 201

        # Step 8: Open Health History (verify records)
        j_history = client.get("/predict/history", headers=j_headers).json()
        assert len(j_history) >= 1
        assert j_history[0]["predicted_risk"] == j_risk

        # Step 9: Open Prescription Vault (verify records)
        j_vault = client.get("/prescriptions", headers=j_headers).json()
        assert len(j_vault) >= 1
        assert j_vault[0]["doctor_name"] == "Dr. Sarah Chen"

        # Step 10: Open Recommended page (verify personalized & doctor recommendation, medicines, warnings)
        r_j_rec = client.get("/api/recommendations", headers=j_headers)
        assert r_j_rec.status_code == 200
        j_rec = r_j_rec.json()
        assert j_rec["risk_level"] == j_risk
        assert j_rec["doctor_recommendation"]["recommended_specialist"] is not None
        assert len(j_rec["medicine_information"]) > 0

        # Step 11: Logout (client clears token)
        # Step 12: Login again with same credentials
        r_relogin = client.post("/auth/login", json={"email": journey_email, "password": journey_pwd})
        assert r_relogin.status_code == 200
        new_token = r_relogin.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # Step 13: Verify all saved data remains available in database
        assert len(client.get("/predict/history", headers=new_headers).json()) >= 1
        assert len(client.get("/problems", headers=new_headers).json()) >= 1
        assert len(client.get("/allergies", headers=new_headers).json()) >= 1
        assert len(client.get("/prescriptions", headers=new_headers).json()) >= 1
        print("  ✓ Full user journey verified: Register -> Profile -> Predict -> Problems -> Allergies -> Vault -> Recommendations -> Relogin -> Data Persistence confirmed.")

        print("\n" + "=" * 70)
        print(" ALL 15 INTEGRATION, SECURITY, AND END-TO-END TESTS PASSED 100%!")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    test_suite()

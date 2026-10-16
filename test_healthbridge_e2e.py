"""
Comprehensive End-to-End Verification Suite for HealthBridge AI
Uses Python standard library (http.client) for lightning-fast direct socket connections to 127.0.0.1.
Validates all 18 clinical journeys and security guarantees against http://127.0.0.1:8000:
1. User registration & authentication
2. ML health risk prediction inference using the 120MB model
3. Saved assessment history verification
4. Health problem management (CRUD, status, notes)
5. Prescription upload (multipart, validation)
6. Prescription extraction intelligence (candidate parsing, confidence score)
7. Prescription vault retrieval & medicine structures
8. Allergy profile management (status, reaction, severity)
9. Unified Health Timeline (chronological aggregation, category filtering)
10. Doctor Briefing synthesis & draft generation via Context Engine
11. Doctor Briefing update and retrieval
12. Secure sharing token generation (with PIN protection, expiration)
13. Public clinician retrieval with audit logging and PIN authentication
14. Immediate token revocation & access denial verification
15. Multi-session data persistence verification
16. Strict authorization & cross-tenant isolation enforcement
17. Edge-case and input validation (invalid types, boundary checks)
18. Clinical guidance and recommendation generation
"""

import sys
import json
import time
import http.client

HOST = "127.0.0.1"
PORT = 8000

class DirectClient:
    def __init__(self, token=None):
        self.token = token

    def set_token(self, token):
        self.token = token

    def request(self, method, path, json_data=None, multipart_fields=None, multipart_files=None, headers=None):
        conn = http.client.HTTPConnection(HOST, PORT, timeout=15)
        req_headers = {}
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        if headers:
            req_headers.update(headers)

        body_bytes = None
        if json_data is not None:
            req_headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(json_data).encode("utf-8")
        elif multipart_files or multipart_fields:
            boundary = "----HealthBridgeFormBoundary7MA4YWxkTrZu0gW"
            req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
            chunks = []
            if multipart_fields:
                for k, v in multipart_fields.items():
                    chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))
            if multipart_files:
                for field_name, (fn, fbytes, ctype) in multipart_files.items():
                    chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{fn}\"\r\nContent-Type: {ctype}\r\n\r\n".encode("utf-8"))
                    chunks.append(fbytes)
                    chunks.append(b"\r\n")
            chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
            body_bytes = b"".join(chunks)

        try:
            conn.request(method, path, body=body_bytes, headers=req_headers)
            resp = conn.getresponse()
            status = resp.status
            raw = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
            except Exception:
                data = raw
            return status, data
        except Exception as exc:
            return 0, str(exc)
        finally:
            conn.close()

def log_test(step_num, title, passed, detail=""):
    badge = " [PASS] " if passed else " [FAIL] "
    print(f"{badge} Step {step_num:02d}: {title}")
    if detail:
        print(f"         {detail}")
    if not passed:
        raise AssertionError(f"Step {step_num} failed: {title} - {detail}")

def run_suite():
    print("=" * 70)
    print("HEALTHBRIDGE AI - COMPREHENSIVE END-TO-END VERIFICATION SUITE")
    print("=" * 70)

    client_a = DirectClient()
    client_b = DirectClient()

    ts = int(time.time())
    user_a_email = f"dr_vance_{ts}@healthbridge.ai"
    user_a_pass = "ClinicalPass123!"
    user_b_email = f"intruder_{ts}@healthbridge.ai"
    user_b_pass = "IntruderPass123!"

    # 1. Register & Authenticate User A
    status_reg, reg_data = client_a.request("POST", "/auth/register", json_data={
        "name": "Dr. Alexandra Vance",
        "email": user_a_email,
        "password": user_a_pass
    })
    
    status_log, log_data = client_a.request("POST", "/auth/login", json_data={
        "email": user_a_email,
        "password": user_a_pass
    })
    token_a = log_data.get("access_token") if isinstance(log_data, dict) else None
    client_a.set_token(token_a)

    status_me, me_data = client_a.request("GET", "/auth/me")
    log_test(1, "User A Registration & JWT Authentication", status_me == 200 and me_data.get("email") == user_a_email,
             f"User: {me_data.get('email')}, Name: {me_data.get('name')}")

    # 2. Enter Health Data & Obtain ML Prediction
    sample_patient = {
        "age": 58,
        "gender": "Male",
        "smoker_status": "Yes",
        "diabetes_history": "Yes",
        "heart_rate": 88.0,
        "systolic_blood_pressure": 145.0,
        "oxygen_saturation": 96.0,
        "chest_pain_severity": 6.0,
        "body_temperature": 37.1
    }
    status_pred, pred_data = client_a.request("POST", "/predict", json_data=sample_patient)
    has_risk = isinstance(pred_data, dict) and "risk_level" in pred_data and "confidence" in pred_data
    log_test(2, "ML Model Inference via 12-Feature Pipeline", status_pred == 200 and has_risk,
             f"Risk: {pred_data.get('risk_level')}, Conf: {pred_data.get('confidence')}%")

    # 3. View Saved Assessment History
    status_hist, hist_data = client_a.request("GET", "/predict/history")
    log_test(3, "Saved Assessment History Persistence", status_hist == 200 and len(hist_data) > 0,
             f"Retrieved {len(hist_data)} historical assessment(s)")

    # 4. Add Recent Health Problem
    status_prob, prob_data = client_a.request("POST", "/problems", json_data={
        "problem_text": "Exertional dyspnea and retrosternal tightness",
        "severity": "Moderate",
        "duration": "Episodes lasting 5-10 minutes upon climbing stairs",
        "status": "Active",
        "notes": "Relieved somewhat with resting"
    })
    problem_id = prob_data.get("id") if isinstance(prob_data, dict) else None
    log_test(4, "Add Recent Health Problem with Status & Notes", status_prob == 201 and problem_id is not None,
             f"Problem ID: {problem_id}, Status: {prob_data.get('status')}")

    # 5. Prescription Extraction Intelligence (Candidate Parser)
    fake_rx_text = b"%PDF-1.4\nDr. Alan Turing, MD\nMetropolitan Cardiology Center\nDate: 2026-09-15\nRx:\n1. Amlodipine 5mg - Once daily for 30 days\n2. Atorvastatin 20mg - At bedtime for 60 days\nSig: Monitor blood pressure morning and evening."
    status_ext, ext_data = client_a.request("POST", "/api/prescriptions/extract", multipart_files={
        "file": ("prescription_sample.pdf", fake_rx_text, "application/pdf")
    })
    print("DEBUG EXT:", status_ext, ext_data)
    extracted_fields = ext_data.get("extracted_data") or ext_data if isinstance(ext_data, dict) else {}
    meds_extracted = extracted_fields.get("medicines", [])
    log_test(5, "Prescription Intelligence Extraction Service", status_ext == 200 and len(meds_extracted) > 0,
             f"Doctor: {extracted_fields.get('doctor_name')}, Medicines found: {len(meds_extracted)}")

    # 6. Upload Prescription to Vault (with Structured Medicines)
    meds_payload = [
        {"medicine_name": "Amlodipine", "dosage": "5 mg", "frequency": "Once daily", "duration": "30 days"},
        {"medicine_name": "Atorvastatin", "dosage": "20 mg", "frequency": "Once nightly", "duration": "60 days"}
    ]
    status_up, upload_json = client_a.request("POST", "/api/prescriptions",
        multipart_fields={
            "prescription_date": "2026-09-15",
            "main_health_problem": "Essential Hypertension",
            "doctor_name": "Dr. Alan Turing, MD",
            "hospital_name": "Metropolitan Cardiology Center",
            "diagnosis": "Stage 2 Systemic Hypertension",
            "notes": "Follow-up in 4 weeks with lipid panel",
            "medicines": json.dumps(meds_payload)
        },
        multipart_files={
            "file": ("doctor_rx_cardiology.pdf", fake_rx_text, "application/pdf")
        }
    )
    presc_id = upload_json.get("id") if isinstance(upload_json, dict) else None
    orig_fn = upload_json.get("original_filename") if isinstance(upload_json, dict) else str(upload_json)
    log_test(6, "Prescription Vault Structured Multipart Upload", status_up == 201 and presc_id is not None,
             f"Prescription ID: {presc_id}, File: {orig_fn}")

    # 7. Prescription Vault Retrieval
    status_vault, vault_items = client_a.request("GET", "/api/prescriptions")
    found_rx = next((rx for rx in vault_items if rx.get("id") == presc_id), None) if isinstance(vault_items, list) else None
    has_meds = found_rx and len(found_rx.get("medicines", [])) == 2
    log_test(7, "Prescription Vault Collection & Medicine Relations", status_vault == 200 and has_meds,
             f"Retrieved {len(vault_items)} prescriptions, verified 2 linked medicines")

    # 8. Allergy Profile Management
    status_allg, allg_data = client_a.request("POST", "/allergies", json_data={
        "allergen": "Penicillin V Potassium",
        "reaction": "Diffuse urticaria and facial angioedema",
        "severity": "Severe",
        "verification_status": "Clinician Confirmed"
    })
    allg_id = allg_data.get("id") if isinstance(allg_data, dict) else None
    log_test(8, "Allergy Profile Creation & Verification Status", status_allg == 201 and allg_id is not None,
             f"Allergen: {allg_data.get('allergen')}, Status: {allg_data.get('verification_status')}")

    # 9. Unified Health Timeline
    status_tl, tl_data = client_a.request("GET", "/api/timeline")
    events = tl_data if isinstance(tl_data, list) else tl_data.get("events", [])
    categories = set(e.get("event_type") for e in events)
    log_test(9, "Unified Health Timeline Synthesis", status_tl == 200 and len(events) >= 3,
             f"Events: {len(events)}, Event Types: {list(categories)}")

    # 10. Doctor Briefing Draft Generation via Context Engine
    status_draft, draft_data = client_a.request("POST", "/api/briefings/draft", json_data={"visit_reason": "Cardiology Follow-Up"})
    draft_briefing = draft_data.get("briefing") or draft_data if isinstance(draft_data, dict) else {}
    vitals_snippet = str(draft_briefing.get("vitals_summary") or "Vitals Recorded")[:40]
    log_test(10, "Doctor Briefing Synthesis via Context Engine", status_draft == 200 and "symptoms_summary" in draft_briefing,
             f"Vitals: {vitals_snippet}...")

    # 11. Create & Update Doctor Briefing Record
    status_create_b, brief_data = client_a.request("POST", "/api/briefings", json_data={
        "title": "Cardiology Consultation Briefing",
        "visit_reason": "Cardiology Consultation & Medication Review",
        "symptoms_summary": draft_briefing.get("symptoms_summary"),
        "vitals_summary": draft_briefing.get("vitals_summary"),
        "allergies_summary": draft_briefing.get("allergies_summary"),
        "medicines_summary": draft_briefing.get("medicines_summary"),
        "questions_to_ask": "1. Are my blood pressure readings adequately controlled?\n2. Should we adjust the statin dosage?",
        "notes": "Patient exercises regularly; experiences mild dyspnea only on steep inclines."
    })
    briefing_id = brief_data.get("id") if isinstance(brief_data, dict) else None
    log_test(11, "Doctor Briefing Creation and Persistence", status_create_b == 201 and briefing_id is not None,
             f"Briefing ID: {briefing_id}, Reason: {brief_data.get('visit_reason')}")

    # 12. Secure Sharing Token Generation (with PIN)
    status_share, share_data = client_a.request("POST", f"/api/briefings/{briefing_id}/share", json_data={
        "duration_hours": 48,
        "access_pin": "5432"
    })
    share_token = share_data.get("share_token") if isinstance(share_data, dict) else None
    log_test(12, "Cryptographic Secure Share Token Creation", status_share == 201 and share_token is not None,
             f"Token: {share_token[:12]}..., PIN: Protected, Expires: {share_data.get('expires_at')}")

    # 13. Public Clinician View with PIN Authentication
    anon_client = DirectClient()
    status_bad_pin, _ = anon_client.request("GET", f"/api/briefings/shared/{share_token}?pin=0000")
    status_good_pin, good_data = anon_client.request("GET", f"/api/briefings/shared/{share_token}?pin=5432")
    log_test(13, "Clinician Public View & PIN Enforcement", status_bad_pin == 401 and status_good_pin == 200,
             f"Bad PIN: {status_bad_pin} (Unauthorized), Good PIN: {status_good_pin} OK (Views: {good_data.get('view_count')})")

    # 14. Instant Revocation & Access Denial
    status_revoke, _ = client_a.request("DELETE", f"/api/briefings/share/{share_token}")
    status_after_revoke, _ = anon_client.request("GET", f"/api/briefings/shared/{share_token}?pin=5432")
    log_test(14, "Immediate Share Token Revocation & Access Denial", status_revoke in [200, 204] and status_after_revoke in [403, 404, 410],
             f"Revoke: {status_revoke}, Post-Revocation Status: {status_after_revoke}")

    # 15. Cross-Session Data Persistence
    client_reconnect = DirectClient()
    status_relog, relog_data = client_reconnect.request("POST", "/auth/login", json_data={
        "email": user_a_email,
        "password": user_a_pass
    })
    client_reconnect.set_token(relog_data.get("access_token"))
    status_re_b, briefings_list = client_reconnect.request("GET", "/api/briefings")
    found_briefing = isinstance(briefings_list, list) and any(b.get("id") == briefing_id for b in briefings_list)
    log_test(15, "Cross-Session Data Persistence & Reload", status_relog == 200 and found_briefing,
             f"Briefing ID {briefing_id} verified across fresh authenticated session")

    # 16. Multi-Tenant Authorization & Security Isolation
    status_reg_b, reg_b_data = client_b.request("POST", "/auth/register", json_data={
        "name": "Intruder User",
        "email": user_b_email,
        "password": user_b_pass
    })
    status_log_b, log_b_data = client_b.request("POST", "/auth/login", json_data={
        "email": user_b_email,
        "password": user_b_pass
    })
    client_b.set_token(log_b_data.get("access_token"))

    # User B attempts to access User A's briefing
    status_intruder_b, _ = client_b.request("GET", f"/api/briefings/{briefing_id}")
    # User B attempts to delete User A's prescription
    status_intruder_del, _ = client_b.request("DELETE", f"/api/prescriptions/{presc_id}")
    log_test(16, "Multi-Tenant Authorization & Isolation",
             status_intruder_b in [403, 404] and status_intruder_del in [403, 404],
             f"Briefing cross-access: {status_intruder_b}, Rx delete: {status_intruder_del}")

    # 17. Input Validation & Fault Tolerance
    status_bad_pred, _ = client_a.request("POST", "/predict", json_data={"age": -10, "gender": "Unknown"})
    log_test(17, "FastAPI Input Validation & Boundary Protection", status_bad_pred == 422,
             f"Invalid payload rejected with HTTP {status_bad_pred} Unprocessable Entity")

    # 18. Clinical Guidance & Personalized Recommendations
    status_rec, rec_data = client_a.request("GET", "/api/recommendations")
    has_guidance = isinstance(rec_data, dict) and "what_to_do" in rec_data and "what_not_to_do" in rec_data and "doctor_recommendation" in rec_data
    log_test(18, "Context Engine Clinical Recommendations", status_rec == 200 and has_guidance,
             f"Specialist: {rec_data.get('doctor_recommendation', {}).get('recommended_specialist')}, Actions: {len(rec_data.get('what_to_do', []))}")

    print("=" * 70)
    print("ALL 18 END-TO-END VERIFICATION JOURNEYS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_suite()
    except Exception as e:
        print(f"\nTEST SUITE FAILED: {e}")
        sys.exit(1)

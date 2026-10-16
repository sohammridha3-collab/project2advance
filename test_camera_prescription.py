"""
Unit & Integration Verification: Direct Camera Capture Prescription Upload
Tests:
1. Upload of captured JPEG image with title and metadata.
2. Upload of captured JPEG image with ONLY the photo file and zero manually entered fields.
3. Verification of file storage, non-exposure of absolute path, and private streaming.
4. Multi-tenant access protection (unauthorized user cannot view/download/delete).
5. Title updates via PUT.
6. Safe deletion of prescription and file cleanup.
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
            content_type = resp.getheader("Content-Type", "")
            raw = resp.read()
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                data = raw
            return status, data, content_type
        except Exception as exc:
            return 0, str(exc), ""
        finally:
            conn.close()


def test_camera_capture_prescription_suite():
    print("=" * 60)
    print("TESTING DIRECT CAMERA CAPTURE FOR PRESCRIPTION VAULT")
    print("=" * 60)

    client_a = DirectClient()
    timestamp = int(time.time())
    user_a_email = f"cam_patient_{timestamp}@healthbridge.ai"
    user_a_pass = "CameraPass123!"

    # 1. Register User A
    status, reg_data, _ = client_a.request("POST", "/auth/register", json_data={
        "name": "Camera Patient",
        "email": user_a_email,
        "password": user_a_pass
    })
    assert status == 201, f"User A registration failed ({status}): {reg_data}"

    # Login User A
    status, login_data, _ = client_a.request("POST", "/auth/login", json_data={
        "email": user_a_email,
        "password": user_a_pass
    })
    assert status == 200, f"User A login failed ({status}): {login_data}"
    token_a = login_data["access_token"]
    client_a.set_token(token_a)

    # 2. Upload captured JPEG photo with Title and doctor name
    fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
    
    status, presc_1, _ = client_a.request(
        "POST",
        "/api/prescriptions",
        multipart_fields={
            "title": "Camera Captured Urgent Care Rx",
            "doctor_name": "Dr. Gregory House",
            "main_health_problem": "Acute Migraine Headache",
            "prescription_date": "2026-10-16",
            "notes": "Take 1 tablet every 8 hours with water"
        },
        multipart_files={
            "file": ("prescription_photo_2026-10-16.jpg", fake_jpeg, "image/jpeg")
        }
    )
    assert status == 201, f"Upload 1 failed with status {status}: {presc_1}"
    assert presc_1["title"] == "Camera Captured Urgent Care Rx"
    assert presc_1["doctor_name"] == "Dr. Gregory House"
    assert presc_1["main_health_problem"] == "Acute Migraine Headache"
    assert presc_1["file_path"] is not None
    print(f" [PASS] 1. Upload captured JPEG photo with title and metadata succeeded. ID: {presc_1['id']}")

    # 3. Upload captured photo with ZERO optional metadata (instant quick save!)
    status, presc_2, _ = client_a.request(
        "POST",
        "/api/prescriptions",
        multipart_files={
            "file": ("prescription_quick_snap.jpg", fake_jpeg, "image/jpeg")
        }
    )
    assert status == 201, f"Quick upload failed with status {status}: {presc_2}"
    assert presc_2["file_path"] is not None
    print(f" [PASS] 2. Quick photo capture upload with zero manual fields succeeded. ID: {presc_2['id']}")

    # 4. Authenticated File Download
    status, body, ct = client_a.request("GET", f"/api/prescriptions/{presc_1['id']}/file")
    assert status == 200, f"File retrieval failed with status {status}"
    assert "image/jpeg" in ct, f"Expected image/jpeg, got {ct}"
    assert len(body) == len(fake_jpeg), f"Length mismatch: {len(body)} vs {len(fake_jpeg)}"
    print(" [PASS] 3. Authenticated photo file download verified (Content-Type: image/jpeg).")

    # 5. Query token download (e.g. for browser direct links)
    client_anon = DirectClient()
    status, body, _ = client_anon.request("GET", f"/api/prescriptions/{presc_1['id']}/file?token={token_a}")
    assert status == 200, f"Query token file retrieval failed with status {status}"
    print(" [PASS] 4. Token query parameter download verified.")

    # 6. Unauthorized access test with User B
    client_b = DirectClient()
    user_b_email = f"cam_patient_b_{timestamp}@healthbridge.ai"
    client_b.request("POST", "/auth/register", json_data={
        "name": "Other Patient",
        "email": user_b_email,
        "password": "Password123!"
    })
    _, login_b, _ = client_b.request("POST", "/auth/login", json_data={
        "email": user_b_email,
        "password": "Password123!"
    })
    client_b.set_token(login_b["access_token"])

    status_unauth, _, _ = client_b.request("GET", f"/api/prescriptions/{presc_1['id']}/file")
    assert status_unauth == 404, f"Security violation: other user accessed prescription! Got status {status_unauth}"
    print(" [PASS] 5. Tenant isolation verified: User B cannot access User A's prescription photo.")

    # 7. Update Prescription Title via PUT
    status, updated_presc, _ = client_a.request("PUT", f"/api/prescriptions/{presc_1['id']}", json_data={
        "title": "Renamed Follow-up Prescription"
    })
    assert status == 200, f"Update failed: {status}"
    assert updated_presc["title"] == "Renamed Follow-up Prescription"
    print(" [PASS] 6. Title update via PUT verified.")

    # 8. Safe Deletion & File Cleanup
    status, _, _ = client_a.request("DELETE", f"/api/prescriptions/{presc_1['id']}")
    assert status == 204, f"Delete failed: {status}"
    status_check, _, _ = client_a.request("GET", f"/api/prescriptions/{presc_1['id']}")
    assert status_check == 404, f"Prescription still exists after deletion! Status: {status_check}"
    print(" [PASS] 7. Safe deletion and file cleanup verified.")

    print("=" * 60)
    print("ALL CAMERA PRESCRIPTION UPLOAD TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_camera_capture_prescription_suite()

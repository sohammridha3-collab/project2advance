# 📘 HealthBridge AI — Complete User Guide & Project Overview

Welcome to **HealthBridge AI**! This guide explains **what the project is**, **how it works**, and **how to use every single feature** in simple, easy-to-understand language.

---

## 🌟 1. What is HealthBridge AI? (In Simple Words)

When people go to the doctor, they often forget their past medical history, lose paper prescriptions, or struggle to explain their symptoms clearly in a 10-minute appointment.

**HealthBridge AI** is a smart personal healthcare assistant that brings all your health information together in one place:
1. **Predicts Heart Risk**: You type in your basic health numbers (like blood pressure, heart rate, age), and a trained Artificial Intelligence (AI) model tells you your risk level (*Low, Moderate, High, or Critical*).
2. **Stores Prescriptions Safely**: You can take a photo of your prescription with your phone or camera or upload a file. The system automatically reads the doctor's name and medicines.
3. **Screens for Medicine Safety**: Warns you if you are allergic to a medicine or if two medicines conflict with each other.
4. **Builds a Unified Health Timeline**: Puts all your doctor visits, health complaints, prescriptions, and test results into a single chronological timeline.
5. **Prepares You for Doctor Visits**: With one click, it writes a neat **Doctor Briefing** summary that you can share with your doctor using a private link and a 4-digit PIN.

---

## 🚀 2. How to Start and Run the Project

Running HealthBridge AI on your computer is quick and easy.

### Prerequisites
- A Windows computer with **Python 3.10 or newer** installed.
- A modern web browser (Google Chrome, Microsoft Edge, Brave, or Firefox).

---

### Step 1: Start the Backend Server

Open the project folder (`project2advance`) and run:

```bat
start_service.bat
```
*(Or double-click `start_service.bat` in your Windows file manager)*

> **What does this do?**  
> It starts the FastAPI server and Uvicorn on your computer at `http://127.0.0.1:8000`. It also includes an automatic supervisor so the server stays alive reliably.

---

### Step 2: Open the Website in Your Browser

Once the server is running, simply open your browser and go to:

👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (or `http://127.0.0.1:8000/index.html`)

That's it! The backend serves both the application programming interface (API) and the entire website together.

---

### Stopping or Restarting the Server
- To **stop** the server: Double-click or run `stop_backend.bat`
- To **restart** the server: Double-click or run `restart_backend.bat`

---

## 🖥️ 3. How to Use Every Feature (Step-by-Step)

Here is how you use each part of the application:

```
┌─────────────────────────────────────────────────────────────┐
│                      HEALTHBRIDGE AI                        │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│ 1. Account  │ 2. AI Risk  │ 3. Vault    │ 4. Timeline       │
│ Register &  │ Predict     │ Camera &    │ See your complete │
│ Log in      │ Heart Risk  │ Upload Rx   │ medical journey   │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

---

### Feature 1: Create an Account & Log In (`login.html`)
1. Click **"Sign In"** or **"Register"** in the top navigation bar.
2. Fill in:
   - Your Full Name (e.g., *Alex Johnson*)
   - Your Email (e.g., *alex@example.com*)
   - Your Password (at least 6 characters)
3. Click **"Create Account"**.
4. Once registered, log in with your email and password.
5. Your name will now appear in the top-right corner, and all your records will be saved securely to your account.

---

### Feature 2: AI Heart Risk Prediction (`index.html`)
1. On the home page, scroll to the **"Heart Health Assessment"** form.
2. Fill in your numbers:
   - **Age**: (e.g., `45` to `65`)
   - **Gender**: Select Male or Female.
   - **Smoker Status**: Yes or No.
   - **Diabetes History**: Yes or No.
   - **Resting Heart Rate**: (e.g., `72` to `88 bpm`)
   - **Systolic Blood Pressure**: Top blood pressure reading (e.g., `120` to `145 mmHg`)
   - **Oxygen Saturation**: (e.g., `96%` to `99%`)
   - **Chest Pain Severity**: Rate from `0` (none) to `10` (severe).
   - **Body Temperature**: Normal is around `37.0 °C`.
3. Click **"Run AI Risk Analysis"**.
4. **What you will see**:
   - **Risk Category**: Shows whether your risk is **Low**, **Moderate**, **High**, or **Critical**.
   - **Confidence Score**: How confident the AI model is (e.g., `94.5%`).
   - **Probability Breakdown**: A color bar showing exact chances for each risk category.
   - **What to Do**: Recommended health habits (diet, exercise, vital tracking).
   - **What to Avoid**: Dangerous foods, smoking, or excessive stimulants.
   - **Doctor Recommendation**: Tells you what kind of specialist to see (e.g., *Cardiologist* or *Primary Care Doctor*).

---

### Feature 3: Share Recent Health Complaints (`problems.html`)
1. If you are experiencing a symptom (like headaches, fatigue, or shortness of breath), click **"Health Problems"** or use the quick form on the homepage.
2. Enter:
   - **Complaint Title**: (e.g., *"Chest tightness when walking upstairs"*)
   - **Status**: Active or Resolved.
   - **Notes**: Extra details on when it started.
3. Click **"Save Problem"**.
4. The system automatically categorizes your problem (e.g., *Cardiovascular*, *Respiratory*, etc.) and saves it to your history.

---

### Feature 4: Record Known Allergies (`allergies.html`)
1. Click **"Allergies"** in the navigation menu.
2. Enter:
   - **Allergen Name**: (e.g., *"Penicillin"* or *"Aspirin"*)
   - **Reaction**: (e.g., *"Skin rash and breathing difficulty"*)
   - **Severity**: Mild, Moderate, or Severe.
   - **Status**: Suspected or Clinician Confirmed.
3. Click **"Save Allergy"**.
4. **Why this matters**: Whenever a prescription or medicine is entered, the system checks this allergy list to protect you from dangerous reactions.

---

### Feature 5: Prescription Vault & Camera Capture (`prescription.html`)
1. Click **"Prescription Vault"**.
2. You have two convenient ways to add prescriptions:
   - **Method A (Upload File)**: Click **"Upload Document"** and choose a PDF or image from your computer.
   - **Method B (Camera Capture)**: Click **"Take Photo"** to open your laptop or phone camera, snap a picture of your paper prescription, and upload it instantly!
3. **AI Candidate Extraction**: The system reads your document and extracts:
   - Doctor's name
   - Prescription date
   - Medicines prescribed (name, dosage, and frequency)
4. Review the extracted medicines and click **"Save to Vault"**.
5. You can view or download your uploaded prescription files anytime.

---

### Feature 6: Unified Health Timeline (`timeline.html`)
1. Click **"Timeline"** in the top menu.
2. Here you see your **entire medical story in order of date and time**:
   - 🩺 Your AI Risk Assessments
   - ⚠️ Your Symptoms and Complaints
   - 💊 Your Prescriptions and Medicines
   - 🛡️ Your Allergies
3. You can click filter buttons (*"Assessments"*, *"Prescriptions"*, *"Symptoms"*, or *"All"*) to quickly view what you want.

---

### Feature 7: Doctor Visit Briefing & Private Sharing (`briefing.html`)
When you are visiting a doctor, you don't need to carry stacks of paper.

1. Click **"Doctor Briefing"**.
2. Click **"Generate Briefing from Health Records"**.
3. In 2 seconds, the system compiles:
   - Your latest vitals and heart risk score.
   - All medicines you are currently taking.
   - Your active allergies.
   - Key discussion points for your doctor.
4. **Share Securely with Your Doctor**:
   - Click **"Share with Doctor"**.
   - Set a 4-digit security PIN (e.g., `1234`).
   - Choose when the link expires (e.g., `48 hours`).
   - Click **"Generate Secure Link"**.
5. **How the Doctor Views It**:
   - Copy the link and send it to your doctor (via email, WhatsApp, or SMS).
   - When the doctor clicks the link, they enter your 4-digit PIN.
   - They see a clean, professional clinical briefing on their phone or computer—no login or password needed!
6. **Revoke Access Anytime**:
   - If you ever want to cancel access, open your Briefing page and click **"Revoke Access"**. The link immediately stops working.

---

## 🧠 4. How the Project Works (Under the Hood)

Here is a simple look at the technical architecture:

```
┌────────────────────────────────────────────────────────┐
│                   YOUR WEB BROWSER                     │
│         (index.html, timeline.html, style.css)         │
└───────────────────────────┬────────────────────────────┘
                            │ (Calls API via api.js)
                            ▼
┌────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND (main.py)              │
│                  Running on Port 8000                  │
├───────────────────────────┼────────────────────────────┤
│ 1. AI Inference Engine    │ Reads heart_risk_model.pkl │
│ 2. Context Engine         │ Aggregates patient timeline│
│ 3. Security & Auth        │ Verifies JWT tokens & PINs │
└───────────────────────────┬────────────────────────────┘
                            │ (Saves & Reads Data)
                            ▼
┌────────────────────────────────────────────────────────┐
│               SQLITE DATABASE (health_risk.db)         │
│          Running in Write-Ahead Logging (WAL) Mode     │
└────────────────────────────────────────────────────────┘
```

1. **The Machine Learning Model (`heart_risk_model.pkl`)**:
   - A 120MB pre-trained machine learning model created with Scikit-learn.
   - It was trained on cardiovascular clinical data.
   - When you click "Analyze Risk", it runs in milliseconds using your input numbers.
2. **The Database (`health_risk.db`)**:
   - Stores users, health records, problems, prescriptions, and briefings.
   - Uses **Write-Ahead Logging (WAL)** so reading your timeline is lightning fast even while new data is being saved.
3. **The Centralized API Client (`api.js`)**:
   - Manages communication between the web page and the Python backend.
   - Automatically handles network hiccups with smart retries.
   - Distinguishes between session expiration (token timeout) and server status.

---

## 📁 5. Important Files Directory

| File Name | Purpose |
| :--- | :--- |
| `index.html` & `script.js` | Home page & AI Heart Risk Assessment form. |
| `timeline.html` & `timeline.js` | Unified chronological health timeline. |
| `prescription.html` & `prescription.js` | Prescription Vault with camera and file upload. |
| `briefing.html` & `briefing.js` | Doctor visit briefing builder and secure sharing. |
| `share.html` & `share.js` | The private page doctors see after entering the 4-digit PIN. |
| `allergies.html` & `allergies.js` | Allergy tracker and contraindication warnings. |
| `problems.html` & `problems.js` | Health complaints and symptom tracker. |
| `main.py` | FastAPI backend entry point and routes router. |
| `heart_risk_model.pkl` | The trained AI machine learning model. |
| `health_risk.db` | The SQLite database containing all saved records. |
| `start_service.bat` | The Windows batch script to launch the backend reliably. |
| `stop_backend.bat` | Script to stop the backend cleanly. |

---

## 🛠️ 6. Troubleshooting & FAQs

### Q1: The page says "Cannot connect to backend server"?
- Ensure `start_service.bat` is running in a terminal window.
- Check if `http://127.0.0.1:8000/health` opens in your browser. If it says `{"status": "online"}`, the server is running properly.

### Q2: How do I test the camera feature on a computer without a webcam?
- Click the **"Upload Document"** tab in the Prescription Vault and upload any image or PDF file instead.

### Q3: How do I test the Doctor Sharing link?
- Generate the share link and PIN.
- Open an **Incognito / Private Window** in your browser.
- Paste the share link, enter the PIN, and view the doctor's screen.

### Q4: Is my personal medical information safe?
- Yes. The application uses hashed passwords, protected JWT sessions, and private PIN hashes.
- Each user's data is isolated so no user can see another user's health records.

---

*HealthBridge AI — Designed for patient empowerment and seamless doctor-patient continuity.*

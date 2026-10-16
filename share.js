/**
 * Public Clinician Shared Briefing View Logic
 */
(() => {
  "use strict";

  const { briefings } = window.HR_API;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const container = document.getElementById("share-state-container");
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  if (!token) {
    container.innerHTML = `
      <div class="glass" style="text-align:center;padding:3rem 1.5rem;border-radius:16px;max-width:540px;margin:2rem auto">
        <span style="font-size:2.5rem;display:block;margin-bottom:1rem">⚠</span>
        <h2 style="margin:0 0 .5rem">Invalid Consultation Link</h2>
        <p style="color:var(--text-muted);font-size:.9rem">This link does not include a valid clinical access token.</p>
      </div>
    `;
    return;
  }

  function formatDate(dStr) {
    if (!dStr) return "Date unrecorded";
    try {
      return new Date(dStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return String(dStr);
    }
  }

  function renderPinPrompt(errorMessage = "") {
    container.innerHTML = `
      <div class="glass" style="max-width:440px;margin:3rem auto;padding:2rem;border-radius:16px">
        <div style="text-align:center;margin-bottom:1.5rem">
          <span style="font-size:2.2rem;display:block;margin-bottom:.5rem">🔒</span>
          <h2 style="margin:0 0 .3rem;font-size:1.3rem">Security PIN Required</h2>
          <p style="color:var(--text-muted);font-size:.86rem;margin:0">The patient has protected this consultation briefing with an access PIN.</p>
        </div>

        ${errorMessage ? `<div class="form-state-box error" style="margin-bottom:1rem"><span>⚠</span><span>${esc(errorMessage)}</span></div>` : ""}

        <form id="pin-form">
          <div style="margin-bottom:1.2rem">
            <label for="input-pin" style="display:block;font-size:.85rem;font-weight:600;color:var(--text-secondary);margin-bottom:.4rem">Enter Access PIN</label>
            <input type="password" id="input-pin" required placeholder="••••" maxlength="10" style="width:100%;box-sizing:border-box;min-height:44px;padding:0 1rem;border-radius:10px;border:1px solid var(--border-subtle);background:rgba(8,16,34,.7);color:var(--text-main);font-size:1.1rem;text-align:center;letter-spacing:.2em">
          </div>
          <button class="btn p" type="submit" style="width:100%">Unlock Briefing &rarr;</button>
        </form>
      </div>
    `;

    document.getElementById("pin-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const enteredPin = document.getElementById("input-pin").value.trim();
      loadBriefing(enteredPin);
    });
  }

  function renderBriefing(data) {
    container.innerHTML = `
      <div class="glass" style="padding:2.2rem;border-radius:16px;margin-bottom:2rem">
        <!-- Print Header -->
        <div style="border-bottom:1px solid var(--border-subtle);padding-bottom:1.2rem;margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem">
          <div>
            <span style="font-size:.8rem;color:var(--primary);font-weight:700;text-transform:uppercase;letter-spacing:.06em">Clinical Continuity Briefing</span>
            <h1 style="margin:.3rem 0 .4rem;font-size:1.6rem;color:var(--text-main)">${esc(data.title)}</h1>
            <p style="margin:0;font-size:.9rem;color:var(--text-secondary)">
              <strong>Patient:</strong> ${esc(data.patient_name)} &bull; 
              <strong>Recipient:</strong> ${esc(data.recipient_name || "Physician")} &bull; 
              <strong>Expires:</strong> ${formatDate(data.expires_at)}
            </p>
          </div>
          <button onclick="window.print()" class="btn btn-sm" type="button">🖨️ Print / Save as PDF</button>
        </div>

        <!-- Clinical Safety Advisory -->
        <div class="urgent-box" style="margin-bottom:1.8rem;background:rgba(94,224,208,.05);border-color:rgba(94,224,208,.2)">
          <span style="font-size:1.3rem">ℹ</span>
          <p style="margin:0;font-size:.85rem;color:var(--text-secondary);line-height:1.5">
            <strong>Clinical Notice:</strong> This summary was prepared directly from patient records to streamline clinical consultation. AI risk scores and extracted medications are decision-support estimates and do not replace licensed clinical judgment.
          </p>
        </div>

        <!-- 1. Reason for Visit -->
        <div class="briefing-section-box" style="margin-bottom:1.2rem">
          <h3 style="margin:0 0 .5rem"><span>🎯</span> Reason for Consultation</h3>
          <p style="margin:0;font-size:.95rem;color:var(--text-main);line-height:1.5">${esc(data.visit_reason)}</p>
        </div>

        <!-- 2. Symptoms -->
        <div class="briefing-section-box" style="margin-bottom:1.2rem">
          <h3 style="margin:0 0 .5rem"><span>📝</span> Reported Symptoms &amp; Duration</h3>
          <pre style="margin:0;font-family:inherit;font-size:.9rem;color:var(--text-secondary);white-space:pre-wrap;line-height:1.6">${esc(data.symptoms_summary || "No active symptoms specified.")}</pre>
        </div>

        <!-- 3. Objective Vitals & AI Screening -->
        <div class="briefing-section-box" style="margin-bottom:1.2rem">
          <h3 style="margin:0 0 .5rem"><span>🩺</span> Recorded Physiological Vitals</h3>
          <pre style="margin:0;font-family:inherit;font-size:.9rem;color:var(--text-secondary);white-space:pre-wrap;line-height:1.6">${esc(data.vitals_summary || "No vital records available.")}</pre>
        </div>

        <!-- 4. Allergies -->
        <div class="briefing-section-box" style="margin-bottom:1.2rem">
          <h3 style="margin:0 0 .5rem"><span>🛡️</span> Documented Allergies &amp; Sensitivities</h3>
          <pre style="margin:0;font-family:inherit;font-size:.9rem;color:var(--text-secondary);white-space:pre-wrap;line-height:1.6">${esc(data.allergies_summary || "No allergies documented.")}</pre>
        </div>

        <!-- 5. Medications -->
        <div class="briefing-section-box" style="margin-bottom:1.2rem">
          <h3 style="margin:0 0 .5rem"><span>💊</span> Documented Prescription Medications</h3>
          <pre style="margin:0;font-family:inherit;font-size:.9rem;color:var(--text-secondary);white-space:pre-wrap;line-height:1.6">${esc(data.medicines_summary || "No active prescription medications recorded.")}</pre>
        </div>

        <!-- 6. Discussion Questions -->
        <div class="briefing-section-box" style="margin-bottom:1.2rem">
          <h3 style="margin:0 0 .5rem"><span>❓</span> Patient Discussion Questions</h3>
          <pre style="margin:0;font-family:inherit;font-size:.9rem;color:var(--text-secondary);white-space:pre-wrap;line-height:1.6">${esc(data.questions_to_ask || "None specified.")}</pre>
        </div>

        <!-- 7. Notes -->
        ${data.notes ? `
          <div class="briefing-section-box" style="margin-bottom:1.2rem">
            <h3 style="margin:0 0 .5rem"><span>📋</span> Follow-up &amp; Clinical Notes</h3>
            <pre style="margin:0;font-family:inherit;font-size:.9rem;color:var(--text-secondary);white-space:pre-wrap;line-height:1.6">${esc(data.notes)}</pre>
          </div>
        ` : ""}
      </div>
    `;
  }

  async function loadBriefing(pin = "") {
    container.innerHTML = `
      <div style="text-align:center;padding:4rem 1rem">
        <p style="color:var(--text-muted)">Validating secure sharing credentials…</p>
      </div>
    `;

    try {
      const data = await briefings.getShared(token, pin);
      renderBriefing(data);
    } catch (err) {
      if (err.status === 401) {
        renderPinPrompt(pin ? "Incorrect PIN entered. Please try again." : "");
      } else if (err.status === 410) {
        container.innerHTML = `
          <div class="glass" style="text-align:center;padding:3rem 1.5rem;border-radius:16px;max-width:540px;margin:2rem auto">
            <span style="font-size:2.5rem;display:block;margin-bottom:1rem">⏳</span>
            <h2 style="margin:0 0 .5rem">Access Expired or Revoked</h2>
            <p style="color:var(--text-muted);font-size:.9rem;line-height:1.5">
              Access to this clinical briefing is no longer active. The patient has revoked access or the temporary consultation window has expired.
            </p>
          </div>
        `;
      } else {
        container.innerHTML = `
          <div class="glass" style="text-align:center;padding:3rem 1.5rem;border-radius:16px;max-width:540px;margin:2rem auto">
            <span style="font-size:2.5rem;display:block;margin-bottom:1rem">⚠</span>
            <h2 style="margin:0 0 .5rem">Consultation Briefing Unavailable</h2>
            <p style="color:var(--text-muted);font-size:.9rem">${esc(err.message)}</p>
          </div>
        `;
      }
    }
  }

  document.addEventListener("DOMContentLoaded", () => loadBriefing());
})();

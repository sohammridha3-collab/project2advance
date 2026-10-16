/**
 * Logic for Health Prediction History Page
 */
(() => {
  "use strict";

  const { predict, auth } = window.HR_API;
  const { showToast, openAuthModal } = window.HR_UI;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const riskKey = (l) => {
    l = String(l).toLowerCase();
    return ["crit", "high", "mod", "low"].find(k => l.includes(k)) || "info";
  };

  const app = document.getElementById("history-app");

  function formatDate(isoStr) {
    if (!isoStr) return "";
    try {
      const dt = new Date(isoStr);
      return dt.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return isoStr;
    }
  }

  async function loadHistory() {
    if (!auth.isAuthenticated()) {
      app.innerHTML = `
        <div class="glass empty-card">
          <span class="chip-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>
          <h3>Account Access Required</h3>
          <p>Sign in to view your complete cardiovascular assessment history and model evaluations.</p>
          <button id="auth-history-btn" class="btn p" type="button" style="margin-top:1rem">Sign In / Register</button>
        </div>
      `;
      document.getElementById("auth-history-btn").addEventListener("click", () => {
        openAuthModal("login", () => loadHistory());
      });
      return;
    }

    app.innerHTML = `<div class="glass empty-card"><p>Loading health history records from database...</p></div>`;

    try {
      const records = await predict.getHistory();

      if (!records || records.length === 0) {
        app.innerHTML = `
          <div class="glass empty-card">
            <span class="chip-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg></span>
            <h3>No assessments recorded yet</h3>
            <p>Every time you run a health prediction on the Home page, the model's output and vitals are stored here.</p>
            <a href="index.html#analysis" class="btn p" style="margin-top:1rem">Run First Health Assessment</a>
          </div>
        `;
        return;
      }

      app.innerHTML = records.map(item => {
        const k = riskKey(item.predicted_risk);
        const conf = Number(item.confidence) || 0;

        return `
          <div class="glass tilt history-item risk-${k}" id="assessment-card-${item.id}" style="margin-bottom:1.5rem">
            <div class="card-header">
              <div>
                <div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap">
                  <span class="pill">${esc(item.predicted_risk)}</span>
                  <span style="font-size:.9rem;color:var(--text);font-weight:600">${conf.toFixed(1)}% model confidence</span>
                </div>
                <div class="history-meta" style="margin-top:.4rem">
                  <span>📅 Assessment Date: ${formatDate(item.created_at)}</span>
                </div>
              </div>
              <button class="btn btn-sm btn-danger del-asmt-btn" data-id="${item.id}" type="button" title="Delete record">Delete</button>
            </div>

            <div style="margin-top:.8rem">
              <h4 style="margin:0 0 .5rem;font-size:.92rem;color:var(--mute)">Recorded Vital Signs & Parameters:</h4>
              <div class="kv" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
                <div>Heart Rate<b>${esc(item.heart_rate)} bpm</b></div>
                <div>Blood Pressure<b>${esc(item.systolic_blood_pressure)} mmHg</b></div>
                <div>Oxygen Saturation<b>${esc(item.oxygen_saturation)}%</b></div>
                <div>Chest Pain Severity<b>${esc(item.chest_pain_severity)} / 10</b></div>
                <div>Body Temperature<b>${esc(item.body_temperature)} °C</b></div>
                <div>Age / Gender<b>${esc(item.age)} yrs · ${esc(item.gender)}</b></div>
                <div>Smoker Status<b>${esc(item.smoker_status)}</b></div>
                <div>Diabetes History<b>${esc(item.diabetes_history)}</b></div>
              </div>
            </div>
          </div>
        `;
      }).join("");

      // Bind delete handlers
      app.querySelectorAll(".del-asmt-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          if (confirm("Are you sure you want to delete this historical health assessment?")) {
            btn.disabled = true;
            btn.textContent = "Deleting...";
            try {
              await predict.deleteAssessment(id);
              showToast("Assessment record deleted.", "info");
              const card = document.getElementById(`assessment-card-${id}`);
              if (card) {
                card.style.opacity = "0";
                card.style.transform = "scale(0.95)";
                setTimeout(() => loadHistory(), 250);
              }
            } catch (delErr) {
              showToast(`Failed to delete: ${delErr.message}`, "error");
              btn.disabled = false;
              btn.textContent = "Delete";
            }
          }
        });
      });

    } catch (err) {
      app.innerHTML = `
        <div class="glass empty-card">
          <p style="color:#ff9aa9">Failed to load history: ${esc(err.message)}</p>
          <button class="btn" type="button" onclick="location.reload()" style="margin-top:1rem">Try Again</button>
        </div>
      `;
    }
  }

  window.addEventListener("hr:auth_changed", loadHistory);
  document.addEventListener("DOMContentLoaded", loadHistory);
})();

/**
 * Unified Health Timeline Logic for HealthBridge AI
 */
(() => {
  "use strict";

  const { timeline, auth } = window.HR_API;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let allEvents = [];
  let currentFilter = "ALL";

  const container = document.getElementById("timeline-container");
  const filterBtns = document.querySelectorAll(".timeline-filter-btn");

  const countAll = document.getElementById("count-all");
  const countAssessment = document.getElementById("count-assessment");
  const countSymptom = document.getElementById("count-symptom");
  const countPrescription = document.getElementById("count-prescription");
  const countAllergy = document.getElementById("count-allergy");
  const countBriefing = document.getElementById("count-briefing");

  function formatDate(dStr) {
    if (!dStr) return "Recorded date unknown";
    try {
      const d = new Date(dStr);
      return d.toLocaleDateString("en-US", {
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

  function getBadgeClass(type, badge) {
    const b = (badge || "").toLowerCase();
    if (b.includes("high") || b.includes("crit") || b.includes("severe")) return "status-pill error";
    if (b.includes("mod")) return "status-pill warn";
    if (b.includes("low") || b.includes("verified") || b.includes("active")) return "status-pill success";
    return "status-pill info";
  }

  function updateCounts() {
    countAll.textContent = allEvents.length;
    countAssessment.textContent = allEvents.filter(e => e.event_type === "ASSESSMENT").length;
    countSymptom.textContent = allEvents.filter(e => e.event_type === "SYMPTOM").length;
    countPrescription.textContent = allEvents.filter(e => e.event_type === "PRESCRIPTION").length;
    countAllergy.textContent = allEvents.filter(e => e.event_type === "ALLERGY").length;
    countBriefing.textContent = allEvents.filter(e => e.event_type === "BRIEFING").length;
  }

  function renderEvents() {
    const filtered = currentFilter === "ALL"
      ? allEvents
      : allEvents.filter(e => e.event_type === currentFilter);

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="glass" style="text-align:center;padding:3rem 1.5rem;border-radius:16px">
          <span style="font-size:2.8rem;display:block;margin-bottom:1rem">⏳</span>
          <h3 style="margin:0 0 .5rem">No Health Events Found</h3>
          <p style="color:var(--text-muted);max-width:440px;margin:0 auto 1.5rem">
            ${currentFilter === "ALL" 
              ? "Your health continuity timeline will automatically populate as you record risk assessments, symptoms, prescriptions, and allergies." 
              : `No events recorded under the ${currentFilter.toLowerCase()} category yet.`}
          </p>
          <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
            <a href="index.html#analysis" class="btn btn-sm p">+ Run Health Assessment</a>
            <a href="problems.html" class="btn btn-sm">📝 Log Symptom</a>
            <a href="prescription.html" class="btn btn-sm">💊 Upload Prescription</a>
          </div>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="timeline-feed">
        ${filtered.map(evt => {
          const typeClass = `type-${evt.event_type.toLowerCase()}`;
          const badgeClass = getBadgeClass(evt.event_type, evt.badge);

          return `
            <div class="timeline-node ${typeClass}">
              <div class="timeline-card">
                <div class="timeline-card-header">
                  <div>
                    <span class="timeline-date">${formatDate(evt.event_date)}</span>
                    <h3 style="margin:.25rem 0 .4rem;font-size:1.15rem;color:var(--text-main)">${esc(evt.title)}</h3>
                  </div>
                  <div>
                    <span class="${badgeClass}">${esc(evt.badge || evt.event_type)}</span>
                  </div>
                </div>

                <p style="margin:0 0 .8rem;font-size:.9rem;color:var(--text-secondary);line-height:1.5">${esc(evt.description)}</p>

                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.6rem;padding-top:.6rem;border-top:1px solid rgba(255,255,255,.05);font-size:.82rem">
                  <span style="color:var(--text-muted)">Record ID: <strong>#${evt.source_id}</strong></span>
                  <a href="${evt.source_link}" style="color:var(--primary);font-weight:700;text-decoration:none">View Source Record &rarr;</a>
                </div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  // Filter Buttons
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      renderEvents();
    });
  });

  async function loadTimeline() {
    container.innerHTML = `
      <div style="text-align:center;padding:3rem 1rem">
        <p style="color:var(--text-muted)">Loading your chronological health timeline...</p>
      </div>
    `;

    try {
      allEvents = await timeline.list();
      updateCounts();
      renderEvents();
    } catch (err) {
      if (err.isAuth || err.status === 401) {
        container.innerHTML = `
          <div class="glass" style="text-align:center;padding:3rem 1.5rem;border-radius:16px;max-width:520px;margin:2rem auto">
            <span style="font-size:2.6rem;display:block;margin-bottom:1rem">🔒</span>
            <h3 style="margin:0 0 .5rem">Session Expired</h3>
            <p style="color:var(--text-muted);margin:0 0 1.5rem">
              Your session has expired. Please sign in again to access your health continuity timeline.
            </p>
            <button id="timeline-login-btn" class="btn p" type="button">Sign In Again</button>
          </div>
        `;
        const btn = document.getElementById("timeline-login-btn");
        if (btn && window.HR_UI && window.HR_UI.openAuthModal) {
          btn.addEventListener("click", () => window.HR_UI.openAuthModal("login", loadTimeline));
        }
      } else if (err.isNetwork) {
        container.innerHTML = `
          <div class="glass" style="text-align:center;padding:3rem 1.5rem;border-radius:16px;border:1px solid rgba(239,68,68,0.4);max-width:540px;margin:2rem auto">
            <span style="font-size:2.6rem;display:block;margin-bottom:1rem">🔌</span>
            <h3 style="margin:0 0 .5rem;color:#fca5a5">Cannot Connect to Backend</h3>
            <p style="color:var(--text-muted);margin:0 0 1.2rem;font-size:0.92rem;line-height:1.5">
              Could not establish connection to the FastAPI server at <code>${esc(err.apiBase || "http://127.0.0.1:8000")}</code>.
              The backend may be restarting or offline.
            </p>
            <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
              <button id="timeline-retry-btn" class="btn p" type="button">⚡ Retry Connection</button>
              <button id="timeline-help-btn" class="btn" type="button">🛠️ Troubleshooting</button>
            </div>
          </div>
        `;
        const retryBtn = document.getElementById("timeline-retry-btn");
        if (retryBtn) {
          retryBtn.addEventListener("click", () => {
            retryBtn.textContent = "Connecting...";
            retryBtn.disabled = true;
            loadTimeline();
          });
        }
        const helpBtn = document.getElementById("timeline-help-btn");
        if (helpBtn && window.HR_UI && window.HR_UI.openBackendHelpModal) {
          helpBtn.addEventListener("click", window.HR_UI.openBackendHelpModal);
        }
      } else {
        container.innerHTML = `
          <div class="glass" style="text-align:center;padding:3rem 1.5rem;border-radius:16px;border:1px solid rgba(239,68,68,0.3);max-width:520px;margin:2rem auto">
            <span style="font-size:2.4rem;display:block;margin-bottom:.8rem">⚠</span>
            <h3 style="margin:0 0 .5rem">Failed to Load Health Timeline</h3>
            <p style="color:var(--text-muted);margin:0 0 1.2rem;font-size:0.92rem">
              ${esc(err.message)}
            </p>
            <button id="timeline-retry-generic-btn" class="btn p" type="button">⚡ Try Again</button>
          </div>
        `;
        const retryBtn = document.getElementById("timeline-retry-generic-btn");
        if (retryBtn) {
          retryBtn.addEventListener("click", loadTimeline);
        }
      }
    }
  }

  // Auto-healing listeners
  window.addEventListener("hr:backend_online", () => {
    // Automatically re-request timeline as soon as FastAPI backend reconnects
    loadTimeline();
  });

  window.addEventListener("hr:auth_changed", (e) => {
    if (e.detail && e.detail.user) {
      loadTimeline();
    }
  });

  document.addEventListener("DOMContentLoaded", () => {
    if (window.HR_UI && window.HR_UI.ensureAuth) {
      window.HR_UI.ensureAuth("view your health continuity timeline", loadTimeline);
    } else {
      loadTimeline();
    }
  });
})();

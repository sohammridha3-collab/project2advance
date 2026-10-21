(() => {
  "use strict";

  const { esc, riskKey, ico, store, observe } = window.HR;
  const app = document.getElementById("app");

  // Icon SVG helper
  const svgIcon = (name) => {
    switch (name) {
      case "alert":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`;
      case "check":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>`;
      case "ban":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/></svg>`;
      case "doctor":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/></svg>`;
      case "pill":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>`;
      case "shield":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;
      case "history":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>`;
      case "activity":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`;
      case "heart":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>`;
      case "compass":
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>`;
      default:
        return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>`;
    }
  };

  // Activity Illustration Icon SVG helper
  const activityIcon = (cat, name) => {
    const s = `${cat} ${name}`.toLowerCase();
    if (s.includes("cycl") || s.includes("bike")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="5.5" cy="17.5" r="3.5"/><circle cx="18.5" cy="17.5" r="3.5"/><path d="M15 6a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm-3 11.5L9 11l3-5 4 4h4"/><path d="m12 6 3 5-3 6.5"/></svg>`;
    }
    if (s.includes("water") || s.includes("pool") || s.includes("swim") || s.includes("aquatic")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12c1.5-1.5 3.5-1.5 5 0s3.5 1.5 5 0 3.5-1.5 5 0 3.5 1.5 5 0"/><path d="M2 18c1.5-1.5 3.5-1.5 5 0s3.5 1.5 5 0 3.5-1.5 5 0 3.5 1.5 5 0"/><circle cx="12" cy="5" r="2"/></svg>`;
    }
    if (s.includes("walk") || s.includes("aerobic") || s.includes("elliptical")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 4v4l3 3-1.5 1.5-2.5-2.5V14l-4 6-1.5-1 3.5-5.5L8 10H5V8h4.5l2-3.5A2 2 0 1 1 13 4z"/><circle cx="13" cy="3" r="1.5"/></svg>`;
    }
    if (s.includes("resist") || s.includes("strength") || s.includes("circuit") || s.includes("push-up") || s.includes("endurance")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1a2 2 0 0 0-2.83 0l-.88.88a2 2 0 0 1-2.83 0l-4.58-4.58a2 2 0 0 1 0-2.83l.88-.88a2 2 0 0 0 0-2.83l-1-1"/><path d="m3 3 1 1a2 2 0 0 0 2.83 0l.88-.88a2 2 0 0 1 2.83 0l4.58 4.58a2 2 0 0 1 0 2.83l-.88.88a2 2 0 0 0 0 2.83l1 1"/></svg>`;
    }
    if (s.includes("flex") || s.includes("mobil") || s.includes("stretch") || s.includes("yoga") || s.includes("postur") || s.includes("core") || s.includes("spine")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4" r="2"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M9 10h6"/><path d="m6 13 3-3"/><path d="m18 13-3-3"/></svg>`;
    }
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`;
  };

  // Render Loading State
  function renderLoading() {
    app.innerHTML = `
      <div class="glass rec-loading-card reveal">
        <div class="rec-spinner"></div>
        <h3 style="margin:0 0 .5rem">Loading Your Recommendations</h3>
        <p style="color:var(--mute);margin:0">Evaluating your health numbers, recent symptoms, and medicine safety…</p>
      </div>
    `;
    observe(app);
  }

  // Render Error State
  function renderError(message, retryFn) {
    app.innerHTML = `
      <div class="glass rec-empty-box reveal">
        <span class="chip-ico" style="margin:0 auto 1rem;color:var(--crit)">${svgIcon("alert")}</span>
        <h3 style="margin:0 0 .6rem">Unable to Load Recommendations</h3>
        <p style="color:var(--mute);margin:0 0 1.5rem">${esc(message)}</p>
        <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
          <button id="rec-retry-btn" class="btn p" type="button">Retry</button>
          <a class="btn" href="index.html">Return to Home</a>
        </div>
      </div>
    `;
    observe(app);
    const retryBtn = document.getElementById("rec-retry-btn");
    if (retryBtn && retryFn) retryBtn.addEventListener("click", retryFn);
  }

  // Render Empty State
  function renderEmpty() {
    const user = window.HR_API ? window.HR_API.auth.getUser() : null;
    if (user) {
      app.innerHTML = `
        <div class="glass rec-empty-box reveal">
          <span class="chip-ico" style="margin:0 auto 1rem;color:var(--aqua)">${svgIcon("activity")}</span>
          <h3 style="margin:0 0 .6rem">No Health Assessment on File</h3>
          <p style="color:var(--mute);margin:0 0 1.5rem">Welcome, <strong>${esc(user.name || "User")}</strong>! You haven't recorded a health assessment yet. Complete a quick health check to get your personalized exercise plan and guidance.</p>
          <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
            <a class="btn p" href="index.html#analysis">Run Health Assessment Now &rarr;</a>
            <a class="btn" href="index.html">Dashboard Home</a>
          </div>
        </div>
      `;
    } else {
      app.innerHTML = `
        <div class="glass rec-empty-box reveal">
          <span class="chip-ico" style="margin:0 auto 1rem;color:var(--aqua)">${svgIcon("pill")}</span>
          <h3 style="margin:0 0 .6rem">No Health Assessment Found</h3>
          <p style="color:var(--mute);margin:0 0 1.5rem">To see personalized recommendations and your tailored 3-tier exercise plan, please complete a quick health check first.</p>
          <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
            <a class="btn p" href="index.html#analysis">Start Health Check</a>
            <button id="open-login-btn" class="btn" type="button">Sign In to Load Profile</button>
          </div>
        </div>
      `;
      const loginBtn = document.getElementById("open-login-btn");
      if (loginBtn) {
        loginBtn.addEventListener("click", () => {
          if (window.HR_COMMON && window.HR_COMMON.openAuthModal) {
            window.HR_COMMON.openAuthModal("login", () => loadRecommendations());
          }
        });
      }
    }
    observe(app);
  }

  // Main Render Function for Complete Recommendation Response
  function renderRecommendations(data, storedPatient = null) {
    const k = riskKey(data.risk_level);
    const doc = data.doctor_recommendation || {};
    const context = data.patient_context_used || {};
    const meds = data.medicine_information || [];
    const safetyWarnings = data.safety_warnings || [];

    // 1. Emergency Warning Banner
    let emergencyHtml = "";
    if (data.emergency_warning) {
      emergencyHtml = `
        <section class="emergency-banner reveal" role="alert" aria-live="assertive">
          <div class="emergency-head">
            <span class="emergency-badge">${svgIcon("alert")} Immediate Medical Attention Needed</span>
            <span style="color:#ffccd5;font-size:.85rem;font-weight:600">Urgent Safety Alert</span>
          </div>
          <p class="emergency-text">${esc(data.emergency_warning)}</p>
          <div style="margin-top:1rem;display:flex;gap:.8rem;align-items:center;flex-wrap:wrap">
            <span style="font-size:.88rem;color:#ffd8df">Please contact emergency medical services (e.g. 911 / 112) or go to the nearest emergency clinic immediately.</span>
          </div>
        </section>
      `;
    }

    // 2. Patient Context Status Bar
    const hasHistory = (context.recent_problems_count > 0) || (context.previous_prescriptions_count > 0) || (context.active_allergies_count > 0);
    const user = window.HR_API ? window.HR_API.auth.getUser() : null;

    let contextBarHtml = "";
    if (user && hasHistory) {
      contextBarHtml = `
        <div class="context-bar reveal">
          <div style="display:flex;align-items:center;gap:.6rem">
            <span style="color:var(--aqua)">${svgIcon("history")}</span>
            <span style="font-weight:600;color:var(--text)">Your Saved Health Info:</span>
          </div>
          <div class="context-chips-group">
            <span class="context-tag" title="Recent health problems recorded">${context.recent_problems_count} Recent Problem${context.recent_problems_count === 1 ? "" : "s"}</span>
            <span class="context-tag" title="Prescriptions in vault">${context.previous_prescriptions_count} Prescription${context.previous_prescriptions_count === 1 ? "" : "s"}</span>
            <span class="context-tag ${context.active_allergies_count ? "warn" : ""}" title="Documented patient allergies">${context.active_allergies_count} Allerg${context.active_allergies_count === 1 ? "y" : "ies"}</span>
            ${(context.current_medicines_considered && context.current_medicines_considered.length) ? `<span class="context-tag" title="Active medications screened">${context.current_medicines_considered.length} Meds Checked</span>` : ""}
          </div>
        </div>
      `;
    } else if (!user) {
      contextBarHtml = `
        <div class="context-bar reveal">
          <span style="color:var(--mute)">Showing advice based on current numbers. <a href="#" id="rec-signin-link" style="color:var(--aqua);text-decoration:underline">Sign in</a> to save your health history and screen prescriptions.</span>
        </div>
      `;
    }

    // 3. Risk Summary Card
    const probs = data.probabilities || {};
    const probRows = [
      { key: "Low Risk", cls: "fill-low", label: "Low Risk" },
      { key: "Moderate Risk", cls: "fill-mod", label: "Moderate" },
      { key: "High Risk", cls: "fill-high", label: "High Risk" },
      { key: "Critical Risk", cls: "fill-crit", label: "Critical" },
    ].map(p => {
      const val = probs[p.key] !== undefined ? Number(probs[p.key]).toFixed(1) : "0.0";
      return `
        <div class="prob-row">
          <span style="color:var(--mute)">${p.label}</span>
          <div class="prob-bar-track">
            <div class="prob-bar-fill ${p.cls}" style="width:${Math.max(Number(val), 2)}%"></div>
          </div>
          <span style="text-align:right;font-weight:600;color:var(--text)">${val}%</span>
        </div>
      `;
    }).join("");

    const patientVitalsHtml = storedPatient ? `
      <div style="display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1.1rem;padding-top:1rem;border-top:1px solid var(--edge)">
        <span class="pill-chip">Age: ${esc(storedPatient.age)}</span>
        <span class="pill-chip">Gender: ${esc(storedPatient.gender)}</span>
        <span class="pill-chip">Blood Pressure: ${esc(storedPatient.systolic_blood_pressure)} mmHg</span>
        <span class="pill-chip">Heart Rate: ${esc(storedPatient.heart_rate)} bpm</span>
        <span class="pill-chip">Oxygen: ${esc(storedPatient.oxygen_saturation)}%</span>
        <span class="pill-chip">Chest Pain: ${esc(storedPatient.chest_pain_severity)}/10</span>
        <span class="pill-chip">Smoker: ${esc(storedPatient.smoker_status)}</span>
        <span class="pill-chip">Diabetes: ${esc(storedPatient.diabetes_history)}</span>
      </div>
    ` : "";

    const riskSummaryHtml = `
      <section class="glass risk-summary-card reveal" style="--i:1">
        <div class="card-header">
          <div>
            <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem;flex-wrap:wrap">
              <span class="badge-verified-db">AI Health Model</span>
              <span class="badge-cat">Educational Support</span>
            </div>
            <h2 style="margin:0;font-size:1.35rem">Your Health Risk Result</h2>
          </div>
          <span class="pill risk-${k}" style="font-size:.9rem;padding:.35rem .9rem">${esc(data.risk_level)}</span>
        </div>
        <div class="risk-summary-grid">
          <div class="risk-metric-box">
            <span style="font-size:.85rem;color:var(--mute);text-transform:uppercase;letter-spacing:.05em">Model Confidence</span>
            <div class="risk-metric-val" style="color:var(--text)">${Number(data.confidence).toFixed(1)}<span style="font-size:1.2rem;color:var(--mute)">%</span></div>
            <p style="font-size:.88rem;color:var(--mute);margin:.3rem 0 0">
              Calculated by our machine learning model from your health numbers.
            </p>
          </div>
          <div class="prob-dist-wrap">
            <span style="font-size:.85rem;font-weight:600;color:var(--text);margin-bottom:.2rem">Predicted Risk Chances</span>
            ${probRows}
          </div>
        </div>
        ${patientVitalsHtml}
      </section>
    `;

    // 4. Doctor Recommendation Card
    const urgencyClass = (doc.urgency || "").split(" ")[0] || "Routine";
    const discussionListHtml = (doc.discussion_points && doc.discussion_points.length) ? `
      <div style="margin-top:1.1rem;padding-top:1rem;border-top:1px solid var(--edge)">
        <div class="doc-points-title">Questions to discuss with your doctor:</div>
        <ul class="doc-points-list">
          ${doc.discussion_points.map(pt => `<li>${svgIcon("check")}<span>${esc(pt)}</span></li>`).join("")}
        </ul>
      </div>
    ` : "";

    const doctorRecHtml = `
      <section class="glass doc-rec-card reveal" style="--i:2">
        <div class="doc-header">
          <div class="doc-title-group">
            <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.2rem;flex-wrap:wrap">
              <span class="badge-ai-guidance">Doctor Guidance</span>
              <span style="font-size:.78rem;color:var(--mute)">(Educational suggestion, not a diagnosis)</span>
            </div>
            <h2 class="doc-specialist-title">${svgIcon("doctor")} ${esc(doc.recommended_specialist || "Primary Care Doctor")}</h2>
          </div>
          <span class="urgency-pill ${urgencyClass}">${esc(doc.urgency || "Timely Consultation")}</span>
        </div>
        <p class="doc-reason">${esc(doc.reason || "We suggest speaking with a doctor to review your results.")}</p>
        ${discussionListHtml}
      </section>
    `;

    // 5. What You Should Do & What You Should Avoid Cards
    const doItems = (data.what_to_do || []).map(item => `
      <li>${svgIcon("check")}<span>${esc(item)}</span></li>
    `).join("");

    const avoidItems = (data.what_not_to_do || []).map(item => `
      <li>${svgIcon("ban")}<span>${esc(item)}</span></li>
    `).join("");

    const guidanceHtml = `
      <section class="guidance-grid">
        <div class="glass guidance-card reveal" style="--i:3">
          <div class="guidance-head guidance-do">
            <span class="chip-ico" style="margin:0;color:var(--low)">${svgIcon("check")}</span>
            <div>
              <span class="badge-ai-guidance" style="font-size:.7rem;margin-bottom:.2rem">Healthy Habits</span>
              <h2 style="margin:0">What You Should Do</h2>
            </div>
          </div>
          <ul class="guidance-list guidance-do">
            ${doItems || `<li><span>Eat a balanced diet, stay hydrated, and follow up with your doctor.</span></li>`}
          </ul>
        </div>
        <div class="glass guidance-card reveal" style="--i:4">
          <div class="guidance-head guidance-avoid">
            <span class="chip-ico" style="margin:0;color:var(--crit)">${svgIcon("ban")}</span>
            <div>
              <span class="badge-ai-guidance" style="font-size:.7rem;margin-bottom:.2rem">Safety Precautions</span>
              <h2 style="margin:0">What You Should Avoid</h2>
            </div>
          </div>
          <ul class="guidance-list guidance-avoid">
            ${avoidItems || `<li><span>Do not change medicines on your own or ignore sudden chest discomfort.</span></li>`}
          </ul>
        </div>
      </section>
    `;

    // 5b. 3-Tier Exercise Recommendation System
    let exerciseSectionHtml = "";
    let buildPlanContentHtml = null;

    if (data.exercise_plan) {
      const ep = data.exercise_plan;
      const safety = ep.safety_status || {};
      const statusLevel = safety.status_level || "Cleared";
      const isCleared = safety.is_exercise_cleared !== false && statusLevel !== "Contraindicated_Urgent";

      // Determine initial active plan
      let activePlanId = (ep.recommended_plan_id && ep.recommended_plan_id !== "restricted") ? ep.recommended_plan_id : "low";

      // 1. Safety Alert Header
      let safetyAlertHtml = "";
      if (!isCleared) {
        const triggersHtml = (safety.trigger_factors || []).map(t =>
          `<span class="exercise-trigger-tag">${svgIcon("alert")} ${esc(t)}</span>`
        ).join("");
        safetyAlertHtml = `
          <div class="exercise-alert exercise-alert-danger reveal">
            <div class="exercise-alert-header">
              ${svgIcon("alert")} <span>${esc(safety.headline || "Workouts Paused — Medical Advice Needed")}</span>
            </div>
            <p class="exercise-alert-text">${esc(safety.safety_message)}</p>
            ${triggersHtml ? `<div class="exercise-triggers-wrap">${triggersHtml}</div>` : ""}
          </div>
        `;
      } else if (statusLevel === "Cautionary_Supervised") {
        const triggersHtml = (safety.trigger_factors || []).map(t =>
          `<span class="exercise-trigger-tag caution">${svgIcon("alert")} ${esc(t)}</span>`
        ).join("");
        safetyAlertHtml = `
          <div class="exercise-alert exercise-alert-caution reveal">
            <div class="exercise-alert-header">
              ${svgIcon("alert")} <span>${esc(safety.headline || "Light & Gentle Activity Recommended")}</span>
            </div>
            <p class="exercise-alert-text">${esc(safety.safety_message)}</p>
            ${triggersHtml ? `<div class="exercise-triggers-wrap">${triggersHtml}</div>` : ""}
          </div>
        `;
      } else {
        safetyAlertHtml = `
          <div class="exercise-alert exercise-alert-cleared reveal">
            <div class="exercise-alert-header">
              ${svgIcon("check")} <span>${esc(safety.headline || "Ready to Exercise — Choose Your Plan")}</span>
            </div>
            <p class="exercise-alert-text">${esc(safety.safety_message)}</p>
          </div>
        `;
      }

      // 2. Risk Influence Explanation Card
      const influenceCardHtml = `
        <div class="exercise-influence-card reveal">
          <div class="exercise-influence-header">
            <span class="exercise-band-badge">${svgIcon("compass")} Recommended: ${esc(ep.recommended_plan_title || "Low Exercise Plan")}</span>
            <span style="font-size:.78rem;color:var(--mute)">Pace Baseline: <strong>${esc(ep.activity_level_assumed || "Steady Baseline")}</strong></span>
          </div>
          <p class="exercise-influence-body">${esc(ep.risk_influence_explanation)}</p>
        </div>
      `;

      // 3. Tab Definitions (3 Plan Categories)
      const tabDefs = [
        { id: "low", icon: "🚶", title: "Low Exercise", sub: "Gentle daily moves • No dumbbells" },
        { id: "medium", icon: "🏃", title: "Medium Exercise", sub: "Brisk walking • Chair squats • Wall push-ups" },
        { id: "advanced", icon: "⚡", title: "Fit & Advanced", sub: "Challenging bodyweight • Strength • Cardio" }
      ];

      const tabsHtml = `
        <div class="exercise-plan-tabs" role="tablist" aria-label="Exercise Plan Categories">
          ${tabDefs.map(t => {
            const isRec = (t.id === ep.recommended_plan_id);
            const isActive = (t.id === activePlanId);
            return `
              <button type="button" 
                      class="exercise-plan-tab ${isActive ? "active" : ""}" 
                      data-plan-id="${t.id}"
                      role="tab"
                      aria-selected="${isActive ? "true" : "false"}"
                      aria-controls="exercise-plan-content">
                ${isRec ? `<span class="plan-tab-badge">⭐ Recommended for You</span>` : ""}
                <div class="exercise-plan-tab-title">
                  <span>${t.icon}</span> <span>${t.title}</span>
                </div>
                <div class="exercise-plan-tab-sub">${t.sub}</div>
              </button>
            `;
          }).join("")}
        </div>
      `;

      // 4. Function to Build Selected Plan's Content
      buildPlanContentHtml = (selectedPlanId) => {
        const plans = ep.plans || {};
        const plan = plans[selectedPlanId] || {
          id: selectedPlanId,
          title: selectedPlanId === "advanced" ? "Fit & Advanced Plan" : selectedPlanId === "medium" ? "Medium Exercise Plan" : "Low Exercise Plan",
          tagline: "Custom activity guidance",
          target_audience: "All users",
          why_recommended: ep.recommended_reason || "Selected workout plan.",
          safety_advisory: null,
          exercises: ep.exercises || []
        };

        const isRec = (selectedPlanId === ep.recommended_plan_id);

        const badgeHtml = isRec ? `
          <span class="plan-tab-badge">⭐ Recommended for You</span>
        ` : "";

        const advisoryHtml = plan.safety_advisory ? `
          <div class="exercise-plan-advisory">
            <span style="font-size:1.15rem;flex-shrink:0">⚠️</span>
            <div>
              <strong>Safety Note:</strong> ${esc(plan.safety_advisory)}
            </div>
          </div>
        ` : "";

        const whyHtml = (isRec && plan.why_recommended) ? `
          <div class="exercise-plan-banner-why">
            <span style="color:var(--aqua);font-size:1.15rem;flex-shrink:0">💡</span>
            <div>
              <strong>Why this plan is recommended for you:</strong> ${esc(plan.why_recommended)}
            </div>
          </div>
        ` : (plan.why_recommended ? `
          <div class="exercise-plan-banner-why">
            <span style="color:var(--aqua);font-size:1.15rem;flex-shrink:0">ℹ️</span>
            <div>
              <strong>About this plan:</strong> ${esc(plan.why_recommended)}
            </div>
          </div>
        ` : "");

        const exercisesList = plan.exercises || [];

        const cardsHtml = exercisesList.map((ex, idx) => `
          <div class="glass exercise-card reveal" style="--i:${idx + 4}">
            <div class="exercise-card-media">
              <img src="${esc(ex.image_url || 'assets/exercises/easy_walking.svg')}" 
                   alt="${esc(ex.image_alt || ex.name)}" 
                   class="exercise-card-img" 
                   loading="lazy" 
                   onerror="this.onerror=null; this.src='assets/exercises/easy_walking.svg';" />
            </div>

            <div class="exercise-card-header">
              <div>
                <span class="exercise-category-chip">${esc(ex.category)}</span>
                <h3 class="exercise-name">${esc(ex.name)}</h3>
              </div>
              <span class="exercise-intensity-badge">${esc(ex.intensity)}</span>
            </div>

            <div class="exercise-reason-box">
              <strong>Why it helps:</strong> ${esc(ex.reason)}
            </div>

            <div class="exercise-instructions-card">
              <strong style="color:var(--aqua);display:block;margin-bottom:0.2rem">How to do it:</strong>
              ${esc(ex.instructions)}
            </div>

            <div class="exercise-metrics-grid">
              <div class="exercise-metric-cell">
                <span class="exercise-metric-cell-lbl">Sets & Reps</span>
                <span class="exercise-metric-cell-val">${esc(ex.sets || "1 set")}</span>
              </div>
              <div class="exercise-metric-cell">
                <span class="exercise-metric-cell-lbl">Rest Time</span>
                <span class="exercise-metric-cell-val">${esc(ex.rest || "Rest as needed")}</span>
              </div>
              <div class="exercise-metric-cell">
                <span class="exercise-metric-cell-lbl">Duration</span>
                <span class="exercise-metric-cell-val">${esc(ex.duration || "15 mins")}</span>
              </div>
              <div class="exercise-metric-cell">
                <span class="exercise-metric-cell-lbl">Equipment</span>
                <span class="exercise-metric-cell-val">${esc(ex.equipment || "None")}</span>
              </div>
            </div>

            <div class="exercise-safety-tip-box">
              <span style="font-size:1rem;flex-shrink:0">💡</span>
              <div>
                <strong style="color:#6ee7b7">Safety Tip:</strong> ${esc(ex.safety_tip || "Stop if you feel any soreness or discomfort.")}
              </div>
            </div>

            <div class="exercise-precaution-callout">
              <strong style="color:#fde68a">Caution:</strong> ${esc(ex.precautions)}
            </div>
          </div>
        `).join("");

        return `
          <div class="exercise-plan-banner reveal">
            <div class="exercise-plan-banner-top">
              <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap">
                <h3 class="exercise-plan-banner-title">${esc(plan.title)}</h3>
                ${badgeHtml}
              </div>
              <span style="font-size:.8rem;color:var(--mute)">Target: <strong>${esc(plan.target_audience || "General")}</strong></span>
            </div>
            <p class="exercise-plan-banner-tagline">${esc(plan.tagline || "")}</p>
            ${whyHtml}
            ${advisoryHtml}
          </div>

          <div class="exercise-cards-grid">
            ${cardsHtml || `<div class="glass" style="padding:1.5rem;grid-column:1/-1;text-align:center;color:var(--mute)">No exercises available in this plan.</div>`}
          </div>
        `;
      };

      // 5. Contraindicated Emergency Box
      let planDisplayHtml = "";
      if (!isCleared) {
        planDisplayHtml = `
          <div class="glass exercise-suppressed-box reveal">
            <div class="exercise-suppressed-title">
              <span class="chip-ico" style="margin:0;color:var(--crit)">${svgIcon("ban")}</span>
              <h3 style="margin:0;color:#fca5a5;font-size:1.15rem">Workouts Paused for Your Safety</h3>
            </div>
            <p style="margin:.6rem 0 0;font-size:.92rem;color:#fecaca;line-height:1.6">
              Because of warning signs (such as chest discomfort, low oxygen, or fainting), routine workouts are temporarily on hold. Exercising right now could be dangerous for your heart. Please rest and speak with a doctor before starting any physical exercise.
            </p>
          </div>
        `;
      } else {
        planDisplayHtml = `
          ${tabsHtml}
          <div id="exercise-plan-content">
            ${buildPlanContentHtml(activePlanId)}
          </div>
        `;
      }

      // 6. Stop Exercising Card
      const stopCriteriaHtml = `
        <div class="exercise-stop-card reveal">
          <div class="exercise-stop-header">
            ${svgIcon("alert")} <span>When to Stop Exercising Right Away</span>
          </div>
          <p style="margin:0 0 .5rem;font-size:.88rem;color:#fecaca">
            Never push through pain. Stop exercising immediately and call emergency services (e.g. 911 / 112) or your doctor if you feel:
          </p>
          <ul class="exercise-stop-list">
            <li>${svgIcon("alert")} Sudden chest pain, tightness, or pressure</li>
            <li>${svgIcon("alert")} Pain spreading to your left arm, neck, jaw, or back</li>
            <li>${svgIcon("alert")} Severe trouble breathing or gasping for air</li>
            <li>${svgIcon("alert")} Feeling dizzy, faint, or breaking into a cold sweat</li>
            <li>${svgIcon("alert")} Very fast, fluttering, or skipping heartbeats</li>
            <li>${svgIcon("alert")} Sharp pain or sudden swelling in your joints</li>
          </ul>
        </div>
      `;

      // 7. General Guidelines
      const guidelinesHtml = (ep.general_guidelines && ep.general_guidelines.length) ? `
        <div class="exercise-guidelines-box reveal">
          <h4 style="margin:0;font-size:1rem;color:var(--text);display:flex;align-items:center;gap:.5rem">
            ${svgIcon("shield")} <span>General Workout Tips</span>
          </h4>
          <ul class="exercise-guidelines-list">
            ${ep.general_guidelines.map(g => `<li>${svgIcon("check")}<span>${esc(g)}</span></li>`).join("")}
          </ul>
        </div>
      ` : "";

      exerciseSectionHtml = `
        <section class="exercise-section" id="exercise-section">
          <div class="med-section-head" style="margin-bottom:1rem">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap">
              <div>
                <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap">
                  <span class="badge-ai-guidance">${svgIcon("activity")} Physical Activity</span>
                  <span class="badge-verified-db">3 Exercise Categories</span>
                </div>
                <h2 style="margin:.35rem 0 0;font-size:1.35rem">Exercise Recommendations</h2>
                <p style="color:var(--mute);margin:.3rem 0 0;font-size:.9rem">
                  Choose a workout that fits your pace. Based on your health check and symptoms, we've highlighted the recommended starting plan for you.
                </p>
              </div>
              <button id="btn-refresh-exercise-plan" class="btn-refresh-plan" type="button" title="Refresh your exercise recommendations">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>Refresh Plan</span>
              </button>
            </div>
          </div>

          ${safetyAlertHtml}
          ${influenceCardHtml}
          
          ${planDisplayHtml}

          ${stopCriteriaHtml}

          ${guidelinesHtml}

          <div style="font-size:.8rem;color:var(--mute);line-height:1.5;padding:.5rem 0">
            <em>${esc(ep.clinical_disclaimer || "Notice: Always check with your doctor before starting any new exercise routine.")}</em>
          </div>
        </section>
      `;
    }

    // 6. Medicine Information & Safety Screening Layer
    let safetyAlertBoxHtml = "";
    if (safetyWarnings.length > 0) {
      safetyAlertBoxHtml = `
        <div class="glass reveal" style="padding:1.1rem 1.4rem;border-color:rgba(255,93,120,.4);background:rgba(255,93,120,.08);margin-bottom:1rem">
          <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:.5rem;color:#ffccd5;font-weight:700">
            ${svgIcon("alert")} Medicine Safety Warnings (${safetyWarnings.length} Detected)
          </div>
          <ul style="margin:0;padding-left:1.2rem;color:#ffe4e8;font-size:.88rem;line-height:1.5">
            ${safetyWarnings.map(w => `<li>${esc(w)}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    const medsHtml = meds.map((med, idx) => {
      const isConflict = med.potential_conflict;
      const statusBadge = isConflict
        ? `<span class="med-status-badge med-status-conflict">${svgIcon("alert")} Potential Conflict Flagged</span>`
        : `<span class="med-status-badge med-status-review">${svgIcon("shield")} Database Screened</span>`;

      const alertHtml = isConflict && med.warning
        ? `<div class="med-warning-alert"><strong>Safety Alert:</strong> ${esc(med.warning)}<br><span style="font-size:.8rem;color:#ffccd5;display:inline-block;margin-top:.3rem">Please consult your doctor before using this medicine.</span></div>`
        : "";

      return `
        <div class="glass med-card ${isConflict ? "conflict" : ""} reveal" style="--i:${idx + 5}">
          <div class="med-card-top">
            <div>
              <div style="display:flex;align-items:center;gap:.4rem;margin-bottom:.25rem;flex-wrap:wrap">
                <span class="badge-verified-db">Verified Info</span>
                ${med.prescription_required ? `<span class="pill-chip" style="font-size:.72rem">Prescription Only (Rx)</span>` : `<span class="pill-chip" style="font-size:.72rem">Over the Counter (OTC)</span>`}
              </div>
              <h3 class="med-name-title">${esc(med.medicine_name)}</h3>
              <div class="med-generic">${esc(med.generic_name || "Generic")} &bull; ${esc(med.category || "Medication")}</div>
            </div>
            ${statusBadge}
          </div>

          ${alertHtml}

          <div class="med-detail-row">
            <span class="med-detail-lbl">Why discuss this medicine</span>
            <span class="med-detail-val">${esc(med.reason || "Candidate therapy to discuss with your doctor.")}</span>
          </div>

          <div class="med-detail-row">
            <span class="med-detail-lbl">Common uses</span>
            <span class="med-detail-val">${esc(med.common_uses || "Cardiovascular support")}</span>
          </div>

          ${med.contraindications ? `
            <div class="med-detail-row">
              <span class="med-detail-lbl">Do not use if</span>
              <span class="med-detail-val" style="color:#fcd0d7">${esc(med.contraindications)}</span>
            </div>
          ` : ""}

          ${med.warnings ? `
            <div class="med-detail-row">
              <span class="med-detail-lbl">Precautions</span>
              <span class="med-detail-val" style="color:var(--mute)">${esc(med.warnings)}</span>
            </div>
          ` : ""}

          <div class="med-screening-note">
            ⚠️ <strong>Safety Check:</strong> AI does NOT prescribe medicine. Always consult your prescribing physician.
          </div>
        </div>
      `;
    }).join("");

    const medicineSectionHtml = `
      <section style="display:flex;flex-direction:column;gap:1rem;margin-top:1rem">
        <div class="med-section-head">
          <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap">
            <span class="badge-verified-db">Medicine Database</span>
            <span class="badge-ai-guidance">Drug Safety Check</span>
          </div>
          <h2 style="margin:0;font-size:1.35rem">Medicine Information & Safety Check</h2>
          <p style="color:var(--mute);margin:0;font-size:.9rem">
            Candidate medicines checked against your health profile, allergies, and prescription vault.
          </p>
        </div>

        <div class="med-disclaimer-box">
          ${svgIcon("shield")}
          <div>
            <strong>Important Safety Notice:</strong> AI does NOT prescribe medication. The information above is for educational reference and doctor consultation only. Never start, stop, or change medication doses without explicit instruction from your licensed doctor.
          </div>
        </div>

        ${safetyAlertBoxHtml}

        <div class="meds-grid">
          ${medsHtml || `<div class="glass" style="padding:1.5rem;grid-column:1/-1;text-align:center;color:var(--mute)">No candidate medicines found for your current profile.</div>`}
        </div>
      </section>
    `;

    // 7. Assemble Full Page
    const navPillsHtml = `
      <nav class="rec-section-nav noprint reveal" aria-label="Guidance Sections">
        <a href="#risk-summary-section" class="rec-nav-pill">📊 Risk Summary</a>
        <a href="#doctor-rec-section" class="rec-nav-pill">🩺 Doctor Advice</a>
        <a href="#guidance-section" class="rec-nav-pill">🛡️ Daily Guidance</a>
        <a href="#exercise-section" class="rec-nav-pill active-pill">🏃 Exercise Plans</a>
        <a href="#medicine-section" class="rec-nav-pill">💊 Medicine Safety</a>
      </nav>
    `;

    app.innerHTML = `
      <div class="rec-page-wrap">
        ${emergencyHtml}
        ${contextBarHtml}
        ${navPillsHtml}
        <div id="risk-summary-section">${riskSummaryHtml}</div>
        <div id="doctor-rec-section">${doctorRecHtml}</div>
        <div id="guidance-section">${guidanceHtml}</div>
        ${exerciseSectionHtml}
        <div id="medicine-section">${medicineSectionHtml}</div>

        <div class="glass" style="padding:1rem 1.4rem;border-radius:12px;font-size:.84rem;color:var(--mute);line-height:1.55;display:flex;align-items:center;gap:.7rem;border-color:rgba(94,224,208,.2);margin-top:.8rem">
          <span style="color:var(--aqua);font-size:1.2rem;flex-shrink:0">🛡️</span>
          <div>
            <strong style="color:var(--text)">HealthBridge AI Guidance:</strong> This platform organizes your personal health records and provides educational context. It does not provide medical diagnoses, treatment plans, or autonomous prescriptions. Always consult a licensed doctor for personal medical advice.
          </div>
        </div>

        <div class="pager noprint" style="margin-top:1.5rem;flex-wrap:wrap;gap:.6rem">
          <a class="btn" href="result.html">Back to Result</a>
          <a class="btn" href="timeline.html">Health Timeline</a>
          <a class="btn" href="prescription.html">Prescription Vault</a>
          <a class="btn p" href="briefing.html" style="background:linear-gradient(135deg,rgba(0,212,170,.25),rgba(14,165,233,.25));border:1px solid var(--aqua)">📋 Doctor Briefing</a>
        </div>
      </div>
    `;

    observe(app);

    // Wire up tab switching event listeners
    const planTabButtons = app.querySelectorAll(".exercise-plan-tab");
    const planContentContainer = document.getElementById("exercise-plan-content");
    if (planTabButtons.length && planContentContainer && buildPlanContentHtml) {
      planTabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
          const targetPlanId = btn.getAttribute("data-plan-id");
          if (!targetPlanId) return;

          planTabButtons.forEach(b => {
            b.classList.remove("active");
            b.setAttribute("aria-selected", "false");
          });
          btn.classList.add("active");
          btn.setAttribute("aria-selected", "true");

          planContentContainer.innerHTML = buildPlanContentHtml(targetPlanId);
          observe(planContentContainer);
        });
      });
    }

    const signinLink = document.getElementById("rec-signin-link");
    if (signinLink) {
      signinLink.addEventListener("click", (e) => {
        e.preventDefault();
        if (window.HR_COMMON && window.HR_COMMON.openAuthModal) {
          window.HR_COMMON.openAuthModal("login", () => loadRecommendations());
        }
      });
    }

    const refreshPlanBtn = document.getElementById("btn-refresh-exercise-plan");
    if (refreshPlanBtn) {
      refreshPlanBtn.addEventListener("click", async () => {
        refreshPlanBtn.classList.add("spinning");
        try {
          await loadRecommendations();
        } finally {
          const btn = document.getElementById("btn-refresh-exercise-plan");
          if (btn) btn.classList.remove("spinning");
        }
      });
    }
  }

  // Orchestrator: Load Recommendations from Real Backend API
  async function loadRecommendations() {
    renderLoading();

    const storedData = store.get() || {};
    const storedPatient = storedData.patient || null;
    const user = window.HR_API ? window.HR_API.auth.getUser() : null;

    // Strategy 1: If user is authenticated, call GET /api/recommendations
    if (user && window.HR_API) {
      try {
        const recResult = await window.HR_API.recommendations.get();
        if (recResult && recResult.risk_level) {
          renderRecommendations(recResult, storedPatient);
          return;
        }
      } catch (err) {
        console.warn("GET /api/recommendations failed, attempting fallback:", err);
        // If 404 or missing assessment, fall through to input endpoint if patient exists
      }
    }

    // Strategy 2: If we have stored patient inputs from recent analysis, call POST /api/recommendations
    if (storedPatient && window.HR_API) {
      try {
        const riskLevel = storedData.result ? storedData.result.risk_level : "";
        const recResult = await window.HR_API.recommendations.getFromInput(storedPatient, riskLevel);
        if (recResult && recResult.risk_level) {
          renderRecommendations(recResult, storedPatient);
          return;
        }
      } catch (err) {
        console.error("POST /api/recommendations failed:", err);
        renderError(`Could not generate clinical recommendations: ${err.message}`, () => loadRecommendations());
        return;
      }
    }

    // Strategy 3: Check if result exists in store with pre-generated recommendations
    if (storedData.result && storedData.result.recommendations) {
      const legacy = storedData.result.recommendations;
      renderRecommendations({
        risk_level: storedData.result.risk_level || "Moderate Risk",
        confidence: storedData.result.confidence || 75.0,
        probabilities: storedData.result.probabilities || {},
        what_to_do: legacy.what_to_do || [],
        what_not_to_do: legacy.what_not_to_do || legacy.what_to_avoid || [],
        doctor_recommendation: {
          recommended_specialist: "Primary Care Physician",
          urgency: "Timely Consultation",
          reason: legacy.doctor || "Consider discussing this with a physician.",
          discussion_points: []
        },
        medicine_information: [],
        safety_warnings: [],
        emergency_warning: legacy.emergency_warning || null,
        exercise_plan: storedData.result.exercise_plan || legacy.exercise_plan || null
      }, storedPatient);
      return;
    }

    // Strategy 4: If neither authenticated profile nor patient input exists, render empty state
    renderEmpty();
  }

  // Listen for login/logout changes to automatically reload recommendations
  window.addEventListener("hr:auth_changed", () => {
    loadRecommendations();
  });

  // Initial load
  loadRecommendations();
})();

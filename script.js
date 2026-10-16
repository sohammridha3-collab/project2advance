/* Shared: config, storage, 3D tilt, reveal, counters, nav, transitions, and the home-page form -> POST /predict */
(() => {
  "use strict";

  const CONFIG = {
    API_URL: (typeof window !== "undefined" && window.location && window.location.origin && window.location.origin.includes(":8000"))
      ? window.location.origin
      : "http://127.0.0.1:8000",
    STORAGE_KEY: "hr_analysis_v1",
    // Must match the category values your model was trained on.
    OPTIONS: {
      gender: ["Male", "Female"],
      smoker_status: ["No", "Yes"],
      diabetes_history: ["No", "Yes"],
    },
  };

  document.documentElement.classList.add("js");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canTilt = !reduce && matchMedia("(hover: hover) and (pointer: fine)").matches;

  const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const riskKey = l => { l = String(l).toLowerCase(); return ["crit", "high", "mod", "low"].find(k => l.includes(k)) || "info"; };

  const I = {
    check: '<path d="M20 6 9 17l-5-5"/>',
    ban: '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
    alert: '<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z"/><path d="M12 9v4M12 17h.01"/>',
    doctor: '<path d="M12 5v14M5 12h14"/><rect x="3" y="3" width="18" height="18" rx="5"/>',
    pulse: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.4 8.3 8 9 4.6-.7 8-4 8-9V6z"/>',
    spark: '<path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
    leaf: '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z"/><path d="M2 21c0-3 1.9-5.4 5.1-6.5C9.4 13.8 12 13 12 13"/>',
    run: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    heart: '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7Z"/>',
  };
  const ico = name => `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${I[name]}</svg>`;

  const store = {
    get() { try { return JSON.parse(sessionStorage.getItem(CONFIG.STORAGE_KEY)); } catch { return null; } },
    set(v) { try { sessionStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(v)); } catch { /* storage unavailable */ } },
  };

  /* ---- scroll reveal ---- */
  let io;
  function observe(root = document) {
    const els = [...root.querySelectorAll(".reveal:not(.in)")];
    if (reduce || !("IntersectionObserver" in window)) { els.forEach(e => e.classList.remove("reveal")); return; }
    io = io || new IntersectionObserver(entries => entries.forEach(en => {
      if (!en.isIntersecting) return;
      const el = en.target; io.unobserve(el); el.classList.add("in");
      setTimeout(() => el.classList.remove("reveal", "in"), 1000);   // hand transforms back to the tilt effect
    }), { threshold: 0.12 });
    els.forEach(e => io.observe(e));
  }

  /* ---- animated counters: markup already holds the final value ---- */
  function countUp(el) {
    const to = parseFloat(el.dataset.count) || 0, d = +el.dataset.decimals || 0, suf = el.dataset.suffix || "";
    const fmt = v => v.toFixed(d) + suf;
    if (reduce) { el.textContent = fmt(to); return; }
    const t0 = performance.now(), dur = 700;
    (function step(t) {
      const p = Math.min((t - t0) / dur, 1);
      el.textContent = fmt(to * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    })(t0);
  }
  const countAll = (root = document) => root.querySelectorAll("[data-count]").forEach(countUp);

  /* ---- Enhanced 3D Card Tilt & Ambient Parallax System ---- */
  if (canTilt) {
    let raf = 0;
    let activeCard = null;

    document.addEventListener("mousemove", e => {
      const c = e.target.closest && e.target.closest(".tilt");
      if (!c) {
        if (activeCard) {
          activeCard.style.transform = "";
          activeCard = null;
        }
        return;
      }

      activeCard = c;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const r = c.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width;
        const y = (e.clientY - r.top) / r.height;
        const rotX = (0.5 - y) * 5;
        const rotY = (x - 0.5) * 6;

        c.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-3px)`;
        c.style.setProperty("--mx", (x * 100).toFixed(1) + "%");
        c.style.setProperty("--my", (y * 100).toFixed(1) + "%");
      });
    }, { passive: true });

    document.addEventListener("mouseout", e => {
      const c = e.target.closest && e.target.closest(".tilt");
      if (c && (!e.relatedTarget || !c.contains(e.relatedTarget))) {
        c.style.transform = "";
      }
    }, { passive: true });
  }

  /* ---- mobile menu ---- */
  const burger = document.querySelector(".burger"), menu = document.getElementById("menu");
  if (burger && menu) {
    burger.addEventListener("click", () => {
      const open = menu.classList.toggle("open");
      burger.setAttribute("aria-expanded", open); burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
    document.addEventListener("keydown", e => { if (e.key === "Escape") { menu.classList.remove("open"); burger.setAttribute("aria-expanded", "false"); } });
  }

  /* ---- short fade between pages ---- */
  document.addEventListener("click", e => {
    const a = e.target.closest && e.target.closest("a[href]");
    if (!a || reduce || e.metaKey || e.ctrlKey || e.shiftKey || e.button || a.target || a.hasAttribute("download")) return;
    const u = new URL(a.href, location.href);
    if (u.origin !== location.origin || u.pathname === location.pathname || !u.pathname.endsWith(".html")) return;
    e.preventDefault(); document.body.classList.add("leaving");
    setTimeout(() => { location.href = u.href; }, 140);
  });
  addEventListener("pageshow", () => document.body.classList.remove("leaving"));

  function emptyState(el) {
    el.innerHTML = `<div class="glass empty-card"><span class="chip-ico">${ico("pulse")}</span><h3>No analysis yet</h3>
      <p>Run a health analysis first, then your results will appear here.</p><a class="btn p" href="index.html#analysis">Start health analysis</a></div>`;
  }

  /* ---- home form: communicates with FastAPI and saves to database if authenticated ---- */
  function initForm() {
    const form = document.getElementById("analysis-form"); if (!form) return;
    form.querySelectorAll("select[data-options]").forEach(s => {
      s.innerHTML = CONFIG.OPTIONS[s.dataset.options].map(o => `<option>${esc(o)}</option>`).join("");
    });
    const btn = document.getElementById("submit-btn"), err = document.getElementById("form-error");
    const btnLabel = btn ? (btn.querySelector(".btn-label") || btn) : null;
    const originalLabel = btnLabel ? btnLabel.textContent : "Submit Assessment";

    // Live Red-Flag Clinical Emergency Monitor
    const redFlagBox = document.getElementById("red-flag-alert");
    function checkLiveRedFlags() {
      if (!redFlagBox) return;
      const sbp = parseFloat(form.querySelector("#systolic_blood_pressure")?.value || 0);
      const hr = parseFloat(form.querySelector("#heart_rate")?.value || 0);
      const spo2 = parseFloat(form.querySelector("#oxygen_saturation")?.value || 100);
      const cp = parseFloat(form.querySelector("#chest_pain_severity")?.value || 0);

      const flags = [];
      if (sbp >= 180) flags.push(`Critical Systolic BP (${sbp} mmHg — Hypertensive Crisis)`);
      if (spo2 > 0 && spo2 < 90) flags.push(`Severe Hypoxemia (SpO₂ ${spo2}%)`);
      if (cp >= 7) flags.push(`Severe Chest Pain (${cp}/10)`);
      if (hr > 140) flags.push(`Extreme Tachycardia (${hr} bpm)`);
      else if (hr > 0 && hr < 40) flags.push(`Extreme Bradycardia (${hr} bpm)`);

      if (flags.length > 0) {
        redFlagBox.hidden = false;
        redFlagBox.style.display = "flex";
        redFlagBox.innerHTML = `
          <div class="urgent-ico-3d-wrap">
            <span class="urgent-ico" aria-hidden="true">⚠️</span>
            <span class="urgent-pulse-wave"></span>
          </div>
          <div class="urgent-content-col">
            <div class="urgent-badge-pill" style="background:rgba(239,68,68,0.2);color:#f87171;border-color:rgba(239,68,68,0.4)">Critical Vital Warning</div>
            <h3 style="margin:.2rem 0;color:#fca5a5;font-size:1.05rem">Immediate Clinical Attention Advised</h3>
            <p style="margin:0 0 .4rem;font-size:.88rem;color:var(--text)">Entered values indicate urgent clinical deviation: <strong>${esc(flags.join(" • "))}</strong>.</p>
            <p style="margin:0;font-size:.82rem;color:var(--mute)">If experiencing acute pressure, shortness of breath, or dizziness, <strong>call emergency services immediately (112 / 911)</strong>.</p>
          </div>
        `;
      } else {
        redFlagBox.hidden = true;
        redFlagBox.style.display = "none";
        redFlagBox.innerHTML = "";
      }
    }

    form.querySelectorAll("input, select").forEach(inp => {
      inp.addEventListener("input", checkLiveRedFlags);
      inp.addEventListener("change", checkLiveRedFlags);
    });

    form.addEventListener("submit", async e => {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      const fd = Object.fromEntries(new FormData(form)), text = ["gender", "smoker_status", "diabetes_history"], payload = {};
      for (const [k, v] of Object.entries(fd)) payload[k] = text.includes(k) ? v : Number(v);
      payload.age = Math.round(payload.age);

      if (btn) btn.disabled = true;
      if (btnLabel) btnLabel.textContent = "Analyzing & Saving…";
      if (err) {
        err.hidden = true;
        err.style.display = "none";
        err.textContent = "";
      }

      try {
        const result = window.HR_API
          ? await window.HR_API.predict.run(payload)
          : await (await fetch(CONFIG.API_URL + "/predict", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            })).json();

        store.set({ result, patient: payload, savedAt: Date.now() });
        location.href = "result.html";
      } catch (ex) {
        if (err) {
          err.hidden = false;
          err.style.display = "flex";
          err.textContent = `Could not get a result: ${ex.message}. Please verify the backend server is running.`;
        }
        if (btn) btn.disabled = false;
        if (btnLabel) btnLabel.textContent = originalLabel;
      }
    });
  }

  /* ---- recent health problem form on home page ---- */
  function initProblemForm() {
    const form = document.getElementById("problem-form");
    if (!form) return;

    const textarea = document.getElementById("problem-text");
    const severitySel = document.getElementById("problem-severity");
    const durationInput = document.getElementById("problem-duration");
    const btn = document.getElementById("problem-submit-btn");
    const statusBox = document.getElementById("problem-status");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = textarea.value.trim();
      if (!text) {
        textarea.focus();
        return;
      }

      const proceedSave = async () => {
        btn.disabled = true;
        btn.textContent = "Saving to database…";
        statusBox.style.display = "flex";
        statusBox.className = "form-state-box info";
        statusBox.innerHTML = `<span>⏳</span><span>Analyzing natural language and saving to database...</span>`;

        try {
          const res = await window.HR_API.problems.create({
            problem_text: text,
            severity: severitySel ? severitySel.value : "Moderate",
            duration: durationInput ? durationInput.value.trim() : null
          });

          statusBox.className = "form-state-box success";
          statusBox.innerHTML = `<span>✓</span><span>Saved to clinical record! Category: <strong>${esc(res.problem_category)}</strong> (Severity: ${esc(res.severity)})</span>`;
          textarea.value = "";
          if (durationInput) durationInput.value = "";
          btn.disabled = false;
          btn.textContent = "Save Another Health Problem";
          if (window.HR_UI) window.HR_UI.showToast("Health problem logged successfully!", "success");
          initDashboard();
        } catch (err) {
          statusBox.className = "form-state-box error";
          statusBox.innerHTML = `<span>⚠</span><span>${esc(err.message)}</span>`;
          btn.disabled = false;
          btn.textContent = "Save Health Problem";
        }
      };

      if (window.HR_UI) {
        window.HR_UI.ensureAuth("record your health problem", proceedSave);
      } else {
        await proceedSave();
      }
    });
  }

  /* ---- Professional Healthcare Analytics Dashboard Initialization ---- */
  async function initDashboard() {
    const welcomeHeading = document.getElementById("welcome-heading");
    if (!welcomeHeading) return;

    const userNameEl = document.getElementById("dash-user-name");
    const todayDateEl = document.getElementById("dash-today-date");
    const totalEvalsEl = document.getElementById("dash-total-evals-badge");
    const latestRiskBadgeSlot = document.getElementById("latest-risk-badge-slot");
    const latestRiskContent = document.getElementById("latest-risk-content");
    const vitalsTimeBadge = document.getElementById("vitals-time-badge");
    const vitalsRowsContainer = document.getElementById("vitals-rows-container");
    const hubPrescCount = document.getElementById("hub-presc-count");
    const hubAllergyCount = document.getElementById("hub-allergy-count");
    const hubProblemCount = document.getElementById("hub-problem-count");
    const historySnapshotContainer = document.getElementById("history-snapshot-container");

    // 1. Format today's date cleanly
    if (todayDateEl) {
      try {
        const now = new Date();
        todayDateEl.textContent = now.toLocaleDateString("en-US", {
          weekday: "long",
          month: "long",
          day: "numeric",
          year: "numeric"
        });
      } catch {
        todayDateEl.textContent = new Date().toDateString();
      }
    }

    // Live Backend & ML Model Status Indicator
    const modelStatusEl = document.getElementById("dash-model-status");
    if (modelStatusEl) {
      if (window.HR_API && window.HR_API.checkHealth) {
        window.HR_API.checkHealth().then(health => {
          if (health.online && health.model_loaded) {
            modelStatusEl.innerHTML = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#4ade80;margin-right:5px"></span> ML Model Online (Random Forest)`;
          } else if (health.online) {
            modelStatusEl.innerHTML = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#fbbf24;margin-right:5px"></span> Backend Connected (Model Standby)`;
          } else {
            modelStatusEl.innerHTML = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#f87171;margin-right:5px"></span> Backend Offline (Port 8000)`;
          }
        }).catch(() => {
          modelStatusEl.innerHTML = `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#f87171;margin-right:5px"></span> Backend Offline (Port 8000)`;
        });
      } else {
        modelStatusEl.textContent = "Random Forest Active";
      }
    }

    const formatDate = (isoStr) => {
      if (!isoStr) return "";
      try {
        const d = new Date(isoStr);
        return d.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit"
        });
      } catch {
        return String(isoStr);
      }
    };

    const getRiskMeta = (riskStr) => {
      const k = riskKey(riskStr);
      const icons = {
        low: "🟢",
        mod: "🟡",
        high: "🟠",
        crit: "🔴",
        info: "ℹ️"
      };
      return {
        key: k,
        icon: icons[k] || "ℹ️",
        label: riskStr || "Unknown Risk"
      };
    };

    // 2. Resolve User Profile
    let currentUser = null;
    if (window.HR_API && window.HR_API.auth) {
      currentUser = window.HR_API.auth.getUser();
    }
    if (userNameEl) {
      userNameEl.textContent = currentUser && currentUser.name ? currentUser.name : "Patient";
    }

    // 3. Fetch real data from backend endpoints (or fallback to local session)
    let historyRecords = [];
    let prescriptionCount = 0;
    let allergyCount = 0;
    let problemCount = 0;

    if (window.HR_API && window.HR_API.auth && window.HR_API.auth.isAuthenticated()) {
      try {
        const [histRes, prescRes, allergyRes, probRes] = await Promise.allSettled([
          window.HR_API.predict.getHistory(),
          window.HR_API.prescriptions.list(),
          window.HR_API.allergies.list(),
          window.HR_API.problems.list()
        ]);

        if (histRes.status === "fulfilled" && Array.isArray(histRes.value)) {
          historyRecords = histRes.value;
        }
        if (prescRes.status === "fulfilled" && Array.isArray(prescRes.value)) {
          prescriptionCount = prescRes.value.length;
        }
        if (allergyRes.status === "fulfilled" && Array.isArray(allergyRes.value)) {
          allergyCount = allergyRes.value.length;
        }
        if (probRes.status === "fulfilled" && Array.isArray(probRes.value)) {
          problemCount = probRes.value.length;
        }
      } catch (err) {
        console.warn("[Dashboard] Could not fetch live records:", err);
      }
    }

    // Update Hub Action Counts
    if (hubPrescCount) {
      hubPrescCount.textContent = prescriptionCount > 0
        ? `${prescriptionCount} Active Record${prescriptionCount === 1 ? '' : 's'}`
        : "Prescription Vault";
    }
    if (hubAllergyCount) {
      hubAllergyCount.textContent = allergyCount > 0
        ? `${allergyCount} Documented`
        : "Allergy Profile";
    }
    if (hubProblemCount) {
      hubProblemCount.textContent = problemCount > 0
        ? `${problemCount} Logged Complaint${problemCount === 1 ? '' : 's'}`
        : "Symptom Log";
    }

    // Update total assessments badge
    if (totalEvalsEl) {
      const evalCount = historyRecords.length;
      totalEvalsEl.textContent = `${evalCount} Assessment${evalCount === 1 ? '' : 's'} Recorded`;
    }

    // 4. Render Latest Health Risk Result
    const sessionData = store.get();
    let latestAssessment = null;

    if (historyRecords.length > 0) {
      latestAssessment = historyRecords[0];
    } else if (sessionData && sessionData.result) {
      latestAssessment = {
        predicted_risk: sessionData.result.risk_level || "Assessed",
        confidence: sessionData.result.confidence || 0,
        systolic_blood_pressure: sessionData.patient ? sessionData.patient.systolic_blood_pressure : null,
        heart_rate: sessionData.patient ? sessionData.patient.heart_rate : null,
        oxygen_saturation: sessionData.patient ? sessionData.patient.oxygen_saturation : null,
        chest_pain_severity: sessionData.patient ? sessionData.patient.chest_pain_severity : null,
        body_temperature: sessionData.patient ? sessionData.patient.body_temperature : null,
        created_at: sessionData.savedAt ? new Date(sessionData.savedAt).toISOString() : new Date().toISOString()
      };
    }

    if (latestAssessment) {
      const meta = getRiskMeta(latestAssessment.predicted_risk);
      const confNum = Number(latestAssessment.confidence) || 0;

      if (latestRiskBadgeSlot) {
        latestRiskBadgeSlot.innerHTML = `<span class="status-pill ${meta.key}"><span aria-hidden="true">${meta.icon}</span> ${esc(meta.label)}</span>`;
      }

      if (latestRiskContent) {
        latestRiskContent.innerHTML = `
          <div class="risk-display-number">${esc(latestAssessment.predicted_risk)}</div>
          <div class="risk-confidence-text">
            <span>🎯 <strong>${confNum.toFixed(1)}%</strong> AI Model Confidence</span>
            <span>·</span>
            <span style="font-size:.82rem;color:var(--text-muted)">Evaluated ${formatDate(latestAssessment.created_at)}</span>
          </div>

          <div style="margin: .9rem 0 1.1rem">
            <div style="display:flex;justify-content:space-between;font-size:.8rem;color:var(--text-secondary);font-weight:600;margin-bottom:.3rem">
              <span>ML Predictive Reliability</span>
              <span>${confNum.toFixed(1)}%</span>
            </div>
            <div style="height:7px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden">
              <div style="width:${Math.min(Math.max(confNum, 12), 100)}%;height:100%;border-radius:99px;background:var(--risk-${meta.key}, var(--primary))"></div>
            </div>
          </div>

          <div class="vitals-snapshot-row">
            <div class="snapshot-item">
              <span class="snapshot-label">Blood Pressure</span>
              <span class="snapshot-val">${esc(latestAssessment.systolic_blood_pressure ?? '—')}<small>mmHg</small></span>
            </div>
            <div class="snapshot-item">
              <span class="snapshot-label">Heart Rate</span>
              <span class="snapshot-val">${esc(latestAssessment.heart_rate ?? '—')}<small>bpm</small></span>
            </div>
            <div class="snapshot-item">
              <span class="snapshot-label">SpO2 Oxygen</span>
              <span class="snapshot-val">${esc(latestAssessment.oxygen_saturation ?? '—')}<small>%</small></span>
            </div>
            <div class="snapshot-item">
              <span class="snapshot-label">Chest Pain</span>
              <span class="snapshot-val">${esc(latestAssessment.chest_pain_severity ?? '0')}<small>/10</small></span>
            </div>
          </div>

          <div class="card-action-footer">
            <a href="result.html" class="btn btn-sm p">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
              View Full Risk Analysis
            </a>
            <a href="recommendation.html" class="btn btn-sm">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              Clinical Guidance &rarr;
            </a>
          </div>
        `;
      }
    } else {
      if (latestRiskBadgeSlot) {
        latestRiskBadgeSlot.innerHTML = `<span class="status-pill info"><span aria-hidden="true">ℹ️</span> Awaiting Assessment</span>`;
      }

      if (latestRiskContent) {
        latestRiskContent.innerHTML = `
          <div style="padding:1.2rem 0">
            <div style="font-size:1.15rem;font-weight:700;color:var(--text-main);margin-bottom:.35rem">No Prior Evaluations Found</div>
            <p style="color:var(--text-secondary);font-size:.92rem;line-height:1.6;margin:0 0 1.2rem">
              You haven't run any health evaluations yet. Enter your physiological indicators in the assessment form below to calculate your cardiovascular risk score and unlock personalized clinical guidance.
            </p>
            <a href="#analysis" class="btn btn-sm p">
              <span>Run First Health Assessment &darr;</span>
            </a>
          </div>
        `;
      }
    }

    // 5. Render Key Health Indicators (Vitals Summary)
    if (vitalsRowsContainer) {
      if (latestAssessment) {
        if (vitalsTimeBadge) {
          vitalsTimeBadge.textContent = `Latest: ${formatDate(latestAssessment.created_at)}`;
        }

        const bp = Number(latestAssessment.systolic_blood_pressure);
        const hr = Number(latestAssessment.heart_rate);
        const spo2 = Number(latestAssessment.oxygen_saturation);
        const temp = Number(latestAssessment.body_temperature);
        const cp = Number(latestAssessment.chest_pain_severity);

        let bpTag = { cls: "optimal", text: "✓ Optimal (<120)" };
        if (bp >= 140) bpTag = { cls: "elevated", text: "⚠ Stage 2 HTN (≥140)" };
        else if (bp >= 130) bpTag = { cls: "elevated", text: "⚠ Stage 1 HTN (130-139)" };
        else if (bp >= 120) bpTag = { cls: "elevated", text: "⚠ Elevated (120-129)" };

        let hrTag = { cls: "optimal", text: "✓ Normal (60-100)" };
        if (hr > 100) hrTag = { cls: "elevated", text: "⚠ Tachycardia (>100)" };
        else if (hr < 60) hrTag = { cls: "neutral", text: "⚠ Bradycardia (<60)" };

        let spo2Tag = { cls: "optimal", text: "✓ Optimal (≥95%)" };
        if (spo2 < 90) spo2Tag = { cls: "elevated", text: "⚠ Hypoxemia (<90%)" };
        else if (spo2 < 95) spo2Tag = { cls: "neutral", text: "⚠ Borderline (90-94%)" };

        let tempTag = { cls: "optimal", text: "✓ Normal (36.5-37.5)" };
        if (temp > 37.5) tempTag = { cls: "elevated", text: "⚠ Fever (>37.5°C)" };
        else if (temp < 36.0) tempTag = { cls: "neutral", text: "⚠ Low (<36.0°C)" };

        let cpTag = { cls: "optimal", text: "✓ Asymptomatic (0)" };
        if (cp >= 7) cpTag = { cls: "elevated", text: "⚠ Severe (7-10)" };
        else if (cp >= 4) cpTag = { cls: "elevated", text: "⚠ Moderate (4-6)" };
        else if (cp > 0) cpTag = { cls: "neutral", text: "⚠ Mild (1-3)" };

        vitalsRowsContainer.innerHTML = `
          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:var(--primary)">🩸</span>
              <div>
                <div class="vital-title">Systolic Blood Pressure</div>
                <div class="vital-ref-range">Standard Reference: &lt; 120 mmHg</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">${bp ? bp + ' mmHg' : '—'}</div>
              <span class="vital-status-tag ${bpTag.cls}">${bpTag.text}</span>
            </div>
          </div>

          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:var(--secondary)">❤️</span>
              <div>
                <div class="vital-title">Resting Heart Rate</div>
                <div class="vital-ref-range">Standard Reference: 60 - 100 bpm</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">${hr ? hr + ' bpm' : '—'}</div>
              <span class="vital-status-tag ${hrTag.cls}">${hrTag.text}</span>
            </div>
          </div>

          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:#38bdf8">🫁</span>
              <div>
                <div class="vital-title">Oxygen Saturation (SpO2)</div>
                <div class="vital-ref-range">Standard Reference: &ge; 95%</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">${spo2 ? spo2 + '%' : '—'}</div>
              <span class="vital-status-tag ${spo2Tag.cls}">${spo2Tag.text}</span>
            </div>
          </div>

          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:#fbbf24">🌡️</span>
              <div>
                <div class="vital-title">Body Temperature</div>
                <div class="vital-ref-range">Standard Reference: 36.5 - 37.5 &deg;C</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">${temp ? temp + ' °C' : '—'}</div>
              <span class="vital-status-tag ${tempTag.cls}">${tempTag.text}</span>
            </div>
          </div>

          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:#f87171">⚡</span>
              <div>
                <div class="vital-title">Chest Pain Severity</div>
                <div class="vital-ref-range">Scale: 0 (None) to 10 (Emergency)</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">${cp !== undefined ? cp + ' / 10' : '—'}</div>
              <span class="vital-status-tag ${cpTag.cls}">${cpTag.text}</span>
            </div>
          </div>
        `;
      } else {
        if (vitalsTimeBadge) vitalsTimeBadge.textContent = "Standard References";
        vitalsRowsContainer.innerHTML = `
          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:var(--primary)">🩸</span>
              <div>
                <div class="vital-title">Systolic Blood Pressure</div>
                <div class="vital-ref-range">Normal Standard: &lt; 120 mmHg</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">&lt; 120 <small>mmHg</small></div>
              <span class="vital-status-tag neutral">Clinical Target</span>
            </div>
          </div>

          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:var(--secondary)">❤️</span>
              <div>
                <div class="vital-title">Resting Heart Rate</div>
                <div class="vital-ref-range">Normal Standard: 60 - 100 bpm</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">60 - 100 <small>bpm</small></div>
              <span class="vital-status-tag neutral">Clinical Target</span>
            </div>
          </div>

          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:#38bdf8">🫁</span>
              <div>
                <div class="vital-title">Oxygen Saturation (SpO2)</div>
                <div class="vital-ref-range">Normal Standard: &ge; 95%</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">&ge; 95 <small>%</small></div>
              <span class="vital-status-tag neutral">Clinical Target</span>
            </div>
          </div>

          <div class="vital-metric-row">
            <div class="vital-name-col">
              <span class="vital-ico-wrap" style="color:#fbbf24">🌡️</span>
              <div>
                <div class="vital-title">Body Temperature</div>
                <div class="vital-ref-range">Normal Standard: 36.5 - 37.5 &deg;C</div>
              </div>
            </div>
            <div class="vital-reading-col">
              <div class="vital-numeric-val">36.8 <small>&deg;C</small></div>
              <span class="vital-status-tag neutral">Clinical Target</span>
            </div>
          </div>
        `;
      }
    }

    // 6. Render Recent Assessment History Snapshot Table
    if (historySnapshotContainer) {
      if (historyRecords.length > 0) {
        const top3 = historyRecords.slice(0, 3);
        historySnapshotContainer.innerHTML = `
          <div class="compact-table-wrap">
            <table class="compact-history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Risk Level</th>
                  <th>Confidence</th>
                  <th>Vitals</th>
                </tr>
              </thead>
              <tbody>
                ${top3.map(item => {
                  const meta = getRiskMeta(item.predicted_risk);
                  const conf = Number(item.confidence) || 0;
                  return `
                    <tr>
                      <td style="font-size:.82rem;color:var(--text-secondary)">${formatDate(item.created_at)}</td>
                      <td>
                        <span class="status-pill ${meta.key}" style="font-size:.76rem;padding:.15rem .5rem">
                          <span aria-hidden="true">${meta.icon}</span> ${esc(meta.label)}
                        </span>
                      </td>
                      <td style="font-weight:700;font-size:.85rem">${conf.toFixed(1)}%</td>
                      <td style="font-size:.82rem;color:var(--text-muted)">
                        BP: ${esc(item.systolic_blood_pressure)} · HR: ${esc(item.heart_rate)}
                      </td>
                    </tr>
                  `;
                }).join("")}
              </tbody>
            </table>
          </div>
          <div style="margin-top:.9rem;text-align:right">
            <a href="history.html" style="font-size:.85rem;color:var(--primary);font-weight:700;text-decoration:none">
              View Complete Assessment History (${historyRecords.length}) &rarr;
            </a>
          </div>
        `;
      } else {
        historySnapshotContainer.innerHTML = `
          <p style="color:var(--text-muted);font-size:.9rem;line-height:1.6;margin:0 0 .8rem">
            No previous cardiovascular risk evaluations stored in your profile.
          </p>
          <a href="#analysis" class="btn btn-sm" style="font-size:.82rem">Start New Assessment</a>
        `;
      }
    }

    if (latestAssessment && latestAssessment.heart_rate && setCardiacBpm) {
      setCardiacBpm(latestAssessment.heart_rate);
    }
  }

  /* ---- Interactive 3D Cardiac Hologram Mesh Visualizer ---- */
  let setCardiacBpm = null;

  function initCardiac3DVisualizer() {
    const canvas = document.getElementById("cardiac-3d-canvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Retina & High-DPI Display Scaling
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = 210;
    const height = 210;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.scale(dpr, dpr);

    const cx = width / 2;
    const cy = height / 2 - 4;

    // Generate 3D Heart coordinates using parametric cardioid equations
    const nodes = [];
    const uSteps = 16;
    const vSteps = 10;
    for (let i = 0; i < uSteps; i++) {
      const u = (i / uSteps) * Math.PI * 2 - Math.PI;
      const ring = [];
      for (let j = 0; j <= vSteps; j++) {
        const v = (j / vSteps) * Math.PI;
        const sinU = Math.sin(u);
        const cosU = Math.cos(u);
        const sinV = Math.sin(v);
        const cosV = Math.cos(v);

        // Anatomical 3D Cardioid geometry
        const x = 16 * Math.pow(sinU, 3) * sinV;
        const y = -(13 * cosU - 5 * Math.cos(2 * u) - 2 * Math.cos(3 * u) - Math.cos(4 * u)) * sinV;
        const z = 10 * cosV * (0.8 + 0.2 * Math.abs(sinU));

        const scale = 2.45;
        ring.push({ x: x * scale, y: y * scale, z: z * scale, uIdx: i, vIdx: j });
      }
      nodes.push(ring);
    }

    // Dynamic rotation & pulse state
    let targetRotX = 0.15;
    let targetRotY = 0;
    let curRotX = 0.15;
    let curRotY = 0;
    let bpm = 72;
    const bpmEl = document.getElementById("hologram-bpm");

    setCardiacBpm = (newBpm) => {
      const b = parseFloat(newBpm);
      if (!isNaN(b) && b >= 30 && b <= 220) {
        bpm = Math.round(b);
        if (bpmEl) bpmEl.textContent = String(bpm);
      }
    };

    // Mouse tracking for interactive 3D rotation
    let isHovering = false;
    const stage = document.getElementById("cardiac-3d-stage") || canvas;
    const banner = canvas.closest(".dashboard-welcome-banner") || stage;

    banner.addEventListener("mousemove", e => {
      const rect = banner.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width - 0.5;
      const ny = (e.clientY - rect.top) / rect.height - 0.5;
      targetRotY = nx * 1.2;
      targetRotX = -ny * 0.7;
      isHovering = true;
    }, { passive: true });

    banner.addEventListener("mouseleave", () => {
      isHovering = false;
      targetRotX = 0.15;
    }, { passive: true });

    let lastTime = performance.now();
    let animId = null;

    function render(now) {
      if (document.hidden) {
        animId = requestAnimationFrame(render);
        return;
      }

      const dt = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;

      // Smooth 3D rotation spring
      if (!isHovering) {
        targetRotY += dt * 0.35; // slow ambient rotation
      }
      curRotX += (targetRotX - curRotX) * 0.05;
      curRotY += (targetRotY - curRotY) * 0.05;

      // Gentle double-peak ("lub-dub") pulse
      const freq = (bpm / 60) * Math.PI * 2;
      const phase = (now / 1000) * freq;
      const lub = Math.pow(Math.max(0, Math.sin(phase)), 24) * 0.07;
      const dub = Math.pow(Math.max(0, Math.sin(phase - 0.38)), 24) * 0.045;
      const pulseScale = 1.0 + lub + dub;

      ctx.clearRect(0, 0, width, height);

      // 1. Draw glowing 3D depth core
      const coreRadius = (28 + (lub + dub) * 55) * pulseScale;
      const coreGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, Math.max(10, coreRadius));
      coreGrad.addColorStop(0, `rgba(94, 224, 208, ${0.28 + lub * 1.5})`);
      coreGrad.addColorStop(0.45, `rgba(56, 189, 248, ${0.12 + dub * 1.2})`);
      coreGrad.addColorStop(1, "rgba(94, 224, 208, 0)");
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, coreRadius, 0, Math.PI * 2);
      ctx.fill();

      // 2. Project 3D coordinates to 2D screen with perspective divide
      const projected = [];
      const d = 260; // focal length

      const cosY = Math.cos(curRotY);
      const sinY = Math.sin(curRotY);
      const cosX = Math.cos(curRotX);
      const sinX = Math.sin(curRotX);

      for (let i = 0; i < uSteps; i++) {
        const ringProj = [];
        for (let j = 0; j <= vSteps; j++) {
          const pt = nodes[i][j];
          const px = pt.x * pulseScale;
          const py = pt.y * pulseScale;
          const pz = pt.z * pulseScale;

          // Rotate around Y axis
          const x1 = px * cosY + pz * sinY;
          const z1 = -px * sinY + pz * cosY;

          // Rotate around X axis
          const y1 = py * cosX - z1 * sinX;
          const z2 = py * sinX + z1 * cosX + 130; // camera distance

          const sx = cx + (x1 * d) / z2;
          const sy = cy + (y1 * d) / z2;
          const depth = Math.max(0.12, Math.min(1.0, (z2 - 60) / 140));

          ringProj.push({ sx, sy, z: z2, depth });
        }
        projected.push(ringProj);
      }

      // 3. Draw 3D wireframe connecting lines
      ctx.lineWidth = 1.1;

      // Longitudinal lines
      for (let i = 0; i < uSteps; i++) {
        for (let j = 0; j < vSteps; j++) {
          const p1 = projected[i][j];
          const p2 = projected[i][j + 1];
          const avgDepth = (p1.depth + p2.depth) * 0.5;
          const alpha = (0.15 + (1 - avgDepth) * 0.75).toFixed(3);

          ctx.strokeStyle = `rgba(94, 224, 208, ${alpha})`;
          ctx.beginPath();
          ctx.moveTo(p1.sx, p1.sy);
          ctx.lineTo(p2.sx, p2.sy);
          ctx.stroke();
        }
      }

      // Latitudinal rings
      for (let j = 1; j < vSteps; j++) {
        for (let i = 0; i < uSteps; i++) {
          const nextI = (i + 1) % uSteps;
          const p1 = projected[i][j];
          const p2 = projected[nextI][j];
          const avgDepth = (p1.depth + p2.depth) * 0.5;
          const alpha = (0.12 + (1 - avgDepth) * 0.65).toFixed(3);

          ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
          ctx.beginPath();
          ctx.moveTo(p1.sx, p1.sy);
          ctx.lineTo(p2.sx, p2.sy);
          ctx.stroke();
        }
      }

      // 4. Draw glowing 3D nodes
      for (let i = 0; i < uSteps; i += 2) {
        for (let j = 2; j < vSteps; j += 2) {
          const p = projected[i][j];
          if (p.depth < 0.6) {
            const nodeAlpha = (1 - p.depth * 1.2).toFixed(2);
            ctx.fillStyle = `rgba(255, 255, 255, ${nodeAlpha})`;
            ctx.beginPath();
            ctx.arc(p.sx, p.sy, 1.8 + lub * 4, 0, Math.PI * 2);
            ctx.fill();

            if ((i + j) % 4 === 0) {
              ctx.strokeStyle = `rgba(94, 224, 208, ${nodeAlpha * 0.6})`;
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.arc(p.sx, p.sy, 4 + dub * 6, 0, Math.PI * 2);
              ctx.stroke();
            }
          }
        }
      }

      animId = requestAnimationFrame(render);
    }

    animId = requestAnimationFrame(render);
  }

  window.HR = { CONFIG, esc, riskKey, ico, I, store, observe, countAll, emptyState, initDashboard, initCardiac3DVisualizer };
  initForm();
  initProblemForm();
  initDashboard();
  initCardiac3DVisualizer();
  observe(document);
  countAll(document);

  window.addEventListener("hr:auth_changed", () => {
    initDashboard();
  });
})();


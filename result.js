(() => {
  "use strict";
  const { esc, riskKey, ico, store, observe, countAll, emptyState } = window.HR;
  const app = document.getElementById("app"), data = store.get();
  if (!data || !data.result) return emptyState(app);

  const r = data.result, p = data.patient || {}, level = r.risk_level, conf = Number(r.confidence) || 0, k = riskKey(level);
  const off = (339.3 * (1 - Math.max(0, Math.min(conf, 100)) / 100)).toFixed(1);
  const bars = Object.entries(r.probabilities || {}).sort((a, b) => b[1] - a[1]).map(([c, v]) =>
    `<div class="bar"><div class="t"><span>${esc(c)}</span><span>${Number(v).toFixed(1)}%</span></div>
     <div class="tr"><div class="fl ${c === level ? "top" : ""}" style="width:${Math.max(0, Math.min(v, 100))}%"></div></div></div>`).join("");

  // Flag thresholds mirror get_recommendation() in the FastAPI code.
  const metric = (label, val, unit, flagged, i) => {
    const cls = flagged == null ? "neu" : flagged ? "flag" : "ok";
    const st = flagged == null ? "Recorded" : flagged ? "Flagged by system rules" : "Not flagged";
    return `<div class="glass tilt metric reveal ${cls}" style="--i:${i}"><div class="k">${label}</div><div class="v">${esc(val)}<small>${unit}</small></div><span class="pill">${st}</span></div>`;
  };
  const hr = p.heart_rate, sbp = p.systolic_blood_pressure, o2 = p.oxygen_saturation, pain = p.chest_pain_severity;

  app.innerHTML = `
  <div class="grid2 risk-${k}">
    <div class="glass tilt reveal"><div class="ringbox">
      <div class="ring-wrap" role="img" aria-label="Model confidence ${conf.toFixed(1)} percent">
        <svg class="ring" viewBox="0 0 120 120" aria-hidden="true"><circle class="trk" cx="60" cy="60" r="54"/><circle class="val" cx="60" cy="60" r="54" style="--off:${off}"/></svg>
        <div class="ring-c"><b data-count="${conf}" data-decimals="0" data-suffix="%">${conf.toFixed(0)}%</b><small>model confidence</small></div></div>
      <div><span class="pill">Risk level</span><div class="level">${esc(level)}</div><p>The model is ${conf.toFixed(1)}% confident in this level.</p></div>
    </div></div>
    <div class="glass tilt reveal" style="--i:1"><h3>Probability by risk level</h3>${bars || '<p class="empty">No probabilities returned.</p>'}</div>
  </div>
  <h2 class="reveal" style="margin-top:1.6rem;font-size:1.2rem">Health indicators</h2>
  <div class="grid">
    ${metric("Heart rate", hr, "bpm", hr < 50 || hr > 120, 0)}${metric("Systolic blood pressure", sbp, "mmHg", sbp >= 140, 1)}
    ${metric("Oxygen saturation", o2, "%", o2 < 94, 2)}${metric("Chest pain severity", pain, "/ 10", pain >= 7, 3)}
    ${metric("Body temperature", p.body_temperature, "°C", null, 4)}${metric("Age", p.age, "years", null, 5)}
  </div>
  <div class="glass tilt reveal"><h3>Prediction summary</h3>
    <div class="kv" style="margin:.8rem 0"><div>Risk level<b>${esc(level)}</b></div><div>Confidence<b>${conf.toFixed(1)}%</b></div>
      <div>Gender<b>${esc(p.gender)}</b></div><div>Smoker status<b>${esc(p.smoker_status)}</b></div><div>Diabetes history<b>${esc(p.diabetes_history)}</b></div></div>
    <p>This is an AI estimate, not a diagnosis. Review the recommendations next.</p></div>
  <div class="pager noprint" style="flex-wrap:wrap;gap:.6rem"><a class="btn" href="index.html">Back to Form</a><a class="btn" href="timeline.html">Timeline</a><a class="btn" href="briefing.html">Doctor Briefing</a><a class="btn p" href="recommendation.html">Next: Guidance</a></div>`;
  observe(app); countAll(app);
})();

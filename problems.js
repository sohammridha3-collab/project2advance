/**
 * Logic for Recent Problems Page
 */
(() => {
  "use strict";

  const { problems, auth } = window.HR_API;
  const { showToast, ensureAuth, openAuthModal } = window.HR_UI;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const app = document.getElementById("problems-app");
  const toggleBtn = document.getElementById("add-problem-toggle-btn");
  const panel = document.getElementById("add-problem-panel");
  const cancelBtn = document.getElementById("cancel-add-btn");
  const form = document.getElementById("page-problem-form");
  const statusBox = document.getElementById("page-problem-status");
  const submitBtn = document.getElementById("page-problem-submit-btn");

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

  async function loadProblems() {
    if (!auth.isAuthenticated()) {
      app.innerHTML = `
        <div class="glass empty-card">
          <span class="chip-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>
          <h3>Account Access Required</h3>
          <p>Please sign in to securely access and manage your personal health problems history.</p>
          <button id="auth-prompt-btn" class="btn p" type="button" style="margin-top:1rem">Sign In / Register</button>
        </div>
      `;
      document.getElementById("auth-prompt-btn").addEventListener("click", () => {
        openAuthModal("login", () => loadProblems());
      });
      return;
    }

    app.innerHTML = `<div class="glass empty-card"><p>Loading your health records...</p></div>`;

    try {
      const items = await problems.list();

      if (!items || items.length === 0) {
        app.innerHTML = `
          <div class="glass empty-card">
            <span class="chip-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg></span>
            <h3>No health problems recorded</h3>
            <p>You haven't logged any health complaints or symptoms yet. Click the button above to record one.</p>
            <button id="empty-add-btn" class="btn p" type="button" style="margin-top:1rem">+ Log First Health Problem</button>
          </div>
        `;
        document.getElementById("empty-add-btn").addEventListener("click", () => {
          panel.style.display = "block";
          document.getElementById("page-problem-text").focus();
        });
        return;
      }

      app.innerHTML = items.map(item => `
        <div class="glass tilt history-item" id="problem-card-${item.id}">
          <div class="card-header">
            <div>
              <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap">
                <span class="card-badge badge-cat">${esc(item.problem_category || "General Health")}</span>
                <span class="card-badge badge-sev ${esc(item.severity || "Moderate")}">${esc(item.severity || "Moderate")} Severity</span>
                ${item.duration ? `<span class="pill-chip">⏱ ${esc(item.duration)}</span>` : ""}
              </div>
              <div class="history-meta" style="margin-top:.5rem">
                <span>📅 ${formatDate(item.created_at)}</span>
              </div>
            </div>
            <button class="btn btn-sm btn-danger del-btn" data-id="${item.id}" type="button" title="Delete record">Delete</button>
          </div>
          <p style="color:var(--text);font-size:1.02rem;line-height:1.6;margin:0;white-space:pre-wrap">${esc(item.problem_text)}</p>
        </div>
      `).join("");

      // Bind delete handlers
      app.querySelectorAll(".del-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          if (confirm("Are you sure you want to delete this health problem record?")) {
            btn.disabled = true;
            btn.textContent = "Deleting...";
            try {
              await problems.delete(id);
              showToast("Health problem deleted.", "info");
              const card = document.getElementById(`problem-card-${id}`);
              if (card) {
                card.style.opacity = "0";
                card.style.transform = "scale(0.95)";
                setTimeout(() => loadProblems(), 250);
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
          <p style="color:#ff9aa9">Failed to load problems: ${esc(err.message)}</p>
          <button class="btn" type="button" onclick="location.reload()" style="margin-top:1rem">Try Again</button>
        </div>
      `;
    }
  }

  // Toggle quick add panel
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      ensureAuth("log a health problem", () => {
        panel.style.display = panel.style.display === "none" ? "block" : "none";
        if (panel.style.display === "block") {
          document.getElementById("page-problem-text").focus();
        }
      });
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      panel.style.display = "none";
      form.reset();
      statusBox.style.display = "none";
    });
  }

  // Form submit
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = document.getElementById("page-problem-text").value.trim();
      const category = document.getElementById("page-problem-cat").value.trim();
      const severity = document.getElementById("page-problem-sev").value;
      const duration = document.getElementById("page-problem-dur").value.trim();

      if (!text) {
        document.getElementById("page-problem-text").focus();
        return;
      }

      ensureAuth("save this health problem", async () => {
        submitBtn.disabled = true;
        submitBtn.textContent = "Saving to database...";
        statusBox.style.display = "flex";
        statusBox.className = "form-state-box info";
        statusBox.innerHTML = `<span>⏳</span><span>Analyzing and storing in database...</span>`;

        try {
          const created = await problems.create({
            problem_text: text,
            problem_category: category || null,
            severity: severity,
            duration: duration || null
          });

          showToast("Health problem saved successfully!", "success");
          form.reset();
          panel.style.display = "none";
          statusBox.style.display = "none";
          submitBtn.disabled = false;
          submitBtn.textContent = "Save Problem";
          loadProblems();
        } catch (err) {
          statusBox.className = "form-state-box error";
          statusBox.innerHTML = `<span>⚠</span><span>${esc(err.message)}</span>`;
          submitBtn.disabled = false;
          submitBtn.textContent = "Save Problem";
        }
      });
    });
  }

  window.addEventListener("hr:auth_changed", loadProblems);
  document.addEventListener("DOMContentLoaded", loadProblems);
})();

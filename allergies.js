/**
 * Logic for Allergy Profile Page
 */
(() => {
  "use strict";

  const { allergies, auth } = window.HR_API;
  const { showToast, ensureAuth, openAuthModal } = window.HR_UI;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const app = document.getElementById("allergies-app");
  const toggleBtn = document.getElementById("toggle-allergy-btn");
  const panel = document.getElementById("allergy-panel");
  const cancelBtn = document.getElementById("cancel-allergy-btn");
  const form = document.getElementById("allergy-form");
  const statusBox = document.getElementById("allergy-form-status");
  const submitBtn = document.getElementById("submit-allergy-btn");

  async function loadAllergies() {
    if (!auth.isAuthenticated()) {
      app.innerHTML = `
        <div class="glass empty-card">
          <span class="chip-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span>
          <h3>Account Access Required</h3>
          <p>Please sign in to view and manage your personal medical allergy profile.</p>
          <button id="auth-allergy-btn" class="btn p" type="button" style="margin-top:1rem">Sign In / Register</button>
        </div>
      `;
      document.getElementById("auth-allergy-btn").addEventListener("click", () => {
        openAuthModal("login", () => loadAllergies());
      });
      return;
    }

    app.innerHTML = `<div class="glass empty-card"><p>Loading allergies from database...</p></div>`;

    try {
      const items = await allergies.list();

      if (!items || items.length === 0) {
        app.innerHTML = `
          <div class="glass empty-card">
            <span class="chip-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span>
            <h3>No known allergies recorded</h3>
            <p>You haven't listed any drug or substance allergies. Adding them helps prevent adverse medication contraindications.</p>
            <button id="empty-allergy-btn" class="btn p" type="button" style="margin-top:1rem">+ Add Your First Allergy</button>
          </div>
        `;
        document.getElementById("empty-allergy-btn").addEventListener("click", () => {
          panel.style.display = "block";
          document.getElementById("allergen-name").focus();
        });
        return;
      }

      app.innerHTML = items.map(item => `
        <div class="glass tilt history-item" id="allergy-card-${item.id}" style="margin-bottom:1.1rem">
          <div class="card-header" id="allergy-header-${item.id}">
            <div>
              <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap">
                <h3 style="margin:0;font-size:1.15rem;color:var(--text)">${esc(item.allergen)}</h3>
                <span class="card-badge badge-sev ${esc(item.severity || 'Moderate')}">${esc(item.severity || 'Moderate')}</span>
              </div>
              ${item.reaction ? `<p style="margin:.4rem 0 0;font-size:.92rem;color:var(--mute)">Observed Reaction: <span style="color:var(--text)">${esc(item.reaction)}</span></p>` : `<p style="margin:.4rem 0 0;font-size:.85rem;color:var(--mute);font-style:italic">No reaction details specified</p>`}
            </div>
            <div style="display:flex;gap:.5rem;align-items:center">
              <button class="btn btn-sm edit-allergy-btn" data-id="${item.id}" type="button">Edit</button>
              <button class="btn btn-sm btn-danger del-allergy-btn" data-id="${item.id}" type="button">Delete</button>
            </div>
          </div>

          <!-- Inline Edit Form (Hidden by default) -->
          <div id="allergy-edit-box-${item.id}" style="display:none;padding-top:1rem;margin-top:.8rem;border-top:1px solid var(--border-subtle)">
            <div class="form-row">
              <label style="font-size:.85rem;color:var(--mute);font-weight:600">
                Allergen / Substance *
                <input type="text" id="edit-allergen-${item.id}" value="${esc(item.allergen)}" required style="font:500 .95rem 'Manrope',sans-serif;color:var(--text);min-height:42px;padding:0 .8rem;border-radius:10px;border:1px solid var(--edge);background:rgba(8,16,34,.7);width:100%;box-sizing:border-box;margin-top:.35rem">
              </label>
              <label style="font-size:.85rem;color:var(--mute);font-weight:600">
                Severity
                <select id="edit-severity-${item.id}" style="font:500 .95rem 'Manrope',sans-serif;color:var(--text);min-height:42px;padding:0 .8rem;border-radius:10px;border:1px solid var(--edge);background:rgba(8,16,34,.7);width:100%;box-sizing:border-box;margin-top:.35rem">
                  <option value="Mild" ${item.severity === 'Mild' ? 'selected' : ''}>Mild - Rash, minor reaction</option>
                  <option value="Moderate" ${item.severity === 'Moderate' || !item.severity ? 'selected' : ''}>Moderate - Hives, discomfort</option>
                  <option value="Severe" ${item.severity === 'Severe' ? 'selected' : ''}>Severe - Anaphylaxis / critical</option>
                </select>
              </label>
            </div>
            <label style="display:block;font-size:.85rem;color:var(--mute);font-weight:600;margin-top:.6rem">
              Observed Reaction
              <input type="text" id="edit-reaction-${item.id}" value="${esc(item.reaction || '')}" placeholder="e.g. Skin hives, facial swelling" style="font:500 .95rem 'Manrope',sans-serif;color:var(--text);min-height:42px;padding:0 .8rem;border-radius:10px;border:1px solid var(--edge);background:rgba(8,16,34,.7);width:100%;box-sizing:border-box;margin-top:.35rem">
            </label>
            <div style="display:flex;gap:.6rem;justify-content:flex-end;margin-top:1rem">
              <button class="btn btn-sm cancel-edit-allergy-btn" data-id="${item.id}" type="button">Cancel</button>
              <button class="btn btn-sm p save-edit-allergy-btn" data-id="${item.id}" type="button">Save Changes</button>
            </div>
          </div>
        </div>
      `).join("");

      // Bind edit handlers
      app.querySelectorAll(".edit-allergy-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const id = btn.dataset.id;
          const box = document.getElementById(`allergy-edit-box-${id}`);
          if (box) {
            const isOpen = box.style.display !== "none";
            box.style.display = isOpen ? "none" : "block";
            btn.textContent = isOpen ? "Edit" : "Close";
          }
        });
      });

      app.querySelectorAll(".cancel-edit-allergy-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const id = btn.dataset.id;
          const box = document.getElementById(`allergy-edit-box-${id}`);
          const editBtn = app.querySelector(`.edit-allergy-btn[data-id="${id}"]`);
          if (box) box.style.display = "none";
          if (editBtn) editBtn.textContent = "Edit";
        });
      });

      app.querySelectorAll(".save-edit-allergy-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          const allergenVal = document.getElementById(`edit-allergen-${id}`).value.trim();
          const sevVal = document.getElementById(`edit-severity-${id}`).value;
          const reactVal = document.getElementById(`edit-reaction-${id}`).value.trim();

          if (!allergenVal) {
            showToast("Allergen name is required.", "error");
            return;
          }

          btn.disabled = true;
          btn.textContent = "Saving...";

          try {
            await allergies.update(id, {
              allergen: allergenVal,
              severity: sevVal,
              reaction: reactVal || null
            });
            showToast("Allergy updated successfully!", "success");
            loadAllergies();
          } catch (updateErr) {
            showToast(`Failed to update allergy: ${updateErr.message}`, "error");
            btn.disabled = false;
            btn.textContent = "Save Changes";
          }
        });
      });

      // Bind delete handlers
      app.querySelectorAll(".del-allergy-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          if (confirm("Are you sure you want to remove this allergy from your medical profile?")) {
            btn.disabled = true;
            btn.textContent = "Deleting...";
            try {
              await allergies.delete(id);
              showToast("Allergy removed.", "info");
              const card = document.getElementById(`allergy-card-${id}`);
              if (card) {
                card.style.opacity = "0";
                card.style.transform = "scale(0.95)";
                setTimeout(() => loadAllergies(), 250);
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
          <p style="color:#ff9aa9">Failed to load allergies: ${esc(err.message)}</p>
          <button class="btn" type="button" onclick="location.reload()" style="margin-top:1rem">Try Again</button>
        </div>
      `;
    }
  }

  // Toggle quick add panel
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      ensureAuth("add an allergy", () => {
        panel.style.display = panel.style.display === "none" ? "block" : "none";
        if (panel.style.display === "block") {
          document.getElementById("allergen-name").focus();
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
      const allergen = document.getElementById("allergen-name").value.trim();
      const severity = document.getElementById("allergen-sev").value;
      const reaction = document.getElementById("allergen-reaction").value.trim();

      if (!allergen) {
        document.getElementById("allergen-name").focus();
        return;
      }

      ensureAuth("save this allergy", async () => {
        submitBtn.disabled = true;
        submitBtn.textContent = "Saving to database...";
        statusBox.style.display = "flex";
        statusBox.className = "form-state-box info";
        statusBox.innerHTML = `<span>⏳</span><span>Recording allergy in clinical database...</span>`;

        try {
          await allergies.create({
            allergen: allergen,
            severity: severity,
            reaction: reaction || null
          });

          showToast(`Allergy '${allergen}' added!`, "success");
          form.reset();
          panel.style.display = "none";
          statusBox.style.display = "none";
          submitBtn.disabled = false;
          submitBtn.textContent = "Save Allergy";
          loadAllergies();
        } catch (err) {
          statusBox.className = "form-state-box error";
          statusBox.innerHTML = `<span>⚠</span><span>${esc(err.message)}</span>`;
          submitBtn.disabled = false;
          submitBtn.textContent = "Save Allergy";
        }
      });
    });
  }

  window.addEventListener("hr:auth_changed", loadAllergies);
  document.addEventListener("DOMContentLoaded", loadAllergies);
})();

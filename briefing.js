/**
 * Doctor-Visit Briefing & Secure Sharing Logic for HealthBridge AI
 */
(() => {
  "use strict";

  const { briefings, auth } = window.HR_API;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // DOM elements
  const draftForm = document.getElementById("draft-form");
  const draftReason = document.getElementById("draft-reason");
  const btnGenerateDraft = document.getElementById("btn-generate-draft");

  const editorSection = document.getElementById("briefing-editor-section");
  const briefingForm = document.getElementById("briefing-form");
  const briefingIdInput = document.getElementById("briefing-id");
  const briefingTitle = document.getElementById("briefing-title");
  const briefingReason = document.getElementById("briefing-reason");
  const briefingSymptoms = document.getElementById("briefing-symptoms");
  const briefingVitals = document.getElementById("briefing-vitals");
  const briefingAllergies = document.getElementById("briefing-allergies");
  const briefingMedicines = document.getElementById("briefing-medicines");
  const briefingQuestions = document.getElementById("briefing-questions");
  const briefingNotes = document.getElementById("briefing-notes");
  const statusBox = document.getElementById("briefing-status-box");

  const btnNewBriefing = document.getElementById("btn-new-briefing");
  const btnCancelEdit = document.getElementById("btn-cancel-edit");
  const btnPrint = document.getElementById("btn-print-briefing");
  const btnShareModal = document.getElementById("btn-share-modal");

  const listContainer = document.getElementById("briefings-list-container");

  // Share modal elements
  const shareModal = document.getElementById("share-modal-overlay");
  const btnCloseShareModal = document.getElementById("btn-close-share-modal");
  const shareForm = document.getElementById("share-form");
  const shareRecipientName = document.getElementById("share-recipient-name");
  const shareDuration = document.getElementById("share-duration");
  const sharePin = document.getElementById("share-pin");
  const shareResultContainer = document.getElementById("share-result-container");
  const shareLinkUrl = document.getElementById("share-link-url");
  const btnCopyShareUrl = document.getElementById("btn-copy-share-url");

  let currentBriefings = [];
  let activeShareBriefingId = null;

  function formatDate(dStr) {
    if (!dStr) return "Date unrecorded";
    try {
      return new Date(dStr).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
    } catch {
      return String(dStr);
    }
  }

  // 1. Auto-generate Draft
  draftForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const reason = draftReason.value.trim();
    if (!reason) return;

    btnGenerateDraft.disabled = true;
    btnGenerateDraft.textContent = "Synthesizing Records…";

    try {
      const draft = await briefings.draft(reason);

      briefingIdInput.value = "";
      briefingTitle.value = draft.title;
      briefingReason.value = draft.visit_reason;
      briefingSymptoms.value = draft.symptoms_summary;
      briefingVitals.value = draft.vitals_summary;
      briefingAllergies.value = draft.allergies_summary;
      briefingMedicines.value = draft.medicines_summary;
      briefingQuestions.value = draft.questions_to_ask;
      briefingNotes.value = draft.notes;

      statusBox.style.display = "none";
      editorSection.style.display = "block";
      editorSection.scrollIntoView({ behavior: "smooth" });

      if (window.HR_UI && window.HR_UI.showToast) {
        window.HR_UI.showToast("Synthesized clinical briefing draft from your records!", "success");
      }
    } catch (err) {
      if (window.HR_UI && window.HR_UI.showToast) {
        window.HR_UI.showToast(`Draft generation failed: ${err.message}`, "error");
      }
    } finally {
      btnGenerateDraft.disabled = false;
      btnGenerateDraft.textContent = "⚡ Auto-Generate from Records";
    }
  });

  // 2. Open Blank Briefing
  btnNewBriefing.addEventListener("click", () => {
    briefingIdInput.value = "";
    briefingTitle.value = "Physician Consultation Briefing";
    briefingReason.value = "";
    briefingSymptoms.value = "";
    briefingVitals.value = "";
    briefingAllergies.value = "";
    briefingMedicines.value = "";
    briefingQuestions.value = "";
    briefingNotes.value = "";
    statusBox.style.display = "none";
    editorSection.style.display = "block";
    editorSection.scrollIntoView({ behavior: "smooth" });
  });

  btnCancelEdit.addEventListener("click", () => {
    editorSection.style.display = "none";
  });

  // 3. Save Briefing
  briefingForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = briefingTitle.value.trim();
    const reason = briefingReason.value.trim();
    if (!title || !reason) {
      statusBox.style.display = "flex";
      statusBox.className = "form-state-box error";
      statusBox.textContent = "Title and visit reason are required.";
      return;
    }

    const payload = {
      title,
      visit_reason: reason,
      symptoms_summary: briefingSymptoms.value.trim() || null,
      vitals_summary: briefingVitals.value.trim() || null,
      allergies_summary: briefingAllergies.value.trim() || null,
      medicines_summary: briefingMedicines.value.trim() || null,
      questions_to_ask: briefingQuestions.value.trim() || null,
      notes: briefingNotes.value.trim() || null
    };

    statusBox.style.display = "flex";
    statusBox.className = "form-state-box info";
    statusBox.textContent = "Saving briefing to patient record…";

    try {
      const existingId = briefingIdInput.value;
      let saved;
      if (existingId) {
        saved = await briefings.update(existingId, payload);
      } else {
        saved = await briefings.create(payload);
        briefingIdInput.value = saved.id;
      }

      statusBox.className = "form-state-box success";
      statusBox.innerHTML = `<span>✓</span><span>Briefing saved successfully!</span>`;

      if (window.HR_UI && window.HR_UI.showToast) {
        window.HR_UI.showToast("Briefing saved to records!", "success");
      }

      await loadBriefings();
    } catch (err) {
      statusBox.className = "form-state-box error";
      statusBox.textContent = `Save failed: ${err.message}`;
    }
  });

  // 4. Print / PDF Export
  btnPrint.addEventListener("click", () => {
    window.print();
  });

  // 5. Secure Share Modal Setup
  btnShareModal.addEventListener("click", () => {
    const id = briefingIdInput.value;
    if (!id) {
      alert("Please save the briefing before generating a sharing link.");
      return;
    }
    openShareModal(id);
  });

  function openShareModal(briefingId) {
    activeShareBriefingId = briefingId;
    shareRecipientName.value = "Dr. ";
    sharePin.value = "";
    shareResultContainer.style.display = "none";
    shareModal.style.display = "flex";
  }

  btnCloseShareModal.addEventListener("click", () => {
    shareModal.style.display = "none";
  });

  shareForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!activeShareBriefingId) return;

    const payload = {
      recipient_name: shareRecipientName.value.trim() || "Physician",
      duration_hours: parseInt(shareDuration.value, 10) || 72,
      access_pin: sharePin.value.trim() || null
    };

    try {
      const shareData = await briefings.share(activeShareBriefingId, payload);
      const origin = window.location.origin;
      const shareUrl = `${origin}/share.html?token=${encodeURIComponent(shareData.share_token)}`;

      shareLinkUrl.textContent = shareUrl;
      shareResultContainer.style.display = "block";

      if (window.HR_UI && window.HR_UI.showToast) {
        window.HR_UI.showToast("Secure shareable link created!", "success");
      }
      await loadBriefings();
    } catch (err) {
      alert(`Sharing failed: ${err.message}`);
    }
  });

  btnCopyShareUrl.addEventListener("click", () => {
    const text = shareLinkUrl.textContent;
    navigator.clipboard.writeText(text).then(() => {
      btnCopyShareUrl.textContent = "Copied!";
      setTimeout(() => btnCopyShareUrl.textContent = "Copy Link", 2000);
    });
  });

  // 6. List Briefings
  async function loadBriefings() {
    try {
      currentBriefings = await briefings.list();
      renderBriefingsList();
    } catch (err) {
      listContainer.innerHTML = `<p style="color:var(--text-muted)">Failed to load briefings: ${esc(err.message)}</p>`;
    }
  }

  function renderBriefingsList() {
    if (currentBriefings.length === 0) {
      listContainer.innerHTML = `
        <div class="glass" style="text-align:center;padding:2.5rem 1rem;border-radius:14px">
          <p style="color:var(--text-muted);margin:0 0 1rem">No doctor-visit briefings prepared yet.</p>
          <p style="font-size:.85rem;color:var(--text-muted)">Use the auto-synthesizer above to generate your first appointment summary.</p>
        </div>
      `;
      return;
    }

    listContainer.innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1.2rem">
        ${currentBriefings.map(b => {
          const activeShares = (b.shares || []).filter(s => !s.is_revoked);

          return `
            <div class="glass tilt" style="padding:1.4rem;border-radius:14px;display:flex;flex-direction:column;justify-content:space-between">
              <div>
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.5rem">
                  <span style="font-size:.8rem;color:var(--text-muted)">${formatDate(b.created_at)}</span>
                  <span class="status-pill info">${b.shares?.length || 0} Shares</span>
                </div>
                <h3 style="margin:0 0 .4rem;font-size:1.15rem;color:var(--text-main)">${esc(b.title)}</h3>
                <p style="font-size:.88rem;color:var(--text-secondary);margin:0 0 1rem"><strong>Reason:</strong> ${esc(b.visit_reason)}</p>
              </div>

              <div>
                ${activeShares.length > 0 ? `
                  <div style="margin-bottom:.8rem;padding:.5rem .8rem;border-radius:8px;background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.2);font-size:.78rem;color:#6ee7b7">
                    <span>Active Share Link: ${activeShares[0].recipient_name || 'Physician'} (${activeShares[0].view_count} views)</span>
                    <button class="btn-revoke-share" data-token="${activeShares[0].share_token}" style="background:transparent;border:none;color:#f87171;font-weight:700;cursor:pointer;margin-left:.5rem;text-decoration:underline">Revoke</button>
                  </div>
                ` : ''}

                <div style="display:flex;gap:.5rem;flex-wrap:wrap">
                  <button class="btn btn-sm btn-edit-briefing" data-id="${b.id}">Edit</button>
                  <button class="btn btn-sm btn-print-briefing-card" data-id="${b.id}">Print</button>
                  <button class="btn btn-sm btn-share-briefing-card" data-id="${b.id}" style="color:var(--primary);border-color:var(--primary)">Share</button>
                  <button class="btn btn-sm btn-del-briefing" data-id="${b.id}" style="color:#f87171">Delete</button>
                </div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;

    // Bind item buttons
    listContainer.querySelectorAll(".btn-edit-briefing").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = parseInt(btn.dataset.id, 10);
        const b = currentBriefings.find(x => x.id === id);
        if (b) {
          briefingIdInput.value = b.id;
          briefingTitle.value = b.title;
          briefingReason.value = b.visit_reason;
          briefingSymptoms.value = b.symptoms_summary || "";
          briefingVitals.value = b.vitals_summary || "";
          briefingAllergies.value = b.allergies_summary || "";
          briefingMedicines.value = b.medicines_summary || "";
          briefingQuestions.value = b.questions_to_ask || "";
          briefingNotes.value = b.notes || "";
          statusBox.style.display = "none";
          editorSection.style.display = "block";
          editorSection.scrollIntoView({ behavior: "smooth" });
        }
      });
    });

    listContainer.querySelectorAll(".btn-print-briefing-card").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = parseInt(btn.dataset.id, 10);
        const b = currentBriefings.find(x => x.id === id);
        if (b) {
          briefingIdInput.value = b.id;
          briefingTitle.value = b.title;
          briefingReason.value = b.visit_reason;
          briefingSymptoms.value = b.symptoms_summary || "";
          briefingVitals.value = b.vitals_summary || "";
          briefingAllergies.value = b.allergies_summary || "";
          briefingMedicines.value = b.medicines_summary || "";
          briefingQuestions.value = b.questions_to_ask || "";
          briefingNotes.value = b.notes || "";
          editorSection.style.display = "block";
          window.print();
        }
      });
    });

    listContainer.querySelectorAll(".btn-share-briefing-card").forEach(btn => {
      btn.addEventListener("click", () => {
        openShareModal(parseInt(btn.dataset.id, 10));
      });
    });

    listContainer.querySelectorAll(".btn-del-briefing").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = parseInt(btn.dataset.id, 10);
        if (confirm("Delete this doctor briefing and revoke all active share links?")) {
          try {
            await briefings.delete(id);
            if (briefingIdInput.value == id) {
              editorSection.style.display = "none";
            }
            if (window.HR_UI && window.HR_UI.showToast) {
              window.HR_UI.showToast("Briefing deleted.", "info");
            }
            await loadBriefings();
          } catch (err) {
            alert(`Delete failed: ${err.message}`);
          }
        }
      });
    });

    listContainer.querySelectorAll(".btn-revoke-share").forEach(btn => {
      btn.addEventListener("click", async () => {
        const token = btn.dataset.token;
        if (confirm("Revoke this active link immediately? Clinicians will no longer be able to access the briefing.")) {
          try {
            await briefings.revokeShare(token);
            if (window.HR_UI && window.HR_UI.showToast) {
              window.HR_UI.showToast("Access revoked immediately.", "info");
            }
            await loadBriefings();
          } catch (err) {
            alert(`Revocation failed: ${err.message}`);
          }
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (window.HR_UI && window.HR_UI.ensureAuth) {
      window.HR_UI.ensureAuth("manage your doctor visit briefings", loadBriefings);
    } else {
      loadBriefings();
    }
  });
})();

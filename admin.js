/**
 * Logic for Private Admin Database & Login Activity Monitor (admin.html)
 */
(() => {
  "use strict";

  const { auth } = window.HR_API;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const pillUsersBtn = document.getElementById("pill-users-btn");
  const pillLoginsBtn = document.getElementById("pill-logins-btn");
  const sectionUsers = document.getElementById("section-users");
  const sectionLogins = document.getElementById("section-logins");
  const refreshBtn = document.getElementById("refresh-all-btn");

  const statTotalUsers = document.getElementById("stat-total-users");
  const statTotalLogins = document.getElementById("stat-total-logins");
  const statServerStatus = document.getElementById("stat-server-status");

  const usersTbody = document.getElementById("admin-users-tbody");
  const loginsTbody = document.getElementById("admin-logins-tbody");

  // Tab switching
  pillUsersBtn.addEventListener("click", () => {
    pillUsersBtn.classList.add("active");
    pillLoginsBtn.classList.remove("active");
    sectionUsers.style.display = "block";
    sectionLogins.style.display = "none";
  });

  pillLoginsBtn.addEventListener("click", () => {
    pillLoginsBtn.classList.add("active");
    pillUsersBtn.classList.remove("active");
    sectionLogins.style.display = "block";
    sectionUsers.style.display = "none";
  });

  function formatDate(isoStr) {
    if (!isoStr) return "-";
    try {
      const dt = new Date(isoStr);
      return dt.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return isoStr;
    }
  }

  async function loadData() {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Loading...";

    try {
      // 1. Load registered users
      const users = await auth.listUsers();
      statTotalUsers.textContent = users.length;
      statServerStatus.textContent = "Online";
      statServerStatus.style.color = "var(--low)";

      if (!users.length) {
        usersTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:1.5rem;color:var(--mute)">No accounts in health_risk.db yet.</td></tr>`;
      } else {
        usersTbody.innerHTML = users.map(u => `
          <tr>
            <td style="font-weight:700;color:var(--aqua)">#${esc(u.id)}</td>
            <td style="font-weight:600">${esc(u.name)}</td>
            <td style="color:var(--mute);font-family:monospace">${esc(u.email)}</td>
            <td style="color:var(--mute)">${formatDate(u.created_at)}</td>
            <td>
              <span class="status-badge-ok">✓ Accepted & Active</span>
            </td>
            <td>
              <span class="pill-chip">${u.assessments_count !== undefined ? u.assessments_count : (u.profile ? "Profile Active" : "0")}</span>
            </td>
          </tr>
        `).join("");
      }

      // 2. Load login event history
      try {
        const logins = await auth.getLoginHistory();
        statTotalLogins.textContent = logins.length;

        if (!logins.length) {
          loginsTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:1.5rem;color:var(--mute)">No login events logged yet.</td></tr>`;
        } else {
          loginsTbody.innerHTML = logins.map(l => {
            const isOk = l.status === "SUCCESS";
            return `
              <tr>
                <td style="color:var(--mute)">#${esc(l.id)}</td>
                <td style="font-weight:600;color:${l.activity_type === "REGISTER" ? "var(--aqua)" : "var(--blue)"}">
                  ${esc(l.activity_type)}
                </td>
                <td style="font-family:monospace">${esc(l.email)}</td>
                <td>${esc(l.name || "-")}</td>
                <td style="color:var(--mute)">${formatDate(l.timestamp)}</td>
                <td>
                  <span class="${isOk ? "status-badge-ok" : "status-badge-failed"}">
                    ${isOk ? "✓ SUCCESS" : "⚠ FAILED"}
                  </span>
                </td>
              </tr>
            `;
          }).join("");
        }
      } catch (logErr) {
        statTotalLogins.textContent = "-";
        loginsTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--mute);padding:1.5rem">Login tracking table initialized. Events will record on next sign in.</td></tr>`;
      }

    } catch (err) {
      statServerStatus.textContent = "Offline";
      statServerStatus.style.color = "var(--crit)";
      usersTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#ff9aa9;padding:1.5rem">Error: Could not connect to backend server. Make sure FastAPI is running.</td></tr>`;
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "🔄 Refresh Data";
    }
  }

  refreshBtn.addEventListener("click", loadData);
  loadData();
})();

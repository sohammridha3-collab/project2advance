/**
 * Shared UI & Navigation Helper: Auth Modal, Toast Notifications, and Topbar Integration
 */
(() => {
  "use strict";

  const { auth } = window.HR_API;
  const currentPath = window.location.pathname.split("/").pop() || "index.html";
  const isAuthPage = currentPath === "login.html";
  const isAdminPage = currentPath === "admin.html";

  // ROUTE GUARD: Ensure login/register is shown before home page or any clinical view.
  if (!auth.isAuthenticated() && !isAuthPage && !isAdminPage) {
    window.location.replace("login.html");
    return;
  }
  if (auth.isAuthenticated() && isAuthPage) {
    window.location.replace("index.html");
    return;
  }

  // Toast container setup
  let toastContainer = document.querySelector(".toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);
  }

  function showToast(message, type = "info", duration = 4000) {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "✓" : type === "error" ? "⚠" : "ℹ";
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // Navigation Links update across all pages
  function setupNavigation() {
    const menu = document.getElementById("menu");
    if (!menu) return;

    // Standard clinical application pages
    const links = [
      { href: "index.html", text: "Dashboard" },
      { href: "history.html", text: "Health History" },
      { href: "prescription.html", text: "Prescription Vault" },
      { href: "allergies.html", text: "Allergies" },
      { href: "problems.html", text: "Symptom Log" },
      { href: "recommendation.html", text: "Recommendations" }
    ];

    if (currentPath === "result.html") {
      links.splice(5, 0, { href: "result.html", text: "Assessment Result" });
    }

    // Rebuild menu links while preserving current highlight
    menu.innerHTML = links.map(l => {
      const isCur = currentPath === l.href;
      const attr = isCur ? 'aria-current="page" class="active"' : "";
      return `<a href="${l.href}" ${attr}>${l.text}</a>`;
    }).join("");

    // Add Auth Widget to topbar
    const topbar = document.querySelector(".topbar");
    if (topbar && !document.querySelector(".auth-nav")) {
      const authNav = document.createElement("div");
      authNav.className = "auth-nav";
      authNav.id = "auth-widget";
      topbar.appendChild(authNav);
      renderAuthWidget();
    }
  }

  function renderAuthWidget() {
    const container = document.getElementById("auth-widget");
    if (!container) return;

    const user = auth.getUser();
    if (user) {
      const initial = (user.name || "P").trim().charAt(0).toUpperCase();
      const firstName = (user.name || "Patient").trim().split(" ")[0];
      container.innerHTML = `
        <div class="user-badge" title="Authenticated account: ${user.email}">
          <span class="user-avatar-circle">${initial}</span>
          <span>${firstName}</span>
        </div>
        <button id="logout-btn" class="btn btn-sm btn-logout" type="button" title="Sign out from session" aria-label="Sign out">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          <span>Sign Out</span>
        </button>
      `;
      document.getElementById("logout-btn").addEventListener("click", () => {
        auth.logout();
        showToast("Signed out successfully.", "info");
        setTimeout(() => {
          window.location.replace("login.html");
        }, 200);
      });
    } else {
      container.innerHTML = "";
    }
  }

  // Auth Modal
  let activeModal = null;

  function openAuthModal(initialTab = "login", onComplete = null) {
    if (activeModal) activeModal.remove();

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="glass modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <button class="modal-close" type="button" aria-label="Close dialog">&times;</button>
        <h2 id="modal-title" style="margin:0;font-size:1.3rem">Account Access</h2>
        <p style="color:var(--mute);font-size:.88rem;margin-top:.2rem">Sign in to securely store your health assessments, prescriptions, and symptoms.</p>
        
        <div class="auth-tabs">
          <button class="auth-tab ${initialTab === 'login' ? 'active' : ''}" id="tab-login" type="button">Sign In</button>
          <button class="auth-tab ${initialTab === 'register' ? 'active' : ''}" id="tab-register" type="button">Register</button>
        </div>

        <form id="auth-form">
          <div id="name-field" style="display:${initialTab === 'register' ? 'grid' : 'none'};margin-bottom:1rem">
            <label style="font-size:.85rem;color:var(--mute);display:block;margin-bottom:.3rem">Full Name</label>
            <input type="text" id="auth-name" placeholder="Alex Doe" style="width:100%;min-height:44px;padding:0 .9rem;border-radius:10px;border:1px solid var(--edge);background:rgba(8,16,34,.7);color:var(--text);box-sizing:border-box">
          </div>
          
          <div style="margin-bottom:1rem">
            <label style="font-size:.85rem;color:var(--mute);display:block;margin-bottom:.3rem">Email Address</label>
            <input type="email" id="auth-email" required placeholder="alex@example.com" style="width:100%;min-height:44px;padding:0 .9rem;border-radius:10px;border:1px solid var(--edge);background:rgba(8,16,34,.7);color:var(--text);box-sizing:border-box">
          </div>

          <div style="margin-bottom:1.2rem">
            <label style="font-size:.85rem;color:var(--mute);display:block;margin-bottom:.3rem">Password</label>
            <input type="password" id="auth-password" required placeholder="••••••••" style="width:100%;min-height:44px;padding:0 .9rem;border-radius:10px;border:1px solid var(--edge);background:rgba(8,16,34,.7);color:var(--text);box-sizing:border-box">
          </div>

          <button id="auth-submit-btn" class="btn p" type="submit" style="width:100%">${initialTab === 'register' ? 'Create Account' : 'Sign In'}</button>
          <p id="auth-error" class="err" style="margin-top:.7rem;font-size:.85rem;min-height:1.2em"></p>
        </form>

        <div class="quick-demo-box">
          <p>Want to test instantly without creating an account?</p>
          <button id="quick-demo-btn" class="btn btn-sm" type="button" style="width:100%">⚡ 1-Click Demo Patient Login</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    activeModal = overlay;

    let currentTab = initialTab;
    const tabLogin = overlay.querySelector("#tab-login");
    const tabRegister = overlay.querySelector("#tab-register");
    const nameField = overlay.querySelector("#name-field");
    const submitBtn = overlay.querySelector("#auth-submit-btn");
    const errBox = overlay.querySelector("#auth-error");
    const form = overlay.querySelector("#auth-form");

    function setTab(tab) {
      currentTab = tab;
      tabLogin.classList.toggle("active", tab === "login");
      tabRegister.classList.toggle("active", tab === "register");
      nameField.style.display = tab === "register" ? "grid" : "none";
      submitBtn.textContent = tab === "register" ? "Create Account" : "Sign In";
      errBox.textContent = "";
    }

    tabLogin.addEventListener("click", () => setTab("login"));
    tabRegister.addEventListener("click", () => setTab("register"));

    overlay.querySelector(".modal-close").addEventListener("click", () => {
      overlay.remove();
      activeModal = null;
    });

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.remove();
        activeModal = null;
      }
    });

    // 1-Click Demo Login
    overlay.querySelector("#quick-demo-btn").addEventListener("click", async () => {
      errBox.textContent = "";
      const btn = overlay.querySelector("#quick-demo-btn");
      btn.disabled = true;
      btn.textContent = "Logging in...";
      try {
        await auth.login("demo@health.io", "Demo123!", true);
        showToast("Signed in as Demo Patient!", "success");
        overlay.remove();
        activeModal = null;
        if (onComplete) onComplete();
      } catch (ex) {
        // If demo user wasn't registered yet, register it
        try {
          await auth.register("Demo Patient", "demo@health.io", "Demo123!");
          showToast("Demo Patient created & signed in!", "success");
          overlay.remove();
          activeModal = null;
          if (onComplete) onComplete();
        } catch (regEx) {
          errBox.textContent = regEx.message;
          btn.disabled = false;
          btn.textContent = "⚡ 1-Click Demo Patient Login";
        }
      }
    });

    // Form submit
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      errBox.textContent = "";
      const email = overlay.querySelector("#auth-email").value.trim();
      const password = overlay.querySelector("#auth-password").value;
      const name = overlay.querySelector("#auth-name").value.trim();

      submitBtn.disabled = true;
      submitBtn.textContent = "Please wait...";

      try {
        if (currentTab === "register") {
          if (!name) throw new Error("Full name is required.");
          await auth.register(name, email, password);
          showToast(`Welcome, ${name}! Account created.`, "success");
        } else {
          const user = await auth.login(email, password, true);
          showToast(`Welcome back, ${user.name}!`, "success");
        }
        overlay.remove();
        activeModal = null;
        if (onComplete) onComplete();
      } catch (err) {
        errBox.textContent = err.message;
        submitBtn.disabled = false;
        submitBtn.textContent = currentTab === "register" ? "Create Account" : "Sign In";
      }
    });
  }

  // Check auth state on startup
  async function initAuth() {
    if (!isAuthPage) {
      if (!auth.isAuthenticated()) {
        window.location.replace("login.html");
        return;
      }
      const me = await auth.getMe();
      if (!me && !auth.isAuthenticated()) {
        window.location.replace("login.html");
        return;
      }
    }
    setupNavigation();
    renderAuthWidget();
  }

  window.addEventListener("hr:auth_changed", (e) => {
    renderAuthWidget();
    if (!e.detail.user && !isAuthPage) {
      window.location.replace("login.html");
    }
  });

  // Ensure user is authenticated before executing action
  function ensureAuth(actionDesc = "perform this action", onReady) {
    if (auth.isAuthenticated()) {
      onReady(auth.getUser());
    } else {
      showToast(`Please sign in to ${actionDesc}.`, "info");
      setTimeout(() => {
        window.location.replace("login.html");
      }, 400);
    }
  }

  window.HR_UI = {
    showToast,
    openAuthModal,
    ensureAuth,
    setupNavigation,
    renderAuthWidget,
  };

  document.addEventListener("DOMContentLoaded", initAuth);
})();

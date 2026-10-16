/**
 * Shared UI & Navigation Helper: Auth Modal, Toast Notifications, and Topbar Integration
 */
(() => {
  "use strict";

  const { auth } = window.HR_API;
  const currentPath = window.location.pathname.split("/").pop() || "index.html";
  const isAuthPage = currentPath === "login.html";
  const isAdminPage = currentPath === "admin.html";
  const isPublicPage = ["index.html", "result.html", "login.html", "share.html", ""].includes(currentPath);

  // ROUTE GUARD: Ensure login is required only for private medical record pages.
  if (!auth.isAuthenticated() && !isPublicPage && !isAdminPage) {
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

    // Standard clinical application pages for HealthBridge AI
    const links = [
      { href: "index.html", text: "Dashboard" },
      { href: "timeline.html", text: "Timeline" },
      { href: "briefing.html", text: "Doctor Briefing" },
      { href: "prescription.html", text: "Prescription Vault" },
      { href: "recommendation.html", text: "Recommendations" },
      { href: "history.html", text: "Assessments" },
      { href: "allergies.html", text: "Allergies" },
      { href: "problems.html", text: "Symptom Log" }
    ];

    if (currentPath === "result.html") {
      links.splice(1, 0, { href: "result.html", text: "Current Result" });
    }

    // Set brand name to HealthBridge AI across all pages
    const brandSpan = document.querySelector(".brand span");
    if (brandSpan) {
      brandSpan.textContent = "HealthBridge AI";
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
      container.innerHTML = `
        <a href="login.html" class="btn btn-sm btn-login-nav" title="Sign in or register an account">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
            <line x1="15" y1="12" x2="3" y2="12"/>
          </svg>
          <span>Sign In</span>
        </a>
      `;
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
    if (!isPublicPage && !isAdminPage) {
      if (!auth.isAuthenticated()) {
        window.location.replace("login.html");
        return;
      }
      const me = await auth.getMe();
      if (!me && !auth.isAuthenticated()) {
        window.location.replace("login.html");
        return;
      }
    } else if (auth.isAuthenticated()) {
      // Validate session in background without blocking public page render
      auth.getMe().catch(() => {});
    }
    setupNavigation();
    renderAuthWidget();
  }

  window.addEventListener("hr:auth_changed", (e) => {
    renderAuthWidget();
    if (!e.detail.user && !isPublicPage && !isAdminPage) {
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

  // ============================================================
  // BACKEND CONNECTION HEALTH & AUTO-HEALING UI
  // ============================================================
  let statusBanner = null;
  let offlineGuideModal = null;

  function showBackendStatusBanner(isOnline, detail = {}) {
    if (!statusBanner) {
      statusBanner = document.createElement("div");
      statusBanner.id = "hr-backend-status-banner";
      statusBanner.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 100000;
        padding: 0.55rem 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.88rem;
        font-family: inherit;
        font-weight: 500;
        box-shadow: 0 4px 20px rgba(0,0,0,0.35);
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
        transform: translateY(0);
      `;
      document.body.prepend(statusBanner);
    }

    if (isOnline) {
      statusBanner.style.background = "linear-gradient(90deg, #065f46, #047857)";
      statusBanner.style.borderBottom = "1px solid #10b981";
      statusBanner.style.color = "#ecfdf5";
      statusBanner.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.6rem">
          <span style="font-size:1.1rem">✓</span>
          <span><strong>FastAPI Connected:</strong> Backend server is online at <code>${detail.base || "http://127.0.0.1:8000"}</code></span>
        </div>
        <button type="button" id="dismiss-status-banner-btn" style="background:transparent;border:none;color:#ecfdf5;cursor:pointer;font-size:1.1rem;padding:0 0.3rem" title="Dismiss">✕</button>
      `;
      const dismissBtn = document.getElementById("dismiss-status-banner-btn");
      if (dismissBtn) {
        dismissBtn.addEventListener("click", () => {
          statusBanner.style.display = "none";
        });
      }
      setTimeout(() => {
        if (statusBanner && statusBanner.style.display !== "none") {
          statusBanner.style.opacity = "0";
          statusBanner.style.transform = "translateY(-100%)";
          setTimeout(() => {
            if (statusBanner) statusBanner.style.display = "none";
          }, 300);
        }
      }, 3500);
    } else {
      statusBanner.style.display = "flex";
      statusBanner.style.opacity = "1";
      statusBanner.style.transform = "translateY(0)";
      statusBanner.style.background = "linear-gradient(90deg, #991b1b, #b91c1c)";
      statusBanner.style.borderBottom = "1px solid #ef4444";
      statusBanner.style.color = "#fef2f2";
      statusBanner.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap">
          <span style="font-size:1.1rem">⚠️</span>
          <span><strong>Backend Offline:</strong> Cannot connect to FastAPI on <code>127.0.0.1:8000</code>. Retrying automatically...</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.5rem">
          <button type="button" id="retry-backend-btn" style="background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.4);color:#fff;padding:0.25rem 0.65rem;border-radius:6px;cursor:pointer;font-size:0.8rem;font-weight:600">⚡ Check Now</button>
          <button type="button" id="help-backend-btn" style="background:#fff;border:none;color:#991b1b;padding:0.25rem 0.65rem;border-radius:6px;cursor:pointer;font-size:0.8rem;font-weight:600">🛠️ How to Start</button>
        </div>
      `;

      const retryBtn = document.getElementById("retry-backend-btn");
      if (retryBtn) {
        retryBtn.addEventListener("click", async () => {
          retryBtn.textContent = "Checking...";
          const h = await window.HR_API.checkHealth();
          if (h.online) {
            showToast("Backend reconnected successfully!", "success");
          } else {
            retryBtn.textContent = "Offline (Retrying...)";
            setTimeout(() => { retryBtn.textContent = "⚡ Check Now"; }, 2000);
          }
        });
      }

      const helpBtn = document.getElementById("help-backend-btn");
      if (helpBtn) {
        helpBtn.addEventListener("click", openBackendHelpModal);
      }
    }
  }

  function openBackendHelpModal() {
    if (offlineGuideModal) offlineGuideModal.remove();

    offlineGuideModal = document.createElement("div");
    offlineGuideModal.className = "modal-overlay";
    offlineGuideModal.innerHTML = `
      <div class="glass modal-card" role="dialog" aria-modal="true" style="max-width:560px;padding:1.8rem;text-align:left">
        <button class="modal-close" id="close-backend-modal" type="button" aria-label="Close dialog">&times;</button>
        <h2 style="margin:0 0 0.5rem 0;font-size:1.35rem;display:flex;align-items:center;gap:0.5rem">
          <span>🛠️</span> FastAPI Backend Server Offline
        </h2>
        <p style="color:var(--mute);font-size:0.9rem;line-height:1.5;margin-bottom:1.2rem">
          The web application requires the Python FastAPI backend running on <code>http://127.0.0.1:8000</code> to process predictions, medical records, and database storage.
        </p>

        <div style="background:rgba(255,255,255,0.04);border:1px solid var(--edge);border-radius:10px;padding:1rem;margin-bottom:1rem">
          <strong style="color:var(--primary,#4f46e5);display:block;margin-bottom:0.4rem;font-size:0.92rem">
            Option 1: 1-Click Launch (Recommended)
          </strong>
          <p style="font-size:0.86rem;color:var(--text);margin:0 0 0.5rem 0">
            In your project folder, double-click:
          </p>
          <div style="display:flex;gap:0.5rem;align-items:center">
            <code style="background:rgba(0,0,0,0.4);padding:0.4rem 0.8rem;border-radius:6px;font-weight:600;color:#60a5fa">run_app.bat</code>
            <span style="font-size:0.82rem;color:var(--mute)">or</span>
            <code style="background:rgba(0,0,0,0.4);padding:0.4rem 0.8rem;border-radius:6px;font-weight:600;color:#60a5fa">run_backend.bat</code>
          </div>
        </div>

        <div style="background:rgba(255,255,255,0.04);border:1px solid var(--edge);border-radius:10px;padding:1rem;margin-bottom:1.2rem">
          <strong style="color:var(--primary,#4f46e5);display:block;margin-bottom:0.4rem;font-size:0.92rem">
            Option 2: Terminal Command
          </strong>
          <p style="font-size:0.86rem;color:var(--text);margin:0 0 0.5rem 0">
            Open PowerShell or CMD in the project folder and run:
          </p>
          <code style="display:block;background:rgba(0,0,0,0.4);padding:0.5rem 0.8rem;border-radius:6px;font-weight:600;color:#34d399">
            python -m uvicorn main:app --host 127.0.0.1 --port 8000
          </code>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:0.8rem">
          <button id="test-connection-btn" class="btn p" type="button" style="padding:0.6rem 1.2rem">
            ⚡ Test Connection Now
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(offlineGuideModal);

    document.getElementById("close-backend-modal").addEventListener("click", () => {
      offlineGuideModal.remove();
      offlineGuideModal = null;
    });

    offlineGuideModal.addEventListener("click", (e) => {
      if (e.target === offlineGuideModal) {
        offlineGuideModal.remove();
        offlineGuideModal = null;
      }
    });

    document.getElementById("test-connection-btn").addEventListener("click", async () => {
      const btn = document.getElementById("test-connection-btn");
      btn.textContent = "Testing...";
      const health = await window.HR_API.checkHealth();
      if (health.online) {
        showToast("Backend is online! Closing...", "success");
        setTimeout(() => {
          if (offlineGuideModal) {
            offlineGuideModal.remove();
            offlineGuideModal = null;
          }
        }, 1000);
      } else {
        btn.textContent = "Still Offline (Check Terminal)";
        setTimeout(() => { btn.textContent = "⚡ Test Connection Now"; }, 2500);
      }
    });
  }

  window.addEventListener("hr:backend_offline", (e) => {
    showBackendStatusBanner(false, e.detail);
  });

  window.addEventListener("hr:backend_online", (e) => {
    showBackendStatusBanner(true, e.detail);
  });

  window.HR_UI = {
    showToast,
    openAuthModal,
    ensureAuth,
    setupNavigation,
    renderAuthWidget,
    showBackendStatusBanner,
    openBackendHelpModal,
  };

  document.addEventListener("DOMContentLoaded", () => {
    initAuth();
    if (window.HR_API && window.HR_API.checkHealth) {
      window.HR_API.checkHealth().then(h => {
        if (!h.online) {
          showBackendStatusBanner(false, h);
        }
      });
    }
  });
})();

/**
 * Logic for Patient & Doctor Authentication Portal (Sign In & Register)
 */
(() => {
  "use strict";

  const getAuth = () => (window.HR_API ? window.HR_API.auth : null);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // If already logged in with a valid token, verify with backend before redirecting
  const checkInitialAuth = async () => {
    const auth = getAuth();
    if (!auth || !auth.isAuthenticated()) return;
    try {
      const user = await auth.getMe();
      if (user) {
        window.location.replace("index.html");
      } else {
        auth.logout();
      }
    } catch {
      if (auth) auth.logout();
    }
  };

  // Run initial token verification safely
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", checkInitialAuth);
  } else {
    checkInitialAuth();
  }

  const tabLoginBtn = document.getElementById("tab-login-btn");
  const tabRegisterBtn = document.getElementById("tab-register-btn");
  const registerFields = document.getElementById("register-fields");
  const authForm = document.getElementById("portal-auth-form");
  const inputName = document.getElementById("input-name");
  const inputEmail = document.getElementById("input-email");
  const inputPassword = document.getElementById("input-password");
  const authMainBtn = document.getElementById("auth-main-btn");
  const statusBox = document.getElementById("auth-status-box");
  const quickDemoBtn = document.getElementById("quick-demo-login-btn");

  let currentMode = "login"; // 'login' or 'register'

  function setMode(mode) {
    currentMode = mode;
    statusBox.style.display = "none";
    statusBox.className = "form-state-box";

    if (mode === "register") {
      tabRegisterBtn.classList.add("active");
      tabLoginBtn.classList.remove("active");
      registerFields.style.display = "block";
      authMainBtn.textContent = "Create Account & Enter Dashboard \u2192";
    } else {
      tabLoginBtn.classList.add("active");
      tabRegisterBtn.classList.remove("active");
      registerFields.style.display = "none";
      authMainBtn.textContent = "Sign In to Dashboard \u2192";
    }
  }

  tabLoginBtn.addEventListener("click", () => setMode("login"));
  tabRegisterBtn.addEventListener("click", () => setMode("register"));

  // Form submit (Sign In or Register)
  authForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const auth = getAuth();
    if (!auth) {
      statusBox.style.display = "flex";
      statusBox.className = "form-state-box error";
      statusBox.innerHTML = `<span>\u26a0</span><span>API client is not ready. Please refresh the page.</span>`;
      return;
    }

    const email = inputEmail.value.trim();
    const password = inputPassword.value;
    const name = inputName.value.trim();

    if (!email || !password) {
      statusBox.style.display = "flex";
      statusBox.className = "form-state-box error";
      statusBox.innerHTML = `<span>\u26a0</span><span>Please enter both email and password.</span>`;
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      statusBox.style.display = "flex";
      statusBox.className = "form-state-box error";
      statusBox.innerHTML = `<span>\u26a0</span><span>Please enter a valid email address (e.g. name@example.com).</span>`;
      inputEmail.focus();
      return;
    }

    if (currentMode === "register") {
      if (!name || name.length < 2) {
        statusBox.style.display = "flex";
        statusBox.className = "form-state-box error";
        statusBox.innerHTML = `<span>\u26a0</span><span>Please enter your full name (at least 2 characters).</span>`;
        inputName.focus();
        return;
      }
      if (password.length < 6) {
        statusBox.style.display = "flex";
        statusBox.className = "form-state-box error";
        statusBox.innerHTML = `<span>\u26a0</span><span>Password must be at least 6 characters long.</span>`;
        inputPassword.focus();
        return;
      }
    }

    authMainBtn.disabled = true;
    authMainBtn.textContent = currentMode === "register" ? "Creating Account..." : "Authenticating...";
    statusBox.style.display = "flex";
    statusBox.className = "form-state-box info";
    statusBox.innerHTML = `<span>\u23f3</span><span>Connecting to backend database...</span>`;

    try {
      if (currentMode === "register") {
        await auth.register(name, email, password);
        statusBox.className = "form-state-box success";
        statusBox.innerHTML = `<span>\u2713</span><span>Account created successfully! Welcome, ${esc(name)}. Redirecting to Home...</span>`;
        if (window.HR_UI && window.HR_UI.showToast) {
          window.HR_UI.showToast(`Account registered successfully for ${name}!`, "success");
        }
        setTimeout(() => {
          window.location.replace("index.html");
        }, 600);
      } else {
        const user = await auth.login(email, password, true);
        statusBox.className = "form-state-box success";
        statusBox.innerHTML = `<span>\u2713</span><span>Welcome back, ${esc(user.name)}! Redirecting to Home...</span>`;
        if (window.HR_UI && window.HR_UI.showToast) {
          window.HR_UI.showToast(`Signed in as ${user.name}!`, "success");
        }
        setTimeout(() => {
          window.location.replace("index.html");
        }, 500);
      }
    } catch (err) {
      statusBox.className = "form-state-box error";
      const cleanMsg = err && err.message ? err.message : "Authentication failed. Please verify your credentials.";
      statusBox.innerHTML = `<span>\u26a0</span><span>${esc(cleanMsg)}</span>`;
      authMainBtn.disabled = false;
      authMainBtn.textContent = currentMode === "register" ? "Create Account & Enter Dashboard \u2192" : "Sign In to Dashboard \u2192";
    }
  });

  // 1-Click Demo Login
  quickDemoBtn.addEventListener("click", async () => {
    const auth = getAuth();
    if (!auth) return;

    quickDemoBtn.disabled = true;
    quickDemoBtn.textContent = "Signing in as Demo Patient...";
    statusBox.style.display = "flex";
    statusBox.className = "form-state-box info";
    statusBox.innerHTML = `<span>\u23f3</span><span>Logging in with Demo Patient credentials...</span>`;

    try {
      let user;
      try {
        user = await auth.login("demo@health.io", "Demo123!", true);
      } catch {
        user = await auth.register("Demo Patient", "demo@health.io", "Demo123!");
      }
      statusBox.className = "form-state-box success";
      statusBox.innerHTML = `<span>\u2713</span><span>Logged in as ${esc(user.name)}! Entering dashboard...</span>`;
      if (window.HR_UI && window.HR_UI.showToast) {
        window.HR_UI.showToast("Signed in as Demo Patient!", "success");
      }
      setTimeout(() => {
        window.location.replace("index.html");
      }, 500);
    } catch (err) {
      statusBox.className = "form-state-box error";
      const cleanMsg = err && err.message ? err.message : "Demo sign in failed.";
      statusBox.innerHTML = `<span>\u26a0</span><span>${esc(cleanMsg)}</span>`;
      quickDemoBtn.disabled = false;
      quickDemoBtn.textContent = "\u26a1 1-Click Demo Patient Login";
    }
  });
})();

/**
 * Centralized API Client & Service Layer for AI Health Risk Prediction System
 * Communicates directly with FastAPI backend.
 */
(() => {
  "use strict";

  const getApiBase = () => {
    // 1. Explicit global configuration or build environment
    if (typeof window !== "undefined") {
      if (window.HEALTHBRIDGE_API_URL && typeof window.HEALTHBRIDGE_API_URL === "string") {
        return window.HEALTHBRIDGE_API_URL.replace(/\/$/, "");
      }
      if (window.__API_BASE__ && typeof window.__API_BASE__ === "string") {
        return window.__API_BASE__.replace(/\/$/, "");
      }
      // 2. Local storage override for custom testing
      try {
        const storedBase = localStorage.getItem("hr_api_base");
        if (storedBase && storedBase.startsWith("http")) {
          return storedBase.replace(/\/$/, "");
        }
      } catch {}

      // 3. HTML meta tag configuration
      try {
        const metaTag = document.querySelector('meta[name="api-base-url"]');
        if (metaTag && metaTag.content && metaTag.content.startsWith("http")) {
          return metaTag.content.replace(/\/$/, "");
        }
      } catch {}

      // 4. Inferred from current browser origin
      if (window.location && window.location.origin && window.location.origin.startsWith("http")) {
        // If loaded directly from FastAPI backend port 8000
        if (window.location.origin.includes(":8000")) {
          return window.location.origin;
        }
        // If loaded from dev server (e.g. port 5500, 3000, 5173) on a custom IP or host
        const hostname = window.location.hostname;
        if (hostname && hostname !== "localhost" && hostname !== "127.0.0.1") {
          return `${window.location.protocol}//${hostname}:8000`;
        }
      }
    }
    // 5. Default reliable local development fallback
    return "http://127.0.0.1:8000";
  };

  let currentApiBase = getApiBase();
  let isServerOnline = true;
  let pollIntervalId = null;

  function startAutoHealthPolling() {
    if (pollIntervalId) return;
    pollIntervalId = setInterval(async () => {
      try {
        const candidates = Array.from(new Set([
          currentApiBase,
          "http://127.0.0.1:8000",
          "http://localhost:8000"
        ]));
        for (const base of candidates) {
          const ctrl = new AbortController();
          const tid = setTimeout(() => ctrl.abort(), 2000);
          const res = await fetch(`${base}/health`, { signal: ctrl.signal }).catch(() => null);
          clearTimeout(tid);
          if (res && res.ok) {
            clearInterval(pollIntervalId);
            pollIntervalId = null;
            currentApiBase = base;
            isServerOnline = true;
            const data = await res.json().catch(() => ({}));
            window.dispatchEvent(new CustomEvent("hr:backend_online", { detail: { base, data } }));
            break;
          }
        }
      } catch {}
    }, 3000);
  }

  const TOKEN_KEY = "hr_auth_token";
  const USER_KEY = "hr_current_user";

  const getStoredToken = () => localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || "";
  const getStoredUser = () => {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY) || "null");
    } catch {
      return null;
    }
  };

  const setAuthData = (token, user, persist = true) => {
    const storage = persist ? localStorage : sessionStorage;
    storage.setItem(TOKEN_KEY, token);
    storage.setItem(USER_KEY, JSON.stringify(user));
  };

  const clearAuthData = () => {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(USER_KEY);
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  /**
   * Unified request handler with timeouts, bounded retry for transient network errors,
   * distinct error typing (401/403/404/422/500/network), and auto-healing.
   */
  async function request(endpoint, options = {}) {
    const isFullUrl = endpoint.startsWith("http");
    const headers = options.headers || {};

    const token = getStoredToken();
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const isFormData = options.body instanceof FormData;
    if (!isFormData && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const maxRetries = options.retry !== undefined ? options.retry : 2;
    const timeoutMs = options.timeoutMs || (isFormData ? 25000 : 12000);

    let lastError = null;
    let response = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      const url = isFullUrl ? endpoint : `${currentApiBase}${endpoint}`;
      const controller = new AbortController();
      const timerId = setTimeout(() => controller.abort(), timeoutMs);

      try {
        response = await fetch(url, {
          ...options,
          headers,
          signal: options.signal || controller.signal,
        });
        clearTimeout(timerId);

        if (!isServerOnline) {
          isServerOnline = true;
          window.dispatchEvent(new CustomEvent("hr:backend_online", { detail: { base: currentApiBase } }));
        }
        break; // Successfully received HTTP response
      } catch (networkError) {
        clearTimeout(timerId);
        lastError = networkError;

        // Try loopback alternate (127.0.0.1 <-> localhost) if on Windows default
        if (!isFullUrl && attempt === 0 && (currentApiBase.includes("127.0.0.1") || currentApiBase.includes("localhost"))) {
          const altBase = currentApiBase.includes("127.0.0.1")
            ? currentApiBase.replace("127.0.0.1", "localhost")
            : currentApiBase.replace("localhost", "127.0.0.1");
          try {
            const altController = new AbortController();
            const altTimerId = setTimeout(() => altController.abort(), 2500);
            const altRes = await fetch(`${altBase}${endpoint}`, {
              ...options,
              headers,
              signal: altController.signal,
            });
            clearTimeout(altTimerId);
            currentApiBase = altBase;
            response = altRes;
            if (!isServerOnline) {
              isServerOnline = true;
              window.dispatchEvent(new CustomEvent("hr:backend_online", { detail: { base: currentApiBase } }));
            }
            break;
          } catch {}
        }

        // Bounded backoff retry only for genuinely transient network/socket glitches
        if (attempt < maxRetries) {
          const backoff = (attempt + 1) * 350;
          await sleep(backoff);
          continue;
        }
      }
    }

    // Network connection completely failed after retries
    if (!response) {
      isServerOnline = false;
      window.dispatchEvent(new CustomEvent("hr:backend_offline", { detail: { base: currentApiBase } }));
      startAutoHealthPolling();
      const err = new Error(`Cannot connect to backend server at ${currentApiBase}. Please ensure FastAPI is running.`);
      err.isNetwork = true;
      err.network = true;
      err.apiBase = currentApiBase;
      err.originalError = lastError;
      throw err;
    }

    if (response.status === 204) {
      return null;
    }

    const contentType = response.headers.get("content-type") || "";
    let data;
    if (contentType.includes("application/json")) {
      data = await response.json().catch(() => ({}));
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let message = `Request failed (${response.status})`;
      if (typeof data === "object" && data !== null) {
        if (Array.isArray(data.detail)) {
          message = data.detail.map((d) => `${d.loc ? d.loc.slice(1).join(".") + ": " : ""}${d.msg}`).join("; ");
        } else if (data.detail) {
          message = data.detail;
        } else if (data.message) {
          message = data.message;
        }
      }

      // Handle specific HTTP error categories distinctly
      if (response.status === 401) {
        clearAuthData();
        window.dispatchEvent(new CustomEvent("hr:auth_changed", { detail: { user: null, expired: true } }));
        message = "Your session has expired or authentication credentials are invalid. Please sign in again.";
      } else if (response.status === 403) {
        message = data.detail || "You do not have permission to access or modify this medical record.";
      } else if (response.status === 404) {
        message = data.detail || "Requested medical record or endpoint could not be found.";
      } else if (response.status >= 500) {
        message = data.detail || "The backend server encountered an error processing your request. Please try again.";
      }

      const err = new Error(message);
      err.status = response.status;
      err.data = data;
      err.isAuth = response.status === 401;
      err.isForbidden = response.status === 403;
      err.isNotFound = response.status === 404;
      err.isValidation = response.status === 422;
      err.isServerError = response.status >= 500;
      err.isNetwork = false;
      throw err;
    }

    return data;
  }

  // API Domain modules
  const api = {
    get BASE_URL() {
      return currentApiBase;
    },
    set BASE_URL(val) {
      currentApiBase = val;
    },

    /**
     * Actively probe the backend server health across loopback interfaces
     */
    async checkHealth() {
      const candidates = Array.from(new Set([
        currentApiBase,
        "http://127.0.0.1:8000",
        "http://localhost:8000"
      ]));

      for (const base of candidates) {
        try {
          const ctrl = new AbortController();
          const tid = setTimeout(() => ctrl.abort(), 2000);
          const res = await fetch(`${base}/health`, { signal: ctrl.signal });
          clearTimeout(tid);
          if (res.ok) {
            currentApiBase = base;
            const data = await res.json().catch(() => ({}));
            const wasOffline = !isServerOnline;
            isServerOnline = true;
            if (wasOffline) {
              window.dispatchEvent(new CustomEvent("hr:backend_online", { detail: { base, data } }));
            }
            return { online: true, base, data, model_loaded: !!data.model_loaded };
          }
        } catch {
          // Probe next candidate
        }
      }

      isServerOnline = false;
      window.dispatchEvent(new CustomEvent("hr:backend_offline", { detail: { base: currentApiBase } }));
      startAutoHealthPolling();
      return { online: false, base: currentApiBase };
    },

    isOnline() {
      return isServerOnline;
    },

    auth: {
      getToken: getStoredToken,
      getUser: getStoredUser,
      isAuthenticated: () => !!getStoredToken(),

      async login(email, password, remember = true) {
        const data = await request("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        const token = data.access_token;
        const storage = remember ? localStorage : sessionStorage;
        storage.setItem(TOKEN_KEY, token);

        // Fetch user profile immediately
        const user = await request("/auth/me");
        setAuthData(token, user, remember);
        window.dispatchEvent(new CustomEvent("hr:auth_changed", { detail: { user } }));
        return user;
      },

      async register(name, email, password) {
        const user = await request("/auth/register", {
          method: "POST",
          body: JSON.stringify({ name, email, password }),
        });
        // Auto-login after registration
        return await this.login(email, password, true);
      },

      async getMe() {
        if (!getStoredToken()) return null;
        try {
          const user = await request("/auth/me");
          setAuthData(getStoredToken(), user, true);
          return user;
        } catch (e) {
          if (e.status === 401) {
            clearAuthData();
            window.dispatchEvent(new CustomEvent("hr:auth_changed", { detail: { user: null } }));
          }
          return null;
        }
      },

      logout() {
        clearAuthData();
        window.dispatchEvent(new CustomEvent("hr:auth_changed", { detail: { user: null } }));
      },

      async listUsers() {
        return await request("/auth/users");
      },

      async getLoginHistory() {
        return await request("/auth/admin/logins");
      },
    },

    predict: {
      async run(payload) {
        return await request("/predict", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      },

      async save(assessmentData) {
        return await request("/predict/save", {
          method: "POST",
          body: JSON.stringify(assessmentData),
        });
      },

      async getHistory() {
        return await request("/predict/history");
      },

      async getAssessment(id) {
        return await request(`/predict/history/${encodeURIComponent(id)}`);
      },

      async deleteAssessment(id) {
        return await request(`/predict/history/${id}`, {
          method: "DELETE",
        });
      },
    },

    problems: {
      async list() {
        return await request("/problems");
      },

      async create(problemData) {
        return await request("/problems", {
          method: "POST",
          body: JSON.stringify(problemData),
        });
      },

      async delete(id) {
        return await request(`/problems/${id}`, {
          method: "DELETE",
        });
      },

      async update(id, problemData) {
        return await request(`/problems/${id}`, {
          method: "PUT",
          body: JSON.stringify(problemData),
        });
      },
    },

    prescriptions: {
      async list() {
        return await request("/api/prescriptions");
      },

      async get(id) {
        return await request(`/api/prescriptions/${id}`);
      },

      async upload(formData) {
        return await request("/api/prescriptions", {
          method: "POST",
          body: formData,
        });
      },

      async extract(formData) {
        return await request("/api/prescriptions/extract", {
          method: "POST",
          body: formData,
        });
      },

      async create(jsonPayload) {
        return await request("/api/prescriptions", {
          method: "POST",
          body: JSON.stringify(jsonPayload),
        });
      },

      async update(id, updateData) {
        return await request(`/api/prescriptions/${id}`, {
          method: "PUT",
          body: JSON.stringify(updateData),
        });
      },

      async delete(id) {
        return await request(`/api/prescriptions/${id}`, {
          method: "DELETE",
        });
      },

      async addMedicine(id, medData) {
        return await request(`/api/prescriptions/${id}/medicines`, {
          method: "POST",
          body: JSON.stringify(medData),
        });
      },

      async updateMedicine(id, medId, medData) {
        return await request(`/api/prescriptions/${id}/medicines/${medId}`, {
          method: "PUT",
          body: JSON.stringify(medData),
        });
      },

      async deleteMedicine(id, medId) {
        return await request(`/api/prescriptions/${id}/medicines/${medId}`, {
          method: "DELETE",
        });
      },

      getFileUrl(id) {
        const token = getStoredToken();
        const q = token ? `?token=${encodeURIComponent(token)}` : "";
        return `${currentApiBase}/api/prescriptions/${id}/file${q}`;
      },
    },

    allergies: {
      async list() {
        return await request("/allergies");
      },

      async create(allergyData) {
        return await request("/allergies", {
          method: "POST",
          body: JSON.stringify(allergyData),
        });
      },

      async update(id, allergyData) {
        return await request(`/allergies/${id}`, {
          method: "PUT",
          body: JSON.stringify(allergyData),
        });
      },

      async delete(id) {
        return await request(`/allergies/${id}`, {
          method: "DELETE",
        });
      },
    },

    timeline: {
      async list(eventType = "") {
        const q = eventType ? `?event_type=${encodeURIComponent(eventType)}` : "";
        return await request(`/api/timeline${q}`);
      },
    },

    briefings: {
      async list() {
        return await request("/api/briefings");
      },
      async get(id) {
        return await request(`/api/briefings/${id}`);
      },
      async draft(visitReason) {
        const q = `?visit_reason=${encodeURIComponent(visitReason)}`;
        return await request(`/api/briefings/draft${q}`, { method: "POST" });
      },
      async create(data) {
        return await request("/api/briefings", {
          method: "POST",
          body: JSON.stringify(data),
        });
      },
      async update(id, data) {
        return await request(`/api/briefings/${id}`, {
          method: "PUT",
          body: JSON.stringify(data),
        });
      },
      async delete(id) {
        return await request(`/api/briefings/${id}`, {
          method: "DELETE",
        });
      },
      async share(id, shareOptions) {
        return await request(`/api/briefings/${id}/share`, {
          method: "POST",
          body: JSON.stringify(shareOptions || {}),
        });
      },
      async revokeShare(token) {
        return await request(`/api/briefings/share/${token}`, {
          method: "DELETE",
        });
      },
      async getShared(token, pin = "") {
        const q = pin ? `?pin=${encodeURIComponent(pin)}` : "";
        return await request(`/api/briefings/shared/${token}${q}`);
      },
    },

    recommendations: {
      async get() {
        return await request("/api/recommendations");
      },

      async getFromInput(patient, risk_level = "") {
        const query = risk_level ? `?risk_level=${encodeURIComponent(risk_level)}` : "";
        return await request(`/api/recommendations${query}`, {
          method: "POST",
          body: JSON.stringify(patient),
        });
      },

      async getPersonalized() {
        return await request("/api/recommendations");
      },
    },

    medicines: {
      async list(search = "") {
        const query = search ? `?search=${encodeURIComponent(search)}` : "";
        return await request(`/medicines${query}`);
      },

      async checkSafety(checkData) {
        return await request("/medicines/check-safety", {
          method: "POST",
          body: JSON.stringify(checkData),
        });
      },
    },
  };

  // Expose globally
  window.HR_API = api;
})();

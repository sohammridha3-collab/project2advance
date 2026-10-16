/**
 * Centralized API Client & Service Layer for AI Health Risk Prediction System
 * Communicates directly with FastAPI backend.
 */
(() => {
  "use strict";

  const getApiBase = () => {
    if (typeof window !== "undefined" && window.location && window.location.origin && window.location.origin.startsWith("http")) {
      if (window.location.origin.includes(":8000")) {
        return window.location.origin;
      }
    }
    return "http://127.0.0.1:8000";
  };
  let currentApiBase = getApiBase();
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

  async function request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${currentApiBase}${endpoint}`;
    const headers = options.headers || {};

    const token = getStoredToken();
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers,
    };

    let response;
    try {
      response = await fetch(url, config);
    } catch (networkError) {
      // Intelligently try alternate loopback (127.0.0.1 <-> localhost) in case Windows mapped only one
      if (!endpoint.startsWith("http")) {
        const altBase = currentApiBase.includes("127.0.0.1") ? "http://localhost:8000" : "http://127.0.0.1:8000";
        try {
          response = await fetch(`${altBase}${endpoint}`, config);
          currentApiBase = altBase; // Alternate succeeded, persist as current
        } catch (secondErr) {
          // Both failed
        }
      }

      if (!response) {
        const err = new Error(`Cannot connect to backend server at ${currentApiBase}. Please ensure FastAPI is running.`);
        err.network = true;
        err.apiBase = currentApiBase;
        throw err;
      }
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
          message = data.detail.map(d => `${d.loc ? d.loc.slice(1).join(".") + ": " : ""}${d.msg}`).join("; ");
        } else if (data.detail) {
          message = data.detail;
        } else if (data.message) {
          message = data.message;
        }
      }
      const err = new Error(message);
      err.status = response.status;
      err.data = data;
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
            return { online: true, base, data };
          }
        } catch {
          // Probe next candidate
        }
      }

      return { online: false, base: currentApiBase };
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
        return `${API_BASE}/api/prescriptions/${id}/file${q}`;
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

/**
 * HealthBridge AI - Runtime Frontend Configuration
 * In production on Render, BACKEND_URL is populated during the static site build.
 * If running locally, api.js automatically targets local development environments.
 */
window.HEALTHBRIDGE_API_URL = window.HEALTHBRIDGE_API_URL || "https://healthbridge-ai.onrender.com";

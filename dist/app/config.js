// Deployment config for the AI service. Set to the public FastAPI API origin.
// For same-origin reverse proxy, use "". For local development with backend at 8000:
window.LUNARIS_API_BASE = window.LUNARIS_API_BASE ?? (
  ["localhost", "127.0.0.1"].includes(window.location.hostname) ? "http://localhost:8000" : ""
);

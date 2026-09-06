import axios from "axios";

const api = axios.create({
  // Using 127.0.0.1 avoids localhost IPv4/IPv6 resolution delays on Windows
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("gramsetu_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      "Something went wrong talking to the server.";
    console.error("[API error]", message);
    return Promise.reject(new Error(message));
  }
);

// Deterministic Loan Structuring
export const structureLoan = (marginCapital) =>
  api
    .post("/finance/structure-loan/", { margin_capital: marginCapital })
    .then((r) => r.data);

// Live Competitor Density & Saturation Mapping (Overpass OSM)
export const competitorsDensity = (payload) =>
  api.post("/competitors/density/", payload).then((r) => r.data);

// AI Feasibility Study (Mistral Structured Output)
export const generateFeasibility = (payload) =>
  api.post("/feasibility/generate/", payload).then((r) => r.data);

// Single-Roundtrip Full Feasibility Evaluation
export const fullFeasibilityEvaluation = (payload) =>
  api.post("/feasibility/evaluate/", payload).then((r) => r.data);

// Citizen Authentication / User Token Generation
export const otpLogin = (payload) =>
  api.post("/auth/otp-login/", payload).then((r) => r.data);

export default api;
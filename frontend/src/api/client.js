import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("gramsetu_access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.message ||
      "Something went wrong talking to the server.";
    console.error("[API error]", message);
    return Promise.reject(new Error(message));
  }
);

export const structureLoan = (marginCapital) =>
  api.post("/finance/structure-loan/", { margin_capital: marginCapital }).then((r) => r.data);

export const competitorsDensity = (payload) =>
  api.post("/geo/competitors-density/", payload).then((r) => r.data);

export const generateFeasibility = (payload) =>
  api.post("/advisory/generate-feasibility/", payload).then((r) => r.data);

export const otpLogin = (payload) =>
  api.post("/auth/otp-login/", payload).then((r) => r.data);

export default api;

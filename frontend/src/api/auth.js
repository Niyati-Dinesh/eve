// api/auth.js
import { apiFetch } from "./client";

export const login = (email, password) =>
  apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const register = (email, password) =>
  apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const getMe = () => apiFetch("/auth/me");

export const logout = () => apiFetch("/auth/logout", { method: "POST" });

// ── Forgot Password Flow ────────────────────────────────────────────────────

/** Step 1 — Request OTP */
export const requestPasswordReset = (email) =>
  apiFetch("/api/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });

/** Step 2 — Verify OTP, receive reset_token */
export const verifyOTP = (email, otp) =>
  apiFetch("/api/verify-otp", {
    method: "POST",
    body: JSON.stringify({ email, otp }),
  });

/** Step 3 — Reset password with reset_token */
export const resetPassword = (reset_token, new_password) =>
  apiFetch("/api/reset-password", {
    method: "POST",
    body: JSON.stringify({ reset_token, new_password }),
  });
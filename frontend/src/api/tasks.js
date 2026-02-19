// api/tasks.js
// All requests go to the FastAPI backend (port 8000),
// which then proxies to the master controller (port 8001).

import { apiFetch } from "./client";

// ── multipart/form-data helper (no Content-Type header — browser sets boundary) ──
async function apiFetchForm(path, formData) {
  const res = await fetch(`http://localhost:8000${path}`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (!res.ok) {
    let message = "API error";
    try {
      const err = await res.json();
      message = err.detail || err.message || message;
    } catch (_) {}
    throw new Error(message);
  }

  return res.json();
}

/**
 * Send a message through the backend proxy → master controller.
 * @param {string}      message        User's text
 * @param {string|null} conversationId Existing conversation ID (null = new)
 * @param {File[]}      files          Optional attachments
 */
export async function sendMessage(message, conversationId = null, files = []) {
  const form = new FormData();
  form.append("message", message);
  if (conversationId) form.append("conversation_id", conversationId);
  files.forEach((f) => form.append("files", f));

  return apiFetchForm("/api/tasks/message", form);
}

/**
 * Fetch message history for a conversation (from DB — persists across sessions).
 * @param {string} conversationId
 * @param {number} limit
 */
export const getHistory = (conversationId, limit = 50) =>
  apiFetch(`/api/tasks/history/${conversationId}?limit=${limit}`);

/**
 * List all conversations for the sidebar (persists across sessions).
 */
export const listConversations = () => apiFetch("/api/tasks/conversations");

/**
 * Soft-delete a conversation.
 * @param {string} conversationId
 */
export const deleteConversation = (conversationId) =>
  apiFetch(`/api/tasks/conversations/${conversationId}`, { method: "DELETE" });
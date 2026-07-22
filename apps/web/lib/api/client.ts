/**
 * Typed API client for ICF AI Copilot.
 * All calls go through Next.js rewrites to /api/v1/* → FastAPI.
 */

const API_BASE = "/api/v1";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `API error ${response.status}`);
  }

  return response.json();
}

export const api = {
  users: {
    me: (token: string) => apiFetch("/users/me", {}, token),
  },
  assessments: {
    modules: (token: string) => apiFetch("/assessments/modules", {}, token),
    start: (token: string) =>
      apiFetch("/assessments/start", { method: "POST" }, token),
    respond: (token: string, id: string, body: unknown) =>
      apiFetch(`/assessments/${id}/respond`, {
        method: "PUT",
        body: JSON.stringify(body),
      }, token),
    complete: (token: string, id: string) =>
      apiFetch(`/assessments/${id}/complete`, { method: "POST" }, token),
  },
  profiles: {
    me: (token: string) => apiFetch("/profiles/me", {}, token),
  },
  plans: {
    list: (token: string) => apiFetch("/plans", {}, token),
    generate: (token: string) =>
      apiFetch("/plans/generate", { method: "POST" }, token),
    get: (token: string, id: string) => apiFetch(`/plans/${id}`, {}, token),
    updateItem: (token: string, planId: string, itemId: string, body: unknown) =>
      apiFetch(`/plans/${planId}/items/${itemId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }, token),
  },
  governance: {
    auditLog: (token: string) => apiFetch("/governance/audit-log", {}, token),
    explain: (token: string, msgId: string) =>
      apiFetch(`/governance/explain/${msgId}`, {}, token),
  },
};

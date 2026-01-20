export const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");

async function requestJson(url, options = {}) {
  const resp = await fetch(url, options);
  const text = await resp.text();

  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // se não for JSON, mantém text como fallback
  }

  if (!resp.ok) {
    const msg = (data && (data.detail || data.message)) || text || `HTTP ${resp.status}`;
    throw new Error(msg);
  }

  return data;
}

export async function apiClassificar(texto) {
  return requestJson(`${API_BASE}/classificar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  });
}

export async function apiFeedback({ texto, previsto, correto }) {
  return requestJson(`${API_BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto, previsto, correto }),
  });
}

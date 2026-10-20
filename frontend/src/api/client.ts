/**
 * Shared backend client. One place owns the base URL and error handling so every
 * resource module (chat, analytics, transactions, budgets, goals) stays thin.
 *
 * The base URL comes from VITE_API_URL (see .env), falling back to the local dev
 * server so a fresh clone works with no config.
 */

export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function extractError(res: Response): Promise<string> {
  let detail = `HTTP ${res.status}`
  try {
    const body = await res.json()
    detail = body?.detail ?? detail
  } catch {
    // no JSON body — keep the status-based message
  }
  return detail
}

/** JSON request/response. Throws Error(detail) on non-2xx. */
export async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(opts.headers ?? {}),
    },
  })
  if (!res.ok) throw new Error(await extractError(res))
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

/** Multipart upload. Do NOT set Content-Type — the browser adds the boundary. */
export async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await extractError(res))
  return (await res.json()) as T
}

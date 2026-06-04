// Base URL — empty in dev (Vite proxy handles /api → localhost:8000)
// Set VITE_API_URL in .env for production deployments
const API_BASE = import.meta.env.VITE_API_URL ?? ''


/**
 * Streaming chat using the Fetch ReadableStream API.
 * Yields parsed SSE event objects one at a time.
 *
 * Event shapes:
 *   { type: 'meta',  agent, sources, session_id }
 *   { type: 'token', content }
 *   { type: 'done'  }
 *   { type: 'error', message }
 *
 * @param {string}      query
 * @param {string}      role        student | faculty | admin | general
 * @param {string|null} sessionId   pass null to start a new session
 * @param {AbortSignal} signal      from an AbortController
 */
export async function* streamMessage(query, role, sessionId = null, signal = null) {
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, role, session_id: sessionId }),
    signal,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }

  const reader  = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer    = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Split on newlines — keep the last (possibly incomplete) line in buffer
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data:')) continue
        try {
          yield JSON.parse(trimmed.slice(5).trim())
        } catch {
          /* skip malformed event */
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}


/**
 * Non-streaming health check — used on startup to verify the API is reachable.
 */
export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`)
  return res.json()
}
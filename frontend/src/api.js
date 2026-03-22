const BASE = '/api'

async function req(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

// Events
export const getEvents = (params = {}) => {
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v != null && v !== '' && q.set(k, v))
  return req(`/events?${q}`)
}

export const getRecommendations = (userId, limit = 20) =>
  req(`/recommendations/${userId}?limit=${limit}`)

// Likes
export const likeEvent = (eventId, userId) =>
  req(`/events/${eventId}/like?user_id=${userId}`, { method: 'POST' })

export const unlikeEvent = (eventId, userId) =>
  req(`/events/${eventId}/like?user_id=${userId}`, { method: 'DELETE' })

// Users
export const getUsers = () => req('/users')
export const createUser = (username) =>
  req('/users', { method: 'POST', body: JSON.stringify({ username }) })

// Scraper
export const triggerScrape = () => req('/scraper/run')
export const getScraperStatus = () => req('/scraper/status')
export const getScraperLogs = () => req('/scraper/logs?limit=20')

import { useState } from 'react'
import { createUser } from '../api.js'

export default function UserSwitcher({ users, currentUser, onUserChange, onUsersUpdate }) {
  const [open, setOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newUsername, setNewUsername] = useState('')
  const [error, setError] = useState('')

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newUsername.trim()) return
    setError('')
    try {
      await createUser(newUsername.trim())
      setNewUsername('')
      setCreating(false)
      onUsersUpdate()
    } catch (err) {
      setError(err.message)
    }
  }

  const avatarColor = (name) => {
    const colors = ['#7c3aed', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']
    const idx = name.charCodeAt(0) % colors.length
    return colors[idx]
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2.5 px-3 py-2 bg-vibe-surface border border-vibe-border rounded-xl
                   hover:border-vibe-purple/50 transition-all duration-200 group"
      >
        {currentUser ? (
          <>
            <span
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
              style={{ backgroundColor: avatarColor(currentUser.username) }}
            >
              {currentUser.username[0].toUpperCase()}
            </span>
            <span className="text-sm font-medium text-vibe-text">{currentUser.username}</span>
          </>
        ) : (
          <span className="text-sm text-vibe-text-muted">Select user</span>
        )}
        <svg
          className={`w-4 h-4 text-vibe-text-dim transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-vibe-card border border-vibe-border rounded-xl shadow-2xl shadow-black/60 z-50 overflow-hidden">
          <div className="p-2 space-y-0.5">
            {users.map((u) => (
              <button
                key={u.id}
                onClick={() => { onUserChange(u); setOpen(false) }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150
                  ${currentUser?.id === u.id
                    ? 'bg-vibe-purple/20 text-vibe-purple-light'
                    : 'text-vibe-text hover:bg-vibe-muted'
                  }`}
              >
                <span
                  className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                  style={{ backgroundColor: avatarColor(u.username) }}
                >
                  {u.username[0].toUpperCase()}
                </span>
                <span className="font-medium truncate">{u.username}</span>
                {currentUser?.id === u.id && (
                  <span className="ml-auto text-vibe-purple text-xs">✓</span>
                )}
              </button>
            ))}
          </div>

          <div className="border-t border-vibe-border p-2">
            {creating ? (
              <form onSubmit={handleCreate} className="space-y-2 p-1">
                <input
                  autoFocus
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="Username..."
                  maxLength={20}
                  className="w-full bg-vibe-muted border border-vibe-border rounded-lg px-3 py-1.5 text-sm
                             text-vibe-text placeholder-vibe-text-dim focus:outline-none focus:border-vibe-purple"
                />
                {error && <p className="text-red-400 text-xs px-1">{error}</p>}
                <div className="flex gap-2">
                  <button type="submit" className="flex-1 btn-primary py-1.5 text-xs">Create</button>
                  <button type="button" onClick={() => { setCreating(false); setError('') }} className="flex-1 btn-ghost py-1.5 text-xs">Cancel</button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setCreating(true)}
                disabled={users.length >= 10}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-vibe-text-muted
                           hover:bg-vibe-muted hover:text-vibe-text transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add user {users.length >= 10 ? '(max reached)' : `(${users.length}/10)`}
              </button>
            )}
          </div>
        </div>
      )}

      {open && (
        <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
      )}
    </div>
  )
}

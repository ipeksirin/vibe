import { useState } from 'react'
import { likeEvent, unlikeEvent } from '../api.js'
import { GenreTag } from './GenreFilter.jsx'

function formatDate(dateStr) {
  if (!dateStr) return null
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return null
    return d.toLocaleDateString('tr-TR', {
      weekday: 'short', day: 'numeric', month: 'short',
    }) + (dateStr.includes('T') ? ' · ' + d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }) : '')
  } catch {
    return null
  }
}

function ImagePlaceholder({ title, isMeyhane }) {
  const colors = isMeyhane
    ? ['from-red-950 to-rose-950', 'from-red-900 to-orange-950', 'from-rose-950 to-red-900']
    : ['from-violet-900 to-purple-950', 'from-indigo-900 to-blue-950', 'from-pink-900 to-rose-950', 'from-cyan-900 to-teal-950', 'from-fuchsia-900 to-purple-950']
  const color = colors[title.charCodeAt(0) % colors.length]
  const initials = title.split(' ').slice(0, 2).map((w) => w[0]?.toUpperCase()).join('')

  return (
    <div className={`w-full h-full bg-gradient-to-br ${color} flex items-center justify-center`}>
      {isMeyhane
        ? <span className="text-5xl select-none">🍷</span>
        : <span className="text-4xl font-black text-white/20 select-none">{initials}</span>
      }
    </div>
  )
}

export default function EventCard({ event, currentUserId, onLikeChange }) {
  const [liked, setLiked] = useState(event.liked || false)
  const [loading, setLoading] = useState(false)
  const [imgError, setImgError] = useState(false)

  const handleLike = async (e) => {
    e.stopPropagation()
    if (!currentUserId) return
    setLoading(true)
    try {
      if (liked) {
        await unlikeEvent(event.id, currentUserId)
        setLiked(false)
        onLikeChange?.(event.id, false)
      } else {
        await likeEvent(event.id, currentUserId)
        setLiked(true)
        onLikeChange?.(event.id, true)
      }
    } catch (err) {
      console.error('Like error:', err)
    } finally {
      setLoading(false)
    }
  }

  const isMeyhane = (event.genres || []).includes('meyhane')

  const handleTicketClick = (e) => {
    e.stopPropagation()
    if (isMeyhane) {
      const query = encodeURIComponent(`${event.venue} ${event.city || 'İstanbul'}`)
      window.open(`https://www.google.com/maps/search/?api=1&query=${query}`, '_blank', 'noopener,noreferrer')
      return
    }
    const url = event.ticket_url || event.source_url
    if (url && url.startsWith('http')) window.open(url, '_blank', 'noopener,noreferrer')
  }

  const genres = event.genres || []

  return (
    <article className="event-card group animate-[slideUp_0.3s_ease-out]">
      {/* Image */}
      <div className="relative aspect-[16/9] overflow-hidden bg-vibe-surface">
        {event.image_url && !imgError ? (
          <img
            src={event.image_url}
            alt={event.title}
            onError={() => setImgError(true)}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <ImagePlaceholder title={event.title} isMeyhane={isMeyhane} />
        )}

        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-vibe-card via-transparent to-transparent opacity-60" />

        {/* Like button */}
        <button
          onClick={handleLike}
          disabled={!currentUserId || loading}
          title={!currentUserId ? 'Select a user to like events' : liked ? 'Unlike' : 'Like'}
          className={`
            absolute top-3 right-3 w-9 h-9 rounded-full flex items-center justify-center
            transition-all duration-200 backdrop-blur-sm
            ${!currentUserId ? 'opacity-40 cursor-not-allowed bg-black/30' : 'cursor-pointer hover:scale-110'}
            ${liked ? 'bg-pink-500/90 shadow-[0_0_16px_rgba(236,72,153,0.6)]' : 'bg-black/40 hover:bg-black/60'}
          `}
        >
          <svg
            viewBox="0 0 24 24"
            className={`w-4.5 h-4.5 transition-all duration-200 ${liked ? 'fill-white stroke-white' : 'fill-none stroke-white/80'}`}
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
          </svg>
        </button>

        {/* Source badge */}
        {event.source && (
          <span className="absolute top-3 left-3 px-2 py-0.5 bg-black/50 backdrop-blur-sm rounded-full
                           text-[10px] font-medium text-vibe-text-dim uppercase tracking-wide">
            {event.source.replace(/_/g, ' ')}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Title */}
        <h3 className="font-bold text-base text-vibe-text leading-tight line-clamp-2 group-hover:text-white transition-colors">
          {event.title}
        </h3>

        {/* Venue + Date */}
        <div className="space-y-1">
          {event.venue && (
            <div className="flex items-center gap-1.5 text-sm text-vibe-text-muted">
              <svg className="w-3.5 h-3.5 flex-shrink-0 text-vibe-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="truncate font-medium">{event.venue}</span>
            </div>
          )}
          {formatDate(event.date) && (
            <div className="flex items-center gap-1.5 text-sm text-vibe-text-muted">
              <svg className="w-3.5 h-3.5 flex-shrink-0 text-vibe-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{formatDate(event.date)}</span>
            </div>
          )}
        </div>

        {/* Genre tags */}
        {genres.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {genres.slice(0, 3).map((g) => (
              <GenreTag key={g} genre={g} small />
            ))}
            {genres.length > 3 && (
              <span className="text-[10px] text-vibe-text-dim px-1.5 py-0.5">+{genres.length - 3}</span>
            )}
          </div>
        )}

        {/* Ticket button */}
        <button
          onClick={handleTicketClick}
          disabled={!isMeyhane && !event.ticket_url && !event.source_url}
          className="w-full mt-1 py-2 px-4 bg-vibe-purple/20 hover:bg-vibe-purple/30 border border-vibe-purple/30
                     hover:border-vibe-purple/60 text-vibe-purple-light text-sm font-semibold rounded-lg
                     transition-all duration-200 hover:shadow-[0_0_12px_rgba(124,58,237,0.2)]
                     disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {isMeyhane ? 'Haritada Gör ↗' : 'Get Tickets ↗'}
        </button>
      </div>
    </article>
  )
}

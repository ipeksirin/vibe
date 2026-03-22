const ALL_GENRES = [
  'electronic', 'techno', 'house', 'deep-house', 'ambient',
  'rock', 'metal', 'alternative', 'indie', 'jazz',
  'classical', 'pop', 'hip-hop', 'world-music',
  'festival', 'dj-set', 'live', 'acoustic',
]

const GENRE_COLORS = {
  electronic: 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10 hover:bg-cyan-500/20',
  techno: 'text-violet-300 border-violet-500/40 bg-violet-500/10 hover:bg-violet-500/20',
  house: 'text-purple-300 border-purple-500/40 bg-purple-500/10 hover:bg-purple-500/20',
  'deep-house': 'text-indigo-300 border-indigo-500/40 bg-indigo-500/10 hover:bg-indigo-500/20',
  ambient: 'text-teal-300 border-teal-500/40 bg-teal-500/10 hover:bg-teal-500/20',
  rock: 'text-red-400 border-red-500/40 bg-red-500/10 hover:bg-red-500/20',
  metal: 'text-red-600 border-red-700/40 bg-red-700/10 hover:bg-red-700/20',
  alternative: 'text-orange-400 border-orange-500/40 bg-orange-500/10 hover:bg-orange-500/20',
  indie: 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10 hover:bg-yellow-500/20',
  jazz: 'text-amber-400 border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20',
  classical: 'text-yellow-200 border-yellow-300/40 bg-yellow-300/10 hover:bg-yellow-300/20',
  pop: 'text-pink-400 border-pink-500/40 bg-pink-500/10 hover:bg-pink-500/20',
  'hip-hop': 'text-green-400 border-green-500/40 bg-green-500/10 hover:bg-green-500/20',
  'world-music': 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20',
  festival: 'text-fuchsia-400 border-fuchsia-500/40 bg-fuchsia-500/10 hover:bg-fuchsia-500/20',
  'dj-set': 'text-sky-400 border-sky-500/40 bg-sky-500/10 hover:bg-sky-500/20',
  live: 'text-lime-400 border-lime-500/40 bg-lime-500/10 hover:bg-lime-500/20',
  acoustic: 'text-stone-300 border-stone-400/40 bg-stone-400/10 hover:bg-stone-400/20',
}

const ACTIVE_COLORS = {
  electronic: 'bg-cyan-500 text-black border-cyan-400',
  techno: 'bg-violet-500 text-white border-violet-400',
  house: 'bg-purple-500 text-white border-purple-400',
  'deep-house': 'bg-indigo-500 text-white border-indigo-400',
  ambient: 'bg-teal-500 text-black border-teal-400',
  rock: 'bg-red-500 text-white border-red-400',
  metal: 'bg-red-700 text-white border-red-600',
  alternative: 'bg-orange-500 text-black border-orange-400',
  indie: 'bg-yellow-500 text-black border-yellow-400',
  jazz: 'bg-amber-500 text-black border-amber-400',
  classical: 'bg-yellow-200 text-black border-yellow-300',
  pop: 'bg-pink-500 text-white border-pink-400',
  'hip-hop': 'bg-green-500 text-black border-green-400',
  'world-music': 'bg-emerald-500 text-black border-emerald-400',
  festival: 'bg-fuchsia-500 text-white border-fuchsia-400',
  'dj-set': 'bg-sky-500 text-black border-sky-400',
  live: 'bg-lime-500 text-black border-lime-400',
  acoustic: 'bg-stone-400 text-black border-stone-300',
}

export function GenreTag({ genre, small = false }) {
  const base = GENRE_COLORS[genre] || 'text-vibe-text-muted border-vibe-border bg-vibe-muted'
  return (
    <span className={`inline-flex items-center rounded-full border font-medium uppercase tracking-wide
      ${small ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'} ${base}`}>
      {genre}
    </span>
  )
}

export default function GenreFilter({ selected, onToggle }) {
  return (
    <div className="flex flex-wrap gap-2">
      {ALL_GENRES.map((genre) => {
        const isActive = selected.includes(genre)
        const activeClass = ACTIVE_COLORS[genre] || 'bg-vibe-purple text-white border-vibe-purple'
        const inactiveClass = GENRE_COLORS[genre] || 'text-vibe-text-muted border-vibe-border bg-vibe-muted'
        return (
          <button
            key={genre}
            onClick={() => onToggle(genre)}
            className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wide
                        border transition-all duration-200 select-none
                        ${isActive ? `${activeClass} shadow-[0_0_10px_rgba(0,0,0,0.3)]` : inactiveClass}`}
          >
            {genre}
          </button>
        )
      })}
    </div>
  )
}

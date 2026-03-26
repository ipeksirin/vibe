import { useState, useEffect, useCallback, useRef } from 'react'
import EventCard from './components/EventCard.jsx'
import GenreFilter from './components/GenreFilter.jsx'
import UserSwitcher from './components/UserSwitcher.jsx'
import TabBar from './components/TabBar.jsx'
import { getEvents, getRecommendations, getUsers, getScraperStatus, triggerScrape, getVenues } from './api.js'

export default function App() {
  const [tab, setTab] = useState('all')
  const [events, setEvents] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [users, setUsers] = useState([])
  const [currentUser, setCurrentUser] = useState(null)
  const [selectedGenres, setSelectedGenres] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [selectedDistrict, setSelectedDistrict] = useState(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [venueSearch, setVenueSearch] = useState('')
  const [venueSuggestions, setVenueSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const venueRef = useRef(null)
  const [scraperStatus, setScraperStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState(false)
  const [error, setError] = useState(null)

  // Load users on mount
  useEffect(() => {
    loadUsers()
    loadScraperStatus()
    const interval = setInterval(loadScraperStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  // Load events when filters or user change (without date filter — date requires manual search)
  useEffect(() => {
    if (tab === 'all') loadEvents()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedGenres, selectedCategory, selectedDistrict, currentUser, tab])

  const handleSearch = () => {
    loadEvents(dateFrom, dateTo, venueSearch)
  }

  const handleClearFilters = () => {
    setDateFrom('')
    setDateTo('')
    setVenueSearch('')
    setVenueSuggestions([])
    setShowSuggestions(false)
    loadEvents()
  }

  // Venue autocomplete
  useEffect(() => {
    if (!venueSearch.trim()) {
      setVenueSuggestions([])
      setShowSuggestions(false)
      return
    }
    const timer = setTimeout(async () => {
      try {
        const results = await getVenues(venueSearch)
        setVenueSuggestions(results)
        setShowSuggestions(results.length > 0)
      } catch {
        setVenueSuggestions([])
      }
    }, 200)
    return () => clearTimeout(timer)
  }, [venueSearch])

  // Close suggestions on outside click
  useEffect(() => {
    const handler = (e) => {
      if (venueRef.current && !venueRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Load recommendations when switching to For You tab or user changes
  useEffect(() => {
    if (tab === 'for-you' && currentUser) loadRecommendations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, currentUser])

  const loadUsers = async () => {
    try {
      const data = await getUsers()
      setUsers(data)
      // Auto-select first user
      if (data.length > 0 && !currentUser) {
        setCurrentUser(data[0])
      }
    } catch (e) {
      console.error('Failed to load users:', e)
    }
  }

  const loadEvents = useCallback(async (fromDate, toDate, venue) => {
    setLoading(true)
    setError(null)
    try {
      const MUSIC_GENRES = [
        'electronic', 'techno', 'house', 'deep-house', 'ambient',
        'rock', 'alternative', 'indie',
        'classical', 'hip-hop',
        'festival', 'dj-set', 'live', 'acoustic',
      ]
      const effectiveGenres =
        selectedCategory === 'stand-up' ? ['stand-up'] :
        selectedCategory === 'meyhane' ? ['meyhane'] :
        (selectedCategory === 'music' && selectedGenres.length === 0) ? MUSIC_GENRES :
        selectedGenres
      const params = { user_id: currentUser?.id, limit: 80 }
      if (effectiveGenres.length === 1) params.genre = effectiveGenres[0]
      if (selectedCategory === 'music' || !selectedCategory) params.exclude_genres = 'meyhane,stand-up'
      if (selectedCategory === 'meyhane' && selectedDistrict) params.city = selectedDistrict
      if (fromDate) params.date_from = fromDate
      if (toDate) params.date_to = toDate
      if (venue) params.venue = venue
      const data = await getEvents(params)
      // Client-side filter only when user has explicitly selected 2+ genres
      // (not when effectiveGenres is the auto-expanded MUSIC_GENRES list)
      const filtered = (effectiveGenres.length > 1 && selectedGenres.length > 0)
        ? data.filter((e) => effectiveGenres.some((g) => (e.genres || []).includes(g)))
        : data
      setEvents(filtered)
    } catch (e) {
      setError('Failed to load events. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }, [selectedGenres, selectedCategory, selectedDistrict, currentUser])

  const loadRecommendations = useCallback(async () => {
    if (!currentUser) return
    setLoading(true)
    setError(null)
    try {
      const data = await getRecommendations(currentUser.id, 40)
      const filtered = selectedGenres.length > 0
        ? data.filter((e) => selectedGenres.some((g) => (e.genres || []).includes(g)))
        : data
      setRecommendations(filtered)
    } catch (e) {
      setError('Failed to load recommendations.')
    } finally {
      setLoading(false)
    }
  }, [currentUser, selectedGenres])

  const loadScraperStatus = async () => {
    try {
      const s = await getScraperStatus()
      setScraperStatus(s)
    } catch {
      // silently fail
    }
  }

  const MEYHANE_DISTRICTS = ['Kadıköy', 'Beyoğlu', 'Beşiktaş', 'Üsküdar', 'Şişli', 'Fatih', 'Sarıyer']

  const handleCategoryChange = (cat) => {
    setSelectedCategory(cat)
    setSelectedGenres([])
    setSelectedDistrict(null)
  }

  const handleGenreToggle = (genre) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    )
  }

  const handleClearGenres = () => setSelectedGenres([])

  const handleLikeChange = () => {
    // Refresh recommendations if on that tab
    if (tab === 'for-you') loadRecommendations()
  }

  const handleScrape = async () => {
    setScraping(true)
    try {
      await triggerScrape()
      setTimeout(() => {
        loadEvents()
        loadScraperStatus()
        setScraping(false)
      }, 3000)
    } catch {
      setScraping(false)
    }
  }

  const BG_THEME = {
    'stand-up': {
      bg: '#0d0900',
      glow1: 'bg-amber-500/10',
      glow2: 'bg-orange-500/8',
      glow3: 'bg-amber-500/5',
    },
    'meyhane': {
      bg: '#0f0004',
      glow1: 'bg-red-700/12',
      glow2: 'bg-rose-600/8',
      glow3: 'bg-red-800/5',
    },
  }
  const theme = BG_THEME[selectedCategory] || { bg: '#080810', glow1: 'bg-vibe-purple/10', glow2: 'bg-vibe-pink/8', glow3: 'bg-vibe-purple/5' }

  const displayedEvents = tab === 'for-you' ? recommendations : events
  const showForYouEmpty = tab === 'for-you' && !loading && recommendations.length === 0

  function formatLastRun(ts) {
    if (!ts) return 'Never'
    try {
      const d = new Date(ts + 'Z')
      const diff = Date.now() - d.getTime()
      const mins = Math.floor(diff / 60000)
      if (mins < 1) return 'Just now'
      if (mins < 60) return `${mins}m ago`
      const hours = Math.floor(mins / 60)
      if (hours < 24) return `${hours}h ago`
      return `${Math.floor(hours / 24)}d ago`
    } catch {
      return ts
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: theme.bg, transition: 'background-color 0.6s ease' }}>
      {/* Background glow effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className={`absolute -top-40 -left-40 w-96 h-96 ${theme.glow1} rounded-full blur-3xl transition-all duration-700`} />
        <div className={`absolute top-1/3 -right-40 w-96 h-96 ${theme.glow2} rounded-full blur-3xl transition-all duration-700`} />
        <div className={`absolute bottom-0 left-1/2 w-96 h-96 ${theme.glow3} rounded-full blur-3xl transition-all duration-700`} />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-30 bg-vibe-bg/80 backdrop-blur-xl border-b border-vibe-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="relative">
              <span className="text-2xl font-black tracking-widest text-white text-glow-purple">VIBE</span>
              <span className="absolute -top-0.5 -right-3 text-[8px] font-bold text-vibe-pink uppercase tracking-widest">IST</span>
            </div>
          </div>

          {/* Tab bar — centered */}
          <div className="flex-1 flex justify-center">
            <TabBar activeTab={tab} onTabChange={(t) => { setTab(t); if (t === 'for-you' && currentUser) loadRecommendations() }} />
          </div>

          {/* Right: user switcher */}
          <div className="flex-shrink-0">
            <UserSwitcher
              users={users}
              currentUser={currentUser}
              onUserChange={setCurrentUser}
              onUsersUpdate={loadUsers}
            />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Filter bar */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-semibold text-vibe-text-muted uppercase tracking-widest">Genres</h2>
              {selectedGenres.length > 0 && (
                <button
                  onClick={handleClearGenres}
                  className="text-xs text-vibe-pink hover:text-vibe-pink-light transition-colors"
                >
                  Clear ({selectedGenres.length})
                </button>
              )}
            </div>
            <div className="flex items-center gap-3">
              {/* Scraper status */}
              {scraperStatus && (
                <span className="text-[11px] text-vibe-text-dim hidden sm:flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse-slow" />
                  {scraperStatus.event_count} events · updated {formatLastRun(scraperStatus.last_run)}
                </span>
              )}
              <button
                onClick={handleScrape}
                disabled={scraping}
                className="flex items-center gap-1.5 text-xs text-vibe-text-dim hover:text-vibe-text
                           px-3 py-1.5 bg-vibe-surface border border-vibe-border rounded-lg
                           hover:border-vibe-purple/40 transition-all duration-200 disabled:opacity-50"
              >
                <svg className={`w-3 h-3 ${scraping ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {scraping ? 'Scraping...' : 'Refresh'}
              </button>
            </div>
          </div>
          <GenreFilter selected={selectedGenres} onToggle={handleGenreToggle} onClearAll={handleClearGenres} selectedCategory={selectedCategory} onCategoryChange={handleCategoryChange} />

          {/* Date range + Search */}
          {selectedCategory === 'meyhane' && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {MEYHANE_DISTRICTS.map((d) => (
                <button
                  key={d}
                  onClick={() => setSelectedDistrict(selectedDistrict === d ? null : d)}
                  className={`text-xs font-semibold px-3 py-2 rounded-lg border transition-all duration-200
                    ${selectedDistrict === d
                      ? 'bg-red-800 text-white border-red-700'
                      : 'bg-vibe-surface border-vibe-border text-vibe-text-dim hover:border-red-700/50 hover:text-vibe-text'}`}
                >
                  {d}
                </button>
              ))}
            </div>
          )}
          {selectedCategory !== 'meyhane' && (<div className="flex flex-wrap items-center gap-2 pt-1">
            {/* Quick year buttons */}
            {['2026', '2027'].map((yr) => {
              const isActive = dateFrom === `${yr}-01-01` && dateTo === `${yr}-12-31`
              return (
                <button
                  key={yr}
                  onClick={() => { setDateFrom(`${yr}-01-01`); setDateTo(`${yr}-12-31`) }}
                  className={`text-xs font-semibold px-3 py-2 rounded-lg border transition-all duration-200
                    ${isActive
                      ? 'bg-vibe-purple text-white border-vibe-purple'
                      : 'bg-vibe-surface border-vibe-border text-vibe-text-dim hover:border-vibe-purple/50 hover:text-vibe-text'}`}
                >
                  {yr}
                </button>
              )
            })}
            <div className="flex items-center gap-2 bg-vibe-surface border border-vibe-border rounded-lg px-3 py-2">
              <svg className="w-3.5 h-3.5 text-vibe-text-dim flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-transparent text-xs text-vibe-text outline-none w-32 cursor-pointer"
              />
              <span className="text-vibe-text-dim text-xs">→</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-transparent text-xs text-vibe-text outline-none w-32 cursor-pointer"
              />
            </div>
            {/* Venue search with autocomplete */}
            <div ref={venueRef} className="relative">
              <div className="flex items-center gap-2 bg-vibe-surface border border-vibe-border rounded-lg px-3 py-2">
                <svg className="w-3.5 h-3.5 text-vibe-text-dim flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <input
                  type="text"
                  value={venueSearch}
                  onChange={(e) => setVenueSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (setShowSuggestions(false), handleSearch())}
                  onFocus={() => venueSuggestions.length > 0 && setShowSuggestions(true)}
                  placeholder="Venue..."
                  className="bg-transparent text-xs text-vibe-text outline-none w-36 placeholder:text-vibe-text-dim"
                />
              </div>
              {showSuggestions && (
                <div className="absolute top-full mt-1 left-0 w-56 bg-vibe-surface border border-vibe-border rounded-lg shadow-xl z-50 overflow-hidden">
                  {venueSuggestions.map((v) => (
                    <button
                      key={v}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        setVenueSearch(v)
                        setShowSuggestions(false)
                        loadEvents(dateFrom, dateTo, v)
                      }}
                      className="w-full text-left px-3 py-2 text-xs text-vibe-text hover:bg-vibe-purple/20 hover:text-white transition-colors"
                    >
                      {v}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleSearch}
              className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 bg-vibe-purple hover:bg-vibe-purple/80 text-white rounded-lg transition-all duration-200"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search
            </button>
            {(dateFrom || dateTo || venueSearch) && (
              <button
                onClick={handleClearFilters}
                className="text-xs text-vibe-text-dim hover:text-vibe-pink transition-colors"
              >
                Clear filters
              </button>
            )}
          </div>
          )}
        </div>

        {/* No user selected — For You tab */}
        {tab === 'for-you' && !currentUser && (
          <div className="text-center py-20 space-y-4">
            <div className="text-6xl">✦</div>
            <p className="text-vibe-text-muted text-lg">Select a user to see your personalized feed</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {/* For You empty state (has user, no likes) */}
        {showForYouEmpty && currentUser && (
          <div className="text-center py-20 space-y-4">
            <div className="text-6xl">◈</div>
            <h3 className="text-xl font-bold text-vibe-text">Your feed is empty</h3>
            <p className="text-vibe-text-muted max-w-md mx-auto">
              Like some events from the <strong className="text-vibe-text">All Events</strong> tab and we'll start surfacing personalized recommendations here.
            </p>
            <button
              onClick={() => setTab('all')}
              className="btn-primary mt-2"
            >
              Browse All Events
            </button>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-vibe-card border border-vibe-border rounded-xl overflow-hidden animate-pulse">
                <div className="aspect-[16/9] bg-vibe-muted" />
                <div className="p-4 space-y-3">
                  <div className="h-4 bg-vibe-muted rounded w-3/4" />
                  <div className="h-3 bg-vibe-muted rounded w-1/2" />
                  <div className="h-3 bg-vibe-muted rounded w-2/3" />
                  <div className="flex gap-2">
                    <div className="h-5 w-16 bg-vibe-muted rounded-full" />
                    <div className="h-5 w-12 bg-vibe-muted rounded-full" />
                  </div>
                  <div className="h-9 bg-vibe-muted rounded-lg" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Events grid */}
        {!loading && displayedEvents.length > 0 && (
          <>
            <div className="flex items-center justify-between">
              <p className="text-sm text-vibe-text-dim">
                {tab === 'for-you' ? `${displayedEvents.length} recommendations` : `${displayedEvents.length} events`}
                {selectedGenres.length > 0 && ` · filtered`}
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {displayedEvents.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  currentUserId={currentUser?.id}
                  onLikeChange={handleLikeChange}
                />
              ))}
            </div>
          </>
        )}

        {/* All events empty state */}
        {!loading && tab === 'all' && displayedEvents.length === 0 && !error && (
          <div className="text-center py-20 space-y-4">
            <div className="text-6xl">◎</div>
            <h3 className="text-xl font-bold text-vibe-text">No events found</h3>
            <p className="text-vibe-text-muted">
              {selectedGenres.length > 0
                ? 'Try different genre filters or run the scraper to fetch new events.'
                : 'Run the scraper to fetch Istanbul events.'}
            </p>
            <div className="flex items-center justify-center gap-3">
              {selectedGenres.length > 0 && (
                <button onClick={handleClearGenres} className="btn-ghost">Clear Filters</button>
              )}
              <button onClick={handleScrape} disabled={scraping} className="btn-primary">
                {scraping ? 'Scraping...' : 'Run Scraper'}
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-vibe-border mt-12 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between text-xs text-vibe-text-dim">
          <span>VIBE Istanbul — Event Discovery</span>
          <span className="hidden sm:block">
            {scraperStatus?.event_count || 0} events · auto-refreshes every 6h
          </span>
        </div>
      </footer>
    </div>
  )
}

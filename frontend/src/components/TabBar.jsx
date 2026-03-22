export default function TabBar({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'for-you', label: 'For You', icon: '✦' },
    { id: 'all', label: 'All Events', icon: '◈' },
  ]

  return (
    <div className="flex gap-1 bg-vibe-surface border border-vibe-border rounded-xl p-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`
            flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200
            ${activeTab === tab.id
              ? 'bg-vibe-purple text-white shadow-[0_0_16px_rgba(124,58,237,0.4)]'
              : 'text-vibe-text-muted hover:text-vibe-text hover:bg-vibe-muted'
            }
          `}
        >
          <span className="text-xs">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </div>
  )
}

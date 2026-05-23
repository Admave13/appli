import './Sidebar.css'

export default function Sidebar({ pages, current, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">appli.</div>
      <nav className="sidebar-nav">
        {Object.entries(pages).map(([key, { label }]) => (
          <button
            key={key}
            className={`nav-item ${current === key ? 'nav-item--active' : ''}`}
            onClick={() => onNavigate(key)}
          >
            {label}
          </button>
        ))}
      </nav>
    </aside>
  )
}

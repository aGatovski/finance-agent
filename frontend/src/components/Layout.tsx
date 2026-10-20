import { NavLink, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/transactions', label: 'Transactions', icon: '📄' },
  { to: '/merchants', label: 'Merchants', icon: '🏷️' },
  { to: '/budgets', label: 'Budgets', icon: '🎯' },
  { to: '/goals', label: 'Goals', icon: '🏁' },
  { to: '/chat', label: 'Chat', icon: '💬' },
]

/** Persistent app shell: sidebar nav on the left, routed page on the right. */
export default function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand">
          <span className="brand-mark">€</span>
          <span>Finance&nbsp;Agent</span>
        </NavLink>
        <nav className="nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon" aria-hidden>
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">local dev · user 1</div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}

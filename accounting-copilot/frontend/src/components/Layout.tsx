import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface LayoutProps { children: React.ReactNode; }

const navItems = [
  {
    path: '/dashboard', label: 'Dashboard',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>,
  },
  {
    path: '/transactions', label: 'Transactions',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>,
  },
  {
    path: '/upload', label: 'Upload',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
  },
  {
    path: '/assistant', label: 'Assistant',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
  },
  {
    path: '/approvals', label: 'Approvals',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>,
  },
  {
    path: '/audit', label: 'Audit Trail',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
  },
];

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <div style={s.wrapper}>
      {sidebarOpen && <div style={s.overlay} onClick={() => setSidebarOpen(false)} />}

      <aside style={{ ...s.sidebar, ...(sidebarOpen ? s.sidebarOpen : {}) }}>
        {/* Brand */}
        <div style={s.brand}>
          <div style={s.brandIcon}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <div style={s.brandName}>AI Accounting</div>
            <div style={s.brandTag}>Copilot</div>
          </div>
        </div>

        {/* Nav */}
        <nav style={s.nav}>
          <div style={s.navGroup}>
            <div style={s.navGroupLabel}>Navigation</div>
            {navItems.map((item) => {
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{ ...s.navItem, ...(active ? s.navItemActive : {}) }}
                  onClick={() => setSidebarOpen(false)}
                >
                  <span style={{ ...s.navIcon, ...(active ? s.navIconActive : {}) }}>
                    {item.icon}
                  </span>
                  <span style={s.navLabel}>{item.label}</span>
                  {active && <span style={s.activePip} />}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* User */}
        <div style={s.userSection}>
          <div style={s.userAvatar}>
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div style={s.userInfo}>
            <div style={s.userName}>{user?.email?.split('@')[0] || 'User'}</div>
            <div style={s.userEmail}>{user?.email || ''}</div>
          </div>
          <button onClick={handleSignOut} style={s.signOutBtn} title="Sign out">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </aside>

      <div style={s.mainWrapper}>
        {/* Mobile header */}
        <div style={s.mobileHeader}>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} style={s.hamburger}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <span style={s.mobileTitle}>AI Accounting Copilot</span>
        </div>
        <main style={s.main}>{children}</main>
      </div>
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  wrapper: { display: 'flex', minHeight: '100vh', backgroundColor: 'var(--color-surface)' },
  overlay: { position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.45)', zIndex: 199, backdropFilter: 'blur(3px)' },
  sidebar: {
    position: 'fixed', top: 0, left: 0, bottom: 0, width: '240px',
    backgroundColor: 'var(--sidebar-bg)',
    display: 'flex', flexDirection: 'column', zIndex: 200,
    transition: 'transform var(--transition-base)',
    borderRight: '1px solid rgba(255,255,255,0.05)',
  },
  sidebarOpen: { transform: 'translateX(0)' },
  brand: {
    display: 'flex', alignItems: 'center', gap: '11px',
    padding: '22px 18px 18px',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
  },
  brandIcon: {
    width: '38px', height: '38px', borderRadius: '10px',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    boxShadow: '0 4px 12px rgba(99,102,241,0.4)',
  },
  brandName: { fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', lineHeight: 1.2 },
  brandTag: { fontSize: '0.65rem', color: 'rgba(148,163,184,0.7)', letterSpacing: '0.8px', textTransform: 'uppercase' as const, marginTop: 1 },
  nav: { flex: 1, padding: '14px 10px', overflowY: 'auto' },
  navGroup: { display: 'flex', flexDirection: 'column', gap: '1px' },
  navGroupLabel: {
    fontSize: '0.6rem', fontWeight: 700, color: 'rgba(148,163,184,0.4)',
    letterSpacing: '1.5px', textTransform: 'uppercase' as const,
    padding: '0 10px', marginBottom: '6px', marginTop: '4px',
  },
  navItem: {
    display: 'flex', alignItems: 'center', gap: '10px',
    padding: '9px 10px', borderRadius: '8px',
    textDecoration: 'none', color: 'var(--sidebar-text)',
    fontSize: '0.875rem', fontWeight: 500,
    transition: 'all var(--transition-fast)', position: 'relative' as const,
  },
  navItemActive: {
    backgroundColor: 'rgba(99,102,241,0.18)',
    color: '#a5b4fc',
  },
  navIcon: { display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.55, flexShrink: 0 },
  navIconActive: { opacity: 1 },
  navLabel: { flex: 1 },
  activePip: { width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#818cf8' },
  userSection: {
    display: 'flex', alignItems: 'center', gap: '9px',
    padding: '14px 14px', borderTop: '1px solid rgba(255,255,255,0.06)',
  },
  userAvatar: {
    width: '32px', height: '32px', borderRadius: '8px',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: '#fff', fontWeight: 700, fontSize: '0.8rem', flexShrink: 0,
  },
  userInfo: { flex: 1, minWidth: 0, overflow: 'hidden' },
  userName: { fontSize: '0.78rem', fontWeight: 600, color: '#e2e8f0', whiteSpace: 'nowrap' as const, overflow: 'hidden', textOverflow: 'ellipsis' },
  userEmail: { fontSize: '0.68rem', color: 'rgba(148,163,184,0.6)', whiteSpace: 'nowrap' as const, overflow: 'hidden', textOverflow: 'ellipsis' },
  signOutBtn: {
    width: '30px', height: '30px', borderRadius: '7px',
    border: '1px solid rgba(255,255,255,0.08)',
    backgroundColor: 'transparent', color: '#64748b',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', flexShrink: 0, transition: 'all var(--transition-fast)',
  },
  mainWrapper: { flex: 1, marginLeft: '240px', minHeight: '100vh', display: 'flex', flexDirection: 'column' },
  mobileHeader: {
    display: 'none', alignItems: 'center', gap: '12px',
    padding: '12px 16px', backgroundColor: 'var(--color-card)',
    borderBottom: '1px solid var(--color-border)',
    position: 'sticky' as const, top: 0, zIndex: 100,
  },
  hamburger: { background: 'none', border: 'none', color: 'var(--color-text)', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' },
  mobileTitle: { fontWeight: 700, fontSize: '1rem', color: 'var(--color-primary)' },
  main: { flex: 1 },
};

// Responsive + hover styles
const sheet = document.createElement('style');
sheet.id = 'layout-styles';
sheet.textContent = `
  @media (max-width: 768px) {
    aside { transform: translateX(-100%) !important; }
    .main-wrapper { margin-left: 0 !important; }
    .mobile-header { display: flex !important; }
  }
  aside a:hover:not([style*="rgba(99,102,241,0.18)"]) {
    background-color: rgba(99,102,241,0.08) !important;
    color: #c7d2fe !important;
  }
  aside a:hover span:first-child { opacity: 0.85 !important; }
  aside button[title="Sign out"]:hover {
    background-color: rgba(255,255,255,0.08) !important;
    color: #94a3b8 !important;
  }
`;
if (!document.getElementById('layout-styles')) document.head.appendChild(sheet);

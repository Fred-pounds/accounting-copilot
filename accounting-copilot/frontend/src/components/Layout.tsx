import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

const navItems = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    path: '/transactions',
    label: 'Transactions',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23" />
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
      </svg>
    ),
  },
  {
    path: '/upload',
    label: 'Upload',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
  {
    path: '/assistant',
    label: 'Assistant',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    path: '/approvals',
    label: 'Approvals',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 11l3 3L22 4" />
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
      </svg>
    ),
  },
  {
    path: '/audit',
    label: 'Audit Trail',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
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
    <div style={styles.wrapper}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          style={styles.overlay}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        style={{
          ...styles.sidebar,
          ...(sidebarOpen ? styles.sidebarOpen : {}),
        }}
      >
        {/* Brand */}
        <div style={styles.brand}>
          <div style={styles.brandIcon}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <div style={styles.brandName}>AccoCopilot</div>
            <div style={styles.brandTagline}>AI Accounting</div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={styles.nav}>
          <div style={styles.navSection}>
            <div style={styles.navSectionLabel}>MENU</div>
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    ...styles.navItem,
                    ...(isActive ? styles.navItemActive : {}),
                  }}
                  onClick={() => setSidebarOpen(false)}
                >
                  <span style={{
                    ...styles.navIcon,
                    ...(isActive ? styles.navIconActive : {}),
                  }}>
                    {item.icon}
                  </span>
                  <span style={styles.navLabel}>{item.label}</span>
                  {isActive && <span style={styles.activeIndicator} />}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* User section */}
        <div style={styles.userSection}>
          <div style={styles.userInfo}>
            <div style={styles.avatar}>
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div style={styles.userDetails}>
              <div style={styles.userName}>
                {user?.email?.split('@')[0] || 'User'}
              </div>
              <div style={styles.userEmail}>{user?.email || ''}</div>
            </div>
          </div>
          <button onClick={handleSignOut} style={styles.signOutBtn} title="Sign Out">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div style={styles.mainWrapper}>
        {/* Mobile top bar */}
        <div style={styles.mobileHeader}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={styles.hamburger}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <span style={styles.mobileTitle}>AccoCopilot</span>
        </div>

        <main style={styles.main}>{children}</main>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: 'var(--color-surface)',
  },
  overlay: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 199,
    backdropFilter: 'blur(4px)',
  },
  sidebar: {
    position: 'fixed',
    top: 0,
    left: 0,
    bottom: 0,
    width: '260px',
    backgroundColor: 'var(--sidebar-bg)',
    display: 'flex',
    flexDirection: 'column',
    zIndex: 200,
    transition: 'transform var(--transition-base)',
    overflowY: 'auto',
    overflowX: 'hidden',
  },
  sidebarOpen: {
    transform: 'translateX(0)',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '24px 20px 20px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
  },
  brandIcon: {
    width: '42px',
    height: '42px',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  brandName: {
    fontSize: '1.125rem',
    fontWeight: 700,
    color: '#ffffff',
    lineHeight: 1.2,
  },
  brandTagline: {
    fontSize: '0.7rem',
    color: 'rgba(199, 210, 254, 0.6)',
    letterSpacing: '0.5px',
    textTransform: 'uppercase' as const,
  },
  nav: {
    flex: 1,
    padding: '16px 12px',
    overflowY: 'auto',
  },
  navSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  navSectionLabel: {
    fontSize: '0.65rem',
    fontWeight: 600,
    color: 'rgba(199, 210, 254, 0.4)',
    letterSpacing: '1.5px',
    padding: '0 12px',
    marginBottom: '8px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 12px',
    borderRadius: '10px',
    textDecoration: 'none',
    color: 'var(--sidebar-text)',
    fontSize: '0.875rem',
    fontWeight: 500,
    transition: 'all var(--transition-fast)',
    position: 'relative' as const,
  },
  navItemActive: {
    backgroundColor: 'var(--sidebar-active)',
    color: '#ffffff',
    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
  },
  navIcon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.7,
  },
  navIconActive: {
    opacity: 1,
  },
  navLabel: {
    flex: 1,
  },
  activeIndicator: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: '#a5b4fc',
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 16px',
    borderTop: '1px solid rgba(255,255,255,0.08)',
    marginTop: 'auto',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    flex: 1,
    minWidth: 0,
  },
  avatar: {
    width: '36px',
    height: '36px',
    borderRadius: '10px',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#ffffff',
    fontWeight: 700,
    fontSize: '0.875rem',
    flexShrink: 0,
  },
  userDetails: {
    minWidth: 0,
    overflow: 'hidden',
  },
  userName: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#e0e7ff',
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userEmail: {
    fontSize: '0.7rem',
    color: 'rgba(199, 210, 254, 0.5)',
    whiteSpace: 'nowrap' as const,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  signOutBtn: {
    width: '34px',
    height: '34px',
    borderRadius: '8px',
    border: '1px solid rgba(255,255,255,0.1)',
    backgroundColor: 'transparent',
    color: 'var(--sidebar-text)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    flexShrink: 0,
    transition: 'all var(--transition-fast)',
  },
  mainWrapper: {
    flex: 1,
    marginLeft: '260px',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  mobileHeader: {
    display: 'none',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    backgroundColor: 'var(--color-card)',
    borderBottom: '1px solid var(--color-border)',
    position: 'sticky' as const,
    top: 0,
    zIndex: 100,
  },
  hamburger: {
    background: 'none',
    border: 'none',
    color: 'var(--color-text)',
    cursor: 'pointer',
    padding: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mobileTitle: {
    fontWeight: 700,
    fontSize: '1.1rem',
    color: 'var(--color-primary)',
  },
  main: {
    flex: 1,
    minHeight: 'calc(100vh - 1px)',
  },
};

// Add responsive styles via a style tag
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @media (max-width: 768px) {
    aside[style] {
      transform: translateX(-100%) !important;
    }
    div[style*="marginLeft: 260px"],
    div[style*="margin-left: 260px"] {
      margin-left: 0 !important;
    }
    div[style*="display: none"][style*="gap: 12px"] {
      display: flex !important;
    }
  }
  aside[style] a[style]:hover {
    background-color: rgba(99, 102, 241, 0.15) !important;
  }
  div[style] button[title="Sign Out"]:hover {
    background-color: rgba(255,255,255,0.1) !important;
  }
`;
if (!document.getElementById('layout-responsive-styles')) {
  styleSheet.id = 'layout-responsive-styles';
  document.head.appendChild(styleSheet);
}

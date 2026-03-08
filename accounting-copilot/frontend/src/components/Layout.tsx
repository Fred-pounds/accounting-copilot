import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/transactions', label: 'Transactions' },
    { path: '/upload', label: 'Upload' },
    { path: '/assistant', label: 'Assistant' },
    { path: '/approvals', label: 'Approvals' },
    { path: '/audit', label: 'Audit Trail' },
  ];

  return (
    <div style={styles.container}>
      <nav style={styles.nav}>
        <div style={styles.navContent}>
          <div style={styles.navBrand}>
            <Link to="/dashboard" style={styles.brandLink}>
              AI Accounting Copilot
            </Link>
          </div>

          <div style={styles.navLinks}>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  ...styles.navLink,
                  ...(location.pathname === item.path ? styles.navLinkActive : {}),
                }}
              >
                {item.label}
              </Link>
            ))}
          </div>

          <div style={styles.navUser}>
            <span style={styles.userName}>{user?.email}</span>
            <button onClick={handleSignOut} style={styles.signOutButton}>
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      <main style={styles.main}>{children}</main>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  nav: {
    backgroundColor: 'white',
    borderBottom: '1px solid #ddd',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  navContent: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '1rem 2rem',
    display: 'flex',
    alignItems: 'center',
    gap: '2rem',
  },
  navBrand: {
    fontSize: '1.25rem',
    fontWeight: 'bold',
  },
  brandLink: {
    textDecoration: 'none',
    color: '#007bff',
  },
  navLinks: {
    display: 'flex',
    gap: '1.5rem',
    flex: 1,
  },
  navLink: {
    textDecoration: 'none',
    color: '#666',
    fontWeight: '500',
    padding: '0.5rem 0',
    borderBottom: '2px solid transparent',
    transition: 'all 0.2s',
  },
  navLinkActive: {
    color: '#007bff',
    borderBottomColor: '#007bff',
  },
  navUser: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  userName: {
    fontSize: '0.875rem',
    color: '#666',
  },
  signOutButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    cursor: 'pointer',
  },
  main: {
    minHeight: 'calc(100vh - 73px)',
  },
};

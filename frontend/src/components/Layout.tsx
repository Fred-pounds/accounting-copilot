import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  const navItems = [
    { 
      path: '/dashboard', 
      label: 'Dashboard',
      icon: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
        </svg>
      )
    },
    { 
      path: '/transactions', 
      label: 'Transactions',
      icon: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M8 5a1 1 0 100 2h5.586l-1.293 1.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L13.586 5H8zM12 15a1 1 0 100-2H6.414l1.293-1.293a1 1 0 10-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L6.414 15H12z"/>
        </svg>
      )
    },
    { 
      path: '/upload', 
      label: 'Upload',
      icon: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd"/>
        </svg>
      )
    },
    { 
      path: '/assistant', 
      label: 'Assistant',
      icon: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
        </svg>
      )
    },
    { 
      path: '/approvals', 
      label: 'Approvals',
      icon: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
        </svg>
      )
    },
    { 
      path: '/audit', 
      label: 'Audit Trail',
      icon: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"/>
        </svg>
      )
    },
  ];

  const getInitials = (email: string) => {
    return email.substring(0, 2).toUpperCase();
  };

  return (
    <div style={styles.container}>
      {/* Top Navigation Bar */}
      <nav style={styles.nav}>
        <div style={styles.navContent}>
          {/* Logo/Brand */}
          <div style={styles.navBrand}>
            <Link to="/dashboard" style={styles.brandLink}>
              <div style={styles.logo}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <span style={styles.brandText}>AI Accounting</span>
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <div style={styles.navLinks}>
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    ...styles.navLink,
                    ...(isActive ? styles.navLinkActive : {}),
                  }}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <span style={styles.navLinkIcon}>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* User Menu */}
          <div style={styles.navUser}>
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              style={styles.userButton}
              aria-label="User menu"
              aria-expanded={isUserMenuOpen}
            >
              <div style={styles.avatar}>
                {getInitials(user?.email || 'U')}
              </div>
              <span style={styles.userEmail}>{user?.email}</span>
              <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" style={{
                transform: isUserMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 200ms',
              }}>
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"/>
              </svg>
            </button>

            {/* User Dropdown Menu */}
            {isUserMenuOpen && (
              <div style={styles.userDropdown} className="animate-slide-in">
                <div style={styles.userDropdownHeader}>
                  <div style={styles.userDropdownEmail}>{user?.email}</div>
                  <div style={styles.userDropdownRole}>Account Owner</div>
                </div>
                <div style={styles.userDropdownDivider} />
                <button onClick={handleSignOut} style={styles.signOutButton}>
                  <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd"/>
                  </svg>
                  Sign Out
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            style={styles.mobileMenuButton}
            aria-label="Toggle menu"
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? (
              <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
              </svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd"/>
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div style={styles.mobileMenu} className="animate-slide-in">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  style={{
                    ...styles.mobileNavLink,
                    ...(isActive ? styles.mobileNavLinkActive : {}),
                  }}
                >
                  <span style={styles.navLinkIcon}>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
            <div style={styles.mobileMenuDivider} />
            <button onClick={handleSignOut} style={styles.mobileSignOutButton}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd"/>
              </svg>
              Sign Out
            </button>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main style={styles.main}>{children}</main>

      {/* Overlay for mobile menu */}
      {(isMobileMenuOpen || isUserMenuOpen) && (
        <div
          style={styles.overlay}
          onClick={() => {
            setIsMobileMenuOpen(false);
            setIsUserMenuOpen(false);
          }}
        />
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    backgroundColor: colors.gray[50],
  },
  nav: {
    backgroundColor: 'white',
    borderBottom: `1px solid ${colors.gray[200]}`,
    position: 'sticky',
    top: 0,
    zIndex: 100,
    boxShadow: shadows.sm,
  },
  navContent: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: `${spacing.md} ${spacing.xl}`,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xl,
  },
  navBrand: {
    display: 'flex',
    alignItems: 'center',
  },
  brandLink: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    textDecoration: 'none',
    color: colors.gray[900],
    fontWeight: typography.fontWeight.bold,
  },
  logo: {
    width: '40px',
    height: '40px',
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary.light,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: colors.primary.main,
  },
  brandText: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
  },
  navLinks: {
    display: 'flex',
    gap: spacing.sm,
    flex: 1,
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    textDecoration: 'none',
    color: colors.gray[600],
    fontWeight: typography.fontWeight.medium,
    padding: `${spacing.sm} ${spacing.md}`,
    borderRadius: borderRadius.md,
    transition: `all ${transitions.base}`,
    fontSize: typography.fontSize.sm,
  },
  navLinkActive: {
    backgroundColor: colors.primary.light,
    color: colors.primary.main,
  },
  navLinkIcon: {
    display: 'flex',
    alignItems: 'center',
  },
  navUser: {
    position: 'relative',
  },
  userButton: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    padding: `${spacing.xs} ${spacing.sm}`,
    border: `1px solid ${colors.gray[200]}`,
    borderRadius: borderRadius.md,
    backgroundColor: 'white',
    cursor: 'pointer',
    transition: `all ${transitions.base}`,
  },
  avatar: {
    width: '32px',
    height: '32px',
    borderRadius: borderRadius.full,
    backgroundColor: colors.primary.main,
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semibold,
  },
  userEmail: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[700],
    maxWidth: '150px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  userDropdown: {
    position: 'absolute',
    top: 'calc(100% + 8px)',
    right: 0,
    backgroundColor: 'white',
    borderRadius: borderRadius.lg,
    boxShadow: shadows.lg,
    minWidth: '240px',
    border: `1px solid ${colors.gray[200]}`,
    overflow: 'hidden',
  },
  userDropdownHeader: {
    padding: spacing.md,
    borderBottom: `1px solid ${colors.gray[200]}`,
  },
  userDropdownEmail: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  userDropdownRole: {
    fontSize: typography.fontSize.xs,
    color: colors.gray[500],
  },
  userDropdownDivider: {
    height: '1px',
    backgroundColor: colors.gray[200],
  },
  signOutButton: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.md,
    border: 'none',
    backgroundColor: 'transparent',
    color: colors.error.main,
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    cursor: 'pointer',
    textAlign: 'left',
    transition: `all ${transitions.base}`,
  },
  mobileMenuButton: {
    display: 'none',
    padding: spacing.sm,
    border: 'none',
    backgroundColor: 'transparent',
    color: colors.gray[600],
    cursor: 'pointer',
  },
  mobileMenu: {
    display: 'none',
    flexDirection: 'column',
    padding: spacing.md,
    borderTop: `1px solid ${colors.gray[200]}`,
    backgroundColor: 'white',
  },
  mobileNavLink: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.md,
    textDecoration: 'none',
    color: colors.gray[700],
    fontWeight: typography.fontWeight.medium,
    borderRadius: borderRadius.md,
    transition: `all ${transitions.base}`,
  },
  mobileNavLinkActive: {
    backgroundColor: colors.primary.light,
    color: colors.primary.main,
  },
  mobileMenuDivider: {
    height: '1px',
    backgroundColor: colors.gray[200],
    margin: `${spacing.md} 0`,
  },
  mobileSignOutButton: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.md,
    border: 'none',
    backgroundColor: 'transparent',
    color: colors.error.main,
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    cursor: 'pointer',
    textAlign: 'left',
    borderRadius: borderRadius.md,
  },
  main: {
    minHeight: 'calc(100vh - 73px)',
  },
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 99,
  },
};

// Media query styles (add to index.css)
const mediaQueryStyles = `
@media (max-width: 1024px) {
  .navLinks {
    display: none !important;
  }
  
  .mobileMenuButton {
    display: flex !important;
  }
  
  .mobileMenu {
    display: flex !important;
  }
  
  .userEmail {
    display: none !important;
  }
}
`;

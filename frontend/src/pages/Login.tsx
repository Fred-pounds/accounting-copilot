import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { signIn, isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (searchParams.get('timeout') === 'true') {
      setError('Your session has expired due to inactivity. Please sign in again.');
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await signIn(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Failed to sign in. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Background decoration */}
      <div style={styles.backgroundDecoration} />
      
      <div style={styles.card} className="animate-slide-in">
        {/* Logo/Icon */}
        <div style={styles.logoContainer}>
          <div style={styles.logo}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke={colors.primary.main} strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
        </div>

        <h1 style={styles.title}>Welcome Back</h1>
        <p style={styles.subtitle}>Sign in to your AI Accounting Copilot</p>

        {error && (
          <div style={mergeStyles(components.alert.base, components.alert.error)} role="alert">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formGroup}>
            <label htmlFor="email" style={styles.label}>
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              style={styles.input}
              placeholder="you@company.com"
              aria-label="Email address"
            />
          </div>

          <div style={styles.formGroup}>
            <label htmlFor="password" style={styles.label}>
              Password
            </label>
            <div style={styles.passwordContainer}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                style={styles.passwordInput}
                placeholder="Enter your password"
                aria-label="Password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={styles.passwordToggle}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd"/>
                    <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                    <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                  </svg>
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={mergeStyles(
              components.button.base,
              components.button.primary,
              styles.submitButton,
              isLoading && styles.buttonDisabled
            )}
            aria-busy={isLoading}
          >
            {isLoading ? (
              <>
                <svg style={styles.spinner} width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25"/>
                  <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" opacity="0.75"/>
                </svg>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div style={styles.footer}>
          <p style={styles.footerText}>
            Secure authentication powered by AWS Cognito
          </p>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: colors.gray[50],
    padding: spacing.xl,
    position: 'relative',
    overflow: 'hidden',
  },
  backgroundDecoration: {
    position: 'absolute',
    top: '-50%',
    right: '-50%',
    width: '100%',
    height: '100%',
    background: `radial-gradient(circle, ${colors.primary.light} 0%, transparent 70%)`,
    opacity: 0.3,
    pointerEvents: 'none',
  },
  card: {
    backgroundColor: 'white',
    padding: spacing['2xl'],
    borderRadius: borderRadius.xl,
    boxShadow: shadows.xl,
    width: '100%',
    maxWidth: '440px',
    position: 'relative',
    zIndex: 1,
  },
  logoContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  logo: {
    width: '64px',
    height: '64px',
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary.light,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: typography.fontWeight.bold,
    marginBottom: spacing.sm,
    textAlign: 'center',
    color: colors.gray[900],
  },
  subtitle: {
    color: colors.gray[600],
    marginBottom: spacing.xl,
    textAlign: 'center',
    fontSize: typography.fontSize.base,
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.lg,
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
  },
  label: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[700],
  },
  input: {
    ...components.input.base,
    padding: `${spacing.md} ${spacing.md}`,
  },
  passwordContainer: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  passwordInput: {
    ...components.input.base,
    padding: `${spacing.md} ${spacing['2xl']} ${spacing.md} ${spacing.md}`,
    paddingRight: '3rem',
  },
  passwordToggle: {
    position: 'absolute',
    right: spacing.md,
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: colors.gray[500],
    padding: spacing.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.sm,
  },
  submitButton: {
    marginTop: spacing.sm,
    padding: `${spacing.md} ${spacing.xl}`,
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semibold,
  },
  buttonDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
    transform: 'none',
  },
  spinner: {
    animation: 'spin 1s linear infinite',
  },
  footer: {
    marginTop: spacing.xl,
    paddingTop: spacing.lg,
    borderTop: `1px solid ${colors.gray[200]}`,
    textAlign: 'center',
  },
  footerText: {
    fontSize: typography.fontSize.xs,
    color: colors.gray[500],
  },
};

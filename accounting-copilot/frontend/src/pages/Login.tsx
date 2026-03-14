import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { signIn, isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();

  useEffect(() => { if (isAuthenticated) navigate('/dashboard'); }, [isAuthenticated, navigate]);
  useEffect(() => {
    if (searchParams.get('timeout') === 'true')
      setError('Your session expired. Please sign in again.');
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await signIn(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={s.page}>
      {/* Left panel — branding */}
      <div style={s.left}>
        <div style={s.leftInner}>
          <div style={s.logoWrap}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h1 style={s.leftTitle}>AI Accounting Copilot</h1>
          <p style={s.leftSub}>AI-powered accounting for modern businesses</p>

          <div style={s.features}>
            {[
              { icon: '⚡', text: 'Instant transaction classification' },
              { icon: '🔍', text: 'Smart document OCR processing' },
              { icon: '💬', text: 'AI financial assistant' },
              { icon: '🔒', text: 'Bank-grade security & encryption' },
            ].map((f) => (
              <div key={f.text} style={s.featureItem}>
                <span style={s.featureIcon}>{f.icon}</span>
                <span style={s.featureText}>{f.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Decorative orbs */}
        <div style={s.orb1} />
        <div style={s.orb2} />
      </div>

      {/* Right panel — form */}
      <div style={s.right}>
        <div style={s.formCard}>
          <div style={s.formHeader}>
            <h2 style={s.formTitle}>Welcome back</h2>
            <p style={s.formSub}>Sign in to your account</p>
          </div>

          {error && (
            <div style={s.errorBox}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={s.form}>
            <div style={s.field}>
              <label htmlFor="email" style={s.label}>Email address</label>
              <div style={s.inputWrap}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" style={s.inputIcon}>
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
                <input
                  id="email" type="email" value={email} required
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  style={s.input}
                />
              </div>
            </div>

            <div style={s.field}>
              <label htmlFor="password" style={s.label}>Password</label>
              <div style={s.inputWrap}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" style={s.inputIcon}>
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input
                  id="password" type="password" value={password} required
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  style={s.input}
                />
              </div>
            </div>

            <button type="submit" disabled={isLoading} style={{ ...s.btn, ...(isLoading ? s.btnDisabled : {}) }}>
              {isLoading ? (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.8s linear infinite' }}>
                    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                  </svg>
                  Signing in…
                </span>
              ) : 'Sign In'}
            </button>
          </form>

          <p style={s.footer}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline', marginRight: 4 }}>
              <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            Secured with end-to-end encryption
          </p>
        </div>
      </div>
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  page: { display: 'flex', minHeight: '100vh', fontFamily: 'Inter, sans-serif' },

  /* Left branding panel */
  left: {
    flex: '0 0 45%', position: 'relative', overflow: 'hidden',
    background: 'linear-gradient(145deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  leftInner: { position: 'relative', zIndex: 1, padding: '3rem', maxWidth: 400 },
  logoWrap: {
    width: 52, height: 52, borderRadius: 14,
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    marginBottom: 20, boxShadow: '0 8px 24px rgba(99,102,241,0.45)',
  },
  leftTitle: { fontSize: '2rem', fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.5px', marginBottom: 10 },
  leftSub: { fontSize: '1rem', color: 'rgba(148,163,184,0.85)', lineHeight: 1.6, marginBottom: 36 },
  features: { display: 'flex', flexDirection: 'column', gap: 14 },
  featureItem: { display: 'flex', alignItems: 'center', gap: 12 },
  featureIcon: { fontSize: '1.1rem', width: 28, textAlign: 'center' as const },
  featureText: { fontSize: '0.875rem', color: 'rgba(199,210,254,0.8)', fontWeight: 500 },
  orb1: {
    position: 'absolute', width: 500, height: 500, borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)',
    top: -150, right: -150, pointerEvents: 'none',
  },
  orb2: {
    position: 'absolute', width: 350, height: 350, borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)',
    bottom: -100, left: -80, pointerEvents: 'none',
  },

  /* Right form panel */
  right: {
    flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
    backgroundColor: '#f8fafc', padding: '2rem',
  },
  formCard: {
    width: '100%', maxWidth: 400,
    backgroundColor: '#ffffff',
    borderRadius: 20, padding: '40px 36px',
    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)',
    animation: 'slideUp 0.4s ease-out',
  },
  formHeader: { marginBottom: 28 },
  formTitle: { fontSize: '1.5rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.3px', marginBottom: 4 },
  formSub: { fontSize: '0.875rem', color: '#64748b' },
  errorBox: {
    display: 'flex', alignItems: 'center', gap: 8,
    backgroundColor: '#fef2f2', color: '#dc2626',
    padding: '11px 14px', borderRadius: 10, marginBottom: 20,
    fontSize: '0.83rem', border: '1px solid #fecaca', fontWeight: 500,
  },
  form: { display: 'flex', flexDirection: 'column', gap: 18 },
  field: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: '0.78rem', fontWeight: 600, color: '#374151', letterSpacing: '0.1px' },
  inputWrap: { position: 'relative', display: 'flex', alignItems: 'center' },
  inputIcon: { position: 'absolute', left: 13, pointerEvents: 'none' },
  input: {
    width: '100%', padding: '11px 13px 11px 40px',
    border: '1.5px solid #e2e8f0', borderRadius: 10,
    fontSize: '0.9rem', color: '#1e293b', backgroundColor: '#f8fafc',
    transition: 'all 0.18s', outline: 'none', fontFamily: 'inherit',
  },
  btn: {
    padding: '12px', marginTop: 4,
    background: 'linear-gradient(135deg, #6366f1, #7c3aed)',
    color: 'white', border: 'none', borderRadius: 10,
    fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer',
    boxShadow: '0 4px 14px rgba(99,102,241,0.35)', fontFamily: 'inherit',
    transition: 'all 0.18s',
  },
  btnDisabled: { background: '#cbd5e1', cursor: 'not-allowed', boxShadow: 'none' },
  footer: { textAlign: 'center' as const, marginTop: 22, fontSize: '0.75rem', color: '#94a3b8' },
};

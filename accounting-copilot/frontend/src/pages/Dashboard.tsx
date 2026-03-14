import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Area, AreaChart, ReferenceLine,
} from 'recharts';
import { apiClient } from '../services/api';
import type { DashboardSummary } from '../types';

const fmt = (v: number) =>
  '$' + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });

const tooltipStyle = {
  backgroundColor: '#1e293b',
  border: 'none',
  borderRadius: '10px',
  color: '#f1f5f9',
  fontSize: '0.82rem',
  boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
};

export const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const loadDashboard = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await apiClient.getDashboardSummary();
      setSummary(data);
      setLastRefresh(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading && !summary) return <LoadingSkeleton />;
  if (error) return <ErrorCard error={error} onRetry={loadDashboard} />;
  if (!summary) return null;

  const profit = summary.total_income - summary.total_expenses;

  const kpiCards = [
    {
      label: 'Cash Balance',
      value: summary.cash_balance,
      color: '#6366f1',
      lightBg: '#eef2ff',
      gradient: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
      icon: <WalletIcon />,
    },
    {
      label: 'Total Income',
      value: summary.total_income,
      color: '#059669',
      lightBg: '#ecfdf5',
      gradient: 'linear-gradient(135deg,#059669,#10b981)',
      icon: <ArrowUpIcon />,
      change: null,
    },
    {
      label: 'Total Expenses',
      value: summary.total_expenses,
      color: '#e11d48',
      lightBg: '#fff1f2',
      gradient: 'linear-gradient(135deg,#e11d48,#f43f5e)',
      icon: <ArrowDownIcon />,
    },
    {
      label: 'Net Profit',
      value: profit,
      color: profit >= 0 ? '#d97706' : '#e11d48',
      lightBg: profit >= 0 ? '#fffbeb' : '#fff1f2',
      gradient: profit >= 0
        ? 'linear-gradient(135deg,#f59e0b,#fbbf24)'
        : 'linear-gradient(135deg,#e11d48,#f43f5e)',
      icon: <TrendIcon />,
    },
  ];

  return (
    <div style={s.container}>
      {/* Header */}
      <div style={s.header}>
        <div>
          <h1 style={s.title}>Dashboard</h1>
          <p style={s.subtitle}>Financial overview • Last updated {lastRefresh.toLocaleTimeString()}</p>
        </div>
        <button onClick={loadDashboard} style={s.refreshBtn} title="Refresh">
          <RefreshIcon />
        </button>
      </div>

      {/* KPI Cards */}
      <div style={s.cardsGrid}>
        {kpiCards.map((card, i) => (
          <div key={card.label} style={{ ...s.card, animationDelay: `${i * 0.07}s` }}>
            <div style={s.cardTop}>
              <span style={s.cardLabel}>{card.label}</span>
              <div style={{ ...s.iconWrap, background: card.lightBg, color: card.color }}>
                {card.icon}
              </div>
            </div>
            <div style={{ ...s.cardValue, color: card.color }}>{fmt(card.value)}</div>
            <div style={{ ...s.cardBar, background: card.gradient }} />
          </div>
        ))}
      </div>

      {/* Pending approvals banner */}
      {(summary.pending_approvals_count ?? 0) > 0 && (
        <Link to="/approvals" style={s.approvalBanner}>
          <div style={s.approvalIcon}><AlertIcon /></div>
          <div style={{ flex: 1 }}>
            <strong>{summary.pending_approvals_count} pending approval{(summary.pending_approvals_count ?? 0) > 1 ? 's' : ''}</strong>
            <div style={{ fontSize: '0.78rem', opacity: 0.7 }}>Items require your review</div>
          </div>
          <ChevronIcon />
        </Link>
      )}

      {/* Charts row */}
      <div style={s.chartsGrid}>
        {/* Income vs Expenses area chart */}
        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <div>
              <h2 style={s.chartTitle}>Income vs Expenses</h2>
              <p style={s.chartSub}>Monthly overview</p>
            </div>
            <div style={s.legendRow}>
              <span style={{ ...s.dot, background: '#10b981' }} /> Income
              <span style={{ ...s.dot, background: '#f43f5e', marginLeft: 12 }} /> Expenses
            </div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={summary.profit_trend} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={(v) => v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`} />
              <Tooltip
                formatter={(v: number, name: string) => [fmt(v), name]}
                contentStyle={tooltipStyle}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Area type="monotone" dataKey="income" stroke="#10b981" strokeWidth={2.5}
                fill="url(#incomeGrad)" name="Income"
                dot={{ fill: '#10b981', r: 4, strokeWidth: 0 }}
                activeDot={{ r: 6, strokeWidth: 0 }} />
              <Area type="monotone" dataKey="expenses" stroke="#f43f5e" strokeWidth={2.5}
                fill="url(#expenseGrad)" name="Expenses"
                dot={{ fill: '#f43f5e', r: 4, strokeWidth: 0 }}
                activeDot={{ r: 6, strokeWidth: 0 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly Profit bar chart */}
        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <div>
              <h2 style={s.chartTitle}>Monthly Profit Trend</h2>
              <p style={s.chartSub}>Net profit per month</p>
            </div>
            <div style={s.legendRow}>
              <span style={{ ...s.dot, background: '#10b981' }} /> Profit
              <span style={{ ...s.dot, background: '#e11d48', marginLeft: 12 }} /> Loss
            </div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={summary.profit_trend} barSize={28} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={(v) => `$${Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`} />
              <ReferenceLine y={0} stroke="#cbd5e1" strokeWidth={1.5} />
              <Tooltip
                formatter={(v: number) => [fmt(v), v >= 0 ? 'Profit' : 'Loss']}
                contentStyle={tooltipStyle}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Bar dataKey="profit" radius={[4, 4, 4, 4]} name="Profit">
                {summary.profit_trend.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.profit >= 0 ? '#10b981' : '#e11d48'} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Expense Categories */}
      {summary.top_categories?.length > 0 && (
        <div style={{ ...s.chartCard, marginTop: 20 }}>
          <div style={s.chartHeader}>
            <div>
              <h2 style={s.chartTitle}>Top Expense Categories</h2>
              <p style={s.chartSub}>Highest spending areas</p>
            </div>
            <span style={s.badge}>Top {summary.top_categories.length}</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={summary.top_categories} barSize={36} layout="vertical"
              margin={{ top: 0, right: 16, left: 80, bottom: 0 }}>
              <defs>
                <linearGradient id="catGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#e11d48" stopOpacity={0.85} />
                  <stop offset="100%" stopColor="#f97316" stopOpacity={0.7} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={(v) => v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`} />
              <YAxis type="category" dataKey="category" tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={false} tickLine={false} width={76} />
              <Tooltip
                formatter={(v: number) => [fmt(v), 'Amount']}
                contentStyle={tooltipStyle}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Bar dataKey="total" fill="url(#catGrad)" radius={[0, 6, 6, 0]} name="Amount" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

/* ── Small sub-components ── */
const LoadingSkeleton = () => (
  <div style={s.container}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 28 }}>
      <div style={sk.title} />
      <div style={sk.btn} />
    </div>
    <div style={s.cardsGrid}>
      {[1, 2, 3, 4].map(i => (
        <div key={i} style={{ ...s.card, padding: 24 }}>
          <div style={sk.line} />
          <div style={sk.value} />
        </div>
      ))}
    </div>
  </div>
);

const ErrorCard = ({ error, onRetry }: { error: string; onRetry: () => void }) => (
  <div style={s.container}>
    <div style={s.errorCard}>
      <p style={{ color: '#e11d48', fontWeight: 600 }}>{error}</p>
      <button onClick={onRetry} style={s.retryBtn}>Retry</button>
    </div>
  </div>
);

/* ── Icons ── */
const WalletIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="5" width="20" height="14" rx="2" /><line x1="2" y1="10" x2="22" y2="10" />
  </svg>
);
const ArrowUpIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" />
  </svg>
);
const ArrowDownIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" /><polyline points="19 12 12 19 5 12" />
  </svg>
);
const TrendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);
const RefreshIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
  </svg>
);
const AlertIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);
const ChevronIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

/* ── Styles ── */
const s: Record<string, React.CSSProperties> = {
  container: { padding: 'var(--space-page)', maxWidth: 1400, margin: '0 auto' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 },
  title: { fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.5px' },
  subtitle: { fontSize: '0.83rem', color: 'var(--color-text-muted)', marginTop: 4 },
  refreshBtn: {
    width: 40, height: 40, borderRadius: 10, border: '1px solid var(--color-border)',
    backgroundColor: 'var(--color-card)', color: 'var(--color-text-secondary)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
  },
  cardsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 20, marginBottom: 24 },
  card: {
    position: 'relative', backgroundColor: 'var(--color-card)', borderRadius: 'var(--radius-lg)',
    padding: '22px 24px', boxShadow: 'var(--shadow-sm)', overflow: 'hidden',
    animation: 'slideUp 0.4s ease-out both',
  },
  cardTop: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 },
  cardLabel: { fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.7px' },
  iconWrap: { width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  cardValue: { fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-0.5px', lineHeight: 1.2 },
  cardBar: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 3 },
  approvalBanner: {
    display: 'flex', alignItems: 'center', gap: 14, padding: '14px 18px',
    backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-lg)',
    marginBottom: 24, textDecoration: 'none', color: '#92400e',
  },
  approvalIcon: {
    width: 38, height: 38, borderRadius: 10, backgroundColor: '#fef3c7',
    display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#d97706', flexShrink: 0,
  },
  chartsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(460px,1fr))', gap: 20 },
  chartCard: {
    backgroundColor: 'var(--color-card)', padding: '22px 24px',
    borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-sm)',
    animation: 'slideUp 0.5s ease-out both',
  },
  chartHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 },
  chartTitle: { fontSize: '1rem', fontWeight: 700, color: 'var(--color-text)' },
  chartSub: { fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: 2 },
  legendRow: { display: 'flex', alignItems: 'center', fontSize: '0.78rem', color: 'var(--color-text-secondary)' },
  dot: { display: 'inline-block', width: 10, height: 10, borderRadius: '50%', marginRight: 5 },
  badge: {
    fontSize: '0.75rem', color: 'var(--color-text-muted)', backgroundColor: 'var(--color-surface)',
    padding: '3px 10px', borderRadius: 'var(--radius-full)',
  },
  errorCard: {
    textAlign: 'center', padding: '3rem', backgroundColor: 'var(--color-card)',
    borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
  },
  retryBtn: {
    padding: '8px 20px', backgroundColor: 'var(--color-primary)', color: 'white',
    border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'inherit', fontWeight: 600,
  },
};

const sk: Record<string, React.CSSProperties> = {
  title: { width: 180, height: 32, borderRadius: 8, background: 'linear-gradient(90deg,#f1f5f9,#e2e8f0,#f1f5f9)', backgroundSize: '200% 100%' },
  btn: { width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(90deg,#f1f5f9,#e2e8f0,#f1f5f9)', backgroundSize: '200% 100%' },
  line: { width: 100, height: 14, borderRadius: 6, background: 'linear-gradient(90deg,#f1f5f9,#e2e8f0,#f1f5f9)', backgroundSize: '200% 100%', marginBottom: 16 },
  value: { width: 140, height: 28, borderRadius: 6, background: 'linear-gradient(90deg,#f1f5f9,#e2e8f0,#f1f5f9)', backgroundSize: '200% 100%' },
};

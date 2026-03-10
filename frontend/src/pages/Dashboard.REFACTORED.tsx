/**
 * REFACTORED DASHBOARD - Modern UI/UX
 * 
 * Copy this entire file content and replace the content of Dashboard.tsx
 * 
 * Improvements:
 * - Modern metric cards with icons
 * - Better loading states
 * - Enhanced error handling
 * - Improved chart styling
 * - Quick actions section
 * - Better responsive layout
 * - Smooth animations
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiClient } from '../services/api';
import type { DashboardSummary } from '../types';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

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
    const interval = setInterval(() => {
      loadDashboard();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Loading State
  if (isLoading && !summary) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingContainer}>
          <div style={styles.spinner}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
              <circle cx="12" cy="12" r="10" stroke={colors.gray[300]} strokeWidth="4"/>
              <path fill={colors.primary.main} d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
          </div>
          <p style={styles.loadingText}>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div style={styles.container}>
        <div style={mergeStyles(components.alert.base, components.alert.error)}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
          </svg>
          <div>
            <div style={{ fontWeight: typography.fontWeight.semibold, marginBottom: spacing.xs }}>Failed to load dashboard</div>
            <div>{error}</div>
          </div>
        </div>
        <button 
          onClick={loadDashboard} 
          style={mergeStyles(components.button.base, components.button.primary, { marginTop: spacing.md })}
        >
          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"/>
          </svg>
          Retry
        </button>
      </div>
    );
  }

  if (!summary) return null;

  const profit = summary.total_income - summary.total_expenses;

  return (
    <div style={styles.container} className="animate-fade-in">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Dashboard</h1>
          <p style={styles.subtitle}>Welcome back! Here's your financial overview.</p>
        </div>
        <div style={styles.headerActions}>
          <div style={styles.refreshInfo}>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" style={{ color: colors.gray[400] }}>
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/>
            </svg>
            <span>Updated {lastRefresh.toLocaleTimeString()}</span>
          </div>
          <button 
            onClick={loadDashboard}
            style={mergeStyles(components.button.base, components.button.outline)}
            aria-label="Refresh dashboard"
          >
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Pending Approvals Banner */}
      {summary.pending_approvals_count > 0 && (
        <Link to="/approvals" style={styles.approvalsBanner} className="animate-slide-in">
          <div style={styles.approvalsContent}>
            <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor" style={{ color: colors.warning.main }}>
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
            </svg>
            <div>
              <div style={{ fontWeight: typography.fontWeight.semibold, marginBottom: spacing.xs }}>
                {summary.pending_approvals_count} Pending Approval{summary.pending_approvals_count > 1 ? 's' : ''}
              </div>
              <div style={{ fontSize: typography.fontSize.sm }}>
                Review and approve transactions that require your attention
              </div>
            </div>
          </div>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style={{ color: colors.warning.dark }}>
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
          </svg>
        </Link>
      )}

      {/* Metric Cards - CONTINUED IN NEXT COMMENT */}

      {/* Metric Cards */}
      <div style={styles.metricsGrid}>
        {/* Cash Balance Card */}
        <div style={styles.metricCard} className="animate-slide-in">
          <div style={styles.metricHeader}>
            <div style={{ ...styles.metricIcon, backgroundColor: colors.primary.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.primary.main}>
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/>
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd"/>
              </svg>
            </div>
            <div style={styles.metricLabel}>Cash Balance</div>
          </div>
          <div style={styles.metricValue}>
            ${summary.cash_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={styles.metricFooter}>
            <span style={{ color: colors.gray[500], fontSize: typography.fontSize.sm }}>
              Current available balance
            </span>
          </div>
        </div>

        {/* Total Income Card */}
        <div style={styles.metricCard} className="animate-slide-in">
          <div style={styles.metricHeader}>
            <div style={{ ...styles.metricIcon, backgroundColor: colors.success.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.success.main}>
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd"/>
              </svg>
            </div>
            <div style={styles.metricLabel}>Total Income</div>
          </div>
          <div style={{ ...styles.metricValue, color: colors.success.main }}>
            +${summary.total_income.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={styles.metricFooter}>
            <span style={{ color: colors.gray[500], fontSize: typography.fontSize.sm }}>
              This month
            </span>
          </div>
        </div>

        {/* Total Expenses Card */}
        <div style={styles.metricCard} className="animate-slide-in">
          <div style={styles.metricHeader}>
            <div style={{ ...styles.metricIcon, backgroundColor: colors.error.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.error.main}>
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd"/>
              </svg>
            </div>
            <div style={styles.metricLabel}>Total Expenses</div>
          </div>
          <div style={{ ...styles.metricValue, color: colors.error.main }}>
            -${summary.total_expenses.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={styles.metricFooter}>
            <span style={{ color: colors.gray[500], fontSize: typography.fontSize.sm }}>
              This month
            </span>
          </div>
        </div>

        {/* Net Profit Card */}
        <div style={styles.metricCard} className="animate-slide-in">
          <div style={styles.metricHeader}>
            <div style={{ 
              ...styles.metricIcon, 
              backgroundColor: profit >= 0 ? colors.success.light : colors.error.light 
            }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={profit >= 0 ? colors.success.main : colors.error.main}>
                <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
              </svg>
            </div>
            <div style={styles.metricLabel}>Net Profit</div>
          </div>
          <div style={{ ...styles.metricValue, color: profit >= 0 ? colors.success.main : colors.error.main }}>
            {profit >= 0 ? '+' : ''}${profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={styles.metricFooter}>
            <span style={{ color: colors.gray[500], fontSize: typography.fontSize.sm }}>
              Income - Expenses
            </span>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div style={styles.chartsGrid}>
        {/* Profit Trend Chart */}
        <div style={styles.chartCard} className="animate-slide-in">
          <div style={styles.chartHeader}>
            <div>
              <h2 style={styles.chartTitle}>Profit Trend</h2>
              <p style={styles.chartSubtitle}>Last 6 months performance</p>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={summary.profit_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.gray[200]} />
              <XAxis 
                dataKey="month" 
                stroke={colors.gray[400]}
                style={{ fontSize: typography.fontSize.sm }}
              />
              <YAxis 
                stroke={colors.gray[400]}
                style={{ fontSize: typography.fontSize.sm }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: `1px solid ${colors.gray[200]}`,
                  borderRadius: borderRadius.md,
                  boxShadow: shadows.md,
                }}
                formatter={(value: number) =>
                  `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                }
              />
              <Legend wrapperStyle={{ fontSize: typography.fontSize.sm }} />
              <Line
                type="monotone"
                dataKey="profit"
                stroke={colors.primary.main}
                strokeWidth={3}
                name="Profit"
                dot={{ fill: colors.primary.main, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Categories Chart */}
        <div style={styles.chartCard} className="animate-slide-in">
          <div style={styles.chartHeader}>
            <div>
              <h2 style={styles.chartTitle}>Top Expense Categories</h2>
              <p style={styles.chartSubtitle}>This month's spending breakdown</p>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={summary.top_categories}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.gray[200]} />
              <XAxis 
                dataKey="category" 
                stroke={colors.gray[400]}
                style={{ fontSize: typography.fontSize.sm }}
              />
              <YAxis 
                stroke={colors.gray[400]}
                style={{ fontSize: typography.fontSize.sm }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: `1px solid ${colors.gray[200]}`,
                  borderRadius: borderRadius.md,
                  boxShadow: shadows.md,
                }}
                formatter={(value: number) =>
                  `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                }
              />
              <Legend wrapperStyle={{ fontSize: typography.fontSize.sm }} />
              <Bar 
                dataKey="amount" 
                fill={colors.error.main} 
                name="Amount"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={styles.quickActions}>
        <h2 style={styles.sectionTitle}>Quick Actions</h2>
        <div style={styles.actionsGrid}>
          <Link to="/upload" style={styles.actionCard}>
            <div style={{ ...styles.actionIcon, backgroundColor: colors.primary.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.primary.main}>
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd"/>
              </svg>
            </div>
            <div style={styles.actionContent}>
              <div style={styles.actionTitle}>Upload Document</div>
              <div style={styles.actionDescription}>Add receipts, invoices, or statements</div>
            </div>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style={{ color: colors.gray[400] }}>
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
            </svg>
          </Link>

          <Link to="/assistant" style={styles.actionCard}>
            <div style={{ ...styles.actionIcon, backgroundColor: colors.info.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.info.main}>
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
              </svg>
            </div>
            <div style={styles.actionContent}>
              <div style={styles.actionTitle}>Ask Assistant</div>
              <div style={styles.actionDescription}>Get insights about your finances</div>
            </div>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style={{ color: colors.gray[400] }}>
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
            </svg>
          </Link>

          <Link to="/transactions" style={styles.actionCard}>
            <div style={{ ...styles.actionIcon, backgroundColor: colors.secondary.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.secondary.main}>
                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"/>
              </svg>
            </div>
            <div style={styles.actionContent}>
              <div style={styles.actionTitle}>View Transactions</div>
              <div style={styles.actionDescription}>Browse and manage all transactions</div>
            </div>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style={{ color: colors.gray[400] }}>
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
};

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: spacing.xl,
    maxWidth: '1400px',
    margin: '0 auto',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '400px',
    gap: spacing.lg,
  },
  spinner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: typography.fontSize.lg,
    color: colors.gray[600],
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.xl,
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  title: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: typography.fontWeight.bold,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: typography.fontSize.base,
    color: colors.gray[600],
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
  },
  refreshInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    fontSize: typography.fontSize.sm,
    color: colors.gray[500],
  },
  approvalsBanner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.warning.light,
    border: `1px solid ${colors.warning.main}`,
    padding: spacing.lg,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.xl,
    textDecoration: 'none',
    color: colors.warning.dark,
    transition: `all ${transitions.base}`,
  },
  approvalsContent: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: spacing.lg,
    marginBottom: spacing.xl,
  },
  metricCard: {
    ...components.card.base,
    transition: `all ${transitions.base}`,
  },
  metricHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  metricIcon: {
    width: '48px',
    height: '48px',
    borderRadius: borderRadius.lg,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[600],
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  metricValue: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: typography.fontWeight.bold,
    color: colors.gray[900],
    marginBottom: spacing.sm,
  },
  metricFooter: {
    paddingTop: spacing.sm,
    borderTop: `1px solid ${colors.gray[200]}`,
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
    gap: spacing.lg,
    marginBottom: spacing.xl,
  },
  chartCard: {
    ...components.card.base,
  },
  chartHeader: {
    marginBottom: spacing.lg,
  },
  chartTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  chartSubtitle: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[500],
  },
  quickActions: {
    marginTop: spacing.xl,
  },
  sectionTitle: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.lg,
  },
  actionsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: spacing.lg,
  },
  actionCard: {
    ...components.card.base,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
    textDecoration: 'none',
    color: colors.gray[900],
    transition: `all ${transitions.base}`,
    cursor: 'pointer',
  },
  actionIcon: {
    width: '48px',
    height: '48px',
    borderRadius: borderRadius.lg,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  actionDescription: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[600],
  },
};

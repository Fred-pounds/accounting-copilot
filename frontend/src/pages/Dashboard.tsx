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

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      loadDashboard();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading && !summary) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingContainer}>
          <div style={styles.spinner}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke={colors.gray[300]} strokeWidth="4"/>
              <path fill={colors.primary.main} d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
          </div>
          <p style={styles.loadingText}>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={mergeStyles(components.alert.base, components.alert.error)}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
          </svg>
          <div>
            <div style={styles.errorTitle}>Failed to load dashboard</div>
            <div style={styles.errorMessage}>{error}</div>
          </div>
        </div>
        <button 
          onClick={loadDashboard} 
          style={mergeStyles(components.button.base, components.button.primary, styles.retryButton)}
        >
          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"/>
          </svg>
          Retry
        </button>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  const profit = summary.total_income - summary.total_expenses;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Dashboard</h1>
        <div style={styles.refreshInfo}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </div>
      </div>

      {/* Summary Cards */}
      <div style={styles.cardsGrid}>
        <div style={styles.card}>
          <div style={styles.cardLabel}>Cash Balance</div>
          <div style={styles.cardValue}>
            ${summary.cash_balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardLabel}>Total Income</div>
          <div style={{ ...styles.cardValue, color: '#28a745' }}>
            ${summary.total_income.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardLabel}>Total Expenses</div>
          <div style={{ ...styles.cardValue, color: '#dc3545' }}>
            ${summary.total_expenses.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardLabel}>Net Profit</div>
          <div
            style={{
              ...styles.cardValue,
              color: profit >= 0 ? '#28a745' : '#dc3545',
            }}
          >
            ${profit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Pending Approvals Badge */}
      {summary.pending_approvals_count > 0 && (
        <Link to="/approvals" style={styles.approvalsBanner}>
          <span style={styles.approvalsBadge}>{summary.pending_approvals_count}</span>
          <span>
            You have {summary.pending_approvals_count} pending approval
            {summary.pending_approvals_count > 1 ? 's' : ''}
          </span>
          <span style={styles.approvalsLink}>Review →</span>
        </Link>
      )}

      {/* Charts */}
      <div style={styles.chartsGrid}>
        {/* Profit Trend Chart */}
        <div style={styles.chartCard}>
          <h2 style={styles.chartTitle}>Profit Trend (Last 6 Months)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={summary.profit_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip
                formatter={(value: number) =>
                  `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                }
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="profit"
                stroke="#007bff"
                strokeWidth={2}
                name="Profit"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Categories Chart */}
        <div style={styles.chartCard}>
          <h2 style={styles.chartTitle}>Top 5 Expense Categories</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={summary.top_categories}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip
                formatter={(value: number) =>
                  `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                }
              />
              <Legend />
              <Bar dataKey="amount" fill="#dc3545" name="Amount" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '2rem',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '1.875rem',
    fontWeight: 'bold',
  },
  refreshInfo: {
    fontSize: '0.875rem',
    color: '#666',
  },
  loading: {
    textAlign: 'center',
    padding: '3rem',
    fontSize: '1.125rem',
    color: '#666',
  },
  error: {
    backgroundColor: '#fee',
    color: '#c33',
    padding: '1rem',
    borderRadius: '8px',
    marginBottom: '1rem',
  },
  retryButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  cardsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
  },
  card: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  cardLabel: {
    fontSize: '0.875rem',
    color: '#666',
    marginBottom: '0.5rem',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  cardValue: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#333',
  },
  approvalsBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    backgroundColor: '#fff3cd',
    border: '1px solid #ffc107',
    padding: '1rem',
    borderRadius: '8px',
    marginBottom: '2rem',
    textDecoration: 'none',
    color: '#856404',
    fontWeight: '500',
  },
  approvalsBadge: {
    backgroundColor: '#ffc107',
    color: 'white',
    borderRadius: '50%',
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
  },
  approvalsLink: {
    marginLeft: 'auto',
    color: '#007bff',
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
    gap: '1.5rem',
  },
  chartCard: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  chartTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    marginBottom: '1rem',
  },
};

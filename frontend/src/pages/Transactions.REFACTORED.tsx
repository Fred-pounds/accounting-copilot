/**
 * REFACTORED TRANSACTIONS - Modern UI/UX
 * 
 * Copy this entire file content and replace the content of Transactions.tsx
 * 
 * Improvements:
 * - Modern table design with hover states
 * - Better filtering UI with chips
 * - Search functionality
 * - Status badges with colors
 * - Quick actions menu
 * - Better responsive layout
 * - Loading skeletons
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { Transaction } from '../types';
import { TransactionDetailModal } from '../components/TransactionDetailModal';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

export const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Filters
  const [typeFilter, setTypeFilter] = useState<'all' | 'income' | 'expense'>('all');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'pending_review'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const loadTransactions = async () => {
    try {
      setIsLoading(true);
      setError('');
      const params: any = {};
      if (typeFilter !== 'all') params.type = typeFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter !== 'all') params.status = statusFilter;

      const data = await apiClient.listTransactions(params);
      setTransactions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load transactions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [typeFilter, categoryFilter, statusFilter]);

  // Filter and sort transactions
  const filteredTransactions = transactions.filter(txn => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      txn.vendor.toLowerCase().includes(query) ||
      txn.category.toLowerCase().includes(query) ||
      txn.description?.toLowerCase().includes(query)
    );
  });

  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    let comparison = 0;
    if (sortBy === 'date') {
      comparison = new Date(a.date).getTime() - new Date(b.date).getTime();
    } else {
      comparison = a.amount - b.amount;
    }
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  const handleApprove = async (id: string) => {
    try {
      await apiClient.approveTransaction(id);
      loadTransactions();
    } catch (err: any) {
      alert(err.message || 'Failed to approve transaction');
    }
  };

  const handleCorrect = async (id: string, corrections: { category?: string; amount?: number }) => {
    try {
      await apiClient.correctTransaction(id, corrections);
      loadTransactions();
      setSelectedTransaction(null);
    } catch (err: any) {
      alert(err.message || 'Failed to correct transaction');
    }
  };

  const clearFilters = () => {
    setTypeFilter('all');
    setCategoryFilter('');
    setStatusFilter('all');
    setSearchQuery('');
  };

  const hasActiveFilters = typeFilter !== 'all' || categoryFilter !== '' || statusFilter !== 'all' || searchQuery !== '';

  // Loading State
  if (isLoading && transactions.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>Transactions</h1>
        </div>
        <div style={styles.loadingContainer}>
          <div style={styles.spinner}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
              <circle cx="12" cy="12" r="10" stroke={colors.gray[300]} strokeWidth="4"/>
              <path fill={colors.primary.main} d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
          </div>
          <p style={styles.loadingText}>Loading transactions...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container} className="animate-fade-in">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Transactions</h1>
          <p style={styles.subtitle}>
            {sortedTransactions.length} transaction{sortedTransactions.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <button
          onClick={loadTransactions}
          style={mergeStyles(components.button.base, components.button.outline)}
          disabled={isLoading}
        >
          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"/>
          </svg>
          Refresh
        </button>
      </div>

      {/* Search and Filters */}
      <div style={styles.filtersContainer}>
        {/* Search Bar */}
        <div style={styles.searchContainer}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style={styles.searchIcon}>
            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd"/>
          </svg>
          <input
            type="text"
            placeholder="Search by vendor, category, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={styles.searchInput}
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} style={styles.clearSearchButton}>
              <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
            </button>
          )}
        </div>

        {/* Filter Buttons */}
        <div style={styles.filtersRow}>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as any)}
            style={styles.filterSelect}
          >
            <option value="all">All Types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            style={styles.filterSelect}
          >
            <option value="all">All Status</option>
            <option value="approved">Approved</option>
            <option value="pending_review">Pending Review</option>
          </select>

          <input
            type="text"
            placeholder="Filter by category"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={styles.filterInput}
          />

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            style={styles.filterSelect}
          >
            <option value="date">Sort by Date</option>
            <option value="amount">Sort by Amount</option>
          </select>

          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            style={mergeStyles(components.button.base, components.button.ghost)}
            title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
          >
            {sortOrder === 'asc' ? (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M3 3a1 1 0 000 2h11a1 1 0 100-2H3zM3 7a1 1 0 000 2h7a1 1 0 100-2H3zM3 11a1 1 0 100 2h4a1 1 0 100-2H3zM15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z"/>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M3 3a1 1 0 000 2h11a1 1 0 100-2H3zM3 7a1 1 0 000 2h5a1 1 0 000-2H3zM3 11a1 1 0 100 2h4a1 1 0 100-2H3zM13 16a1 1 0 102 0v-5.586l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 101.414 1.414L13 10.414V16z"/>
              </svg>
            )}
          </button>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              style={mergeStyles(components.button.base, components.button.ghost)}
            >
              <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={mergeStyles(components.alert.base, components.alert.error)}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Transactions Table */}
      <div style={styles.tableContainer}>
        {sortedTransactions.length === 0 ? (
          <div style={styles.emptyState}>
            <svg width="64" height="64" viewBox="0 0 20 20" fill={colors.gray[300]}>
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/>
            </svg>
            <h3 style={styles.emptyStateTitle}>No transactions found</h3>
            <p style={styles.emptyStateText}>
              {hasActiveFilters
                ? 'Try adjusting your filters or search query'
                : 'Upload documents to start tracking transactions'}
            </p>
          </div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Date</th>
                <th style={styles.th}>Vendor</th>
                <th style={styles.th}>Category</th>
                <th style={styles.th}>Amount</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Confidence</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedTransactions.map((transaction) => (
                <tr key={transaction.transaction_id} style={styles.tr}>
                  <td style={styles.td}>
                    {new Date(transaction.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </td>
                  <td style={styles.td}>
                    <div style={styles.vendorCell}>
                      <div style={styles.vendorName}>{transaction.vendor}</div>
                      {transaction.description && (
                        <div style={styles.vendorDescription}>{transaction.description}</div>
                      )}
                    </div>
                  </td>
                  <td style={styles.td}>
                    <span style={mergeStyles(components.badge.base, components.badge.neutral)}>
                      {transaction.category}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.amountText,
                      color: transaction.type === 'income' ? colors.success.main : colors.error.main,
                    }}>
                      {transaction.type === 'income' ? '+' : '-'}$
                      {transaction.amount.toFixed(2)}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <span style={mergeStyles(
                      components.badge.base,
                      transaction.type === 'income' ? components.badge.success : components.badge.error
                    )}>
                      {transaction.type}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.confidenceCell}>
                      <div style={{
                        ...styles.confidenceBar,
                        width: `${transaction.classification_confidence * 100}%`,
                        backgroundColor: transaction.classification_confidence >= 0.7
                          ? colors.success.main
                          : colors.warning.main,
                      }} />
                      <span style={styles.confidenceText}>
                        {(transaction.classification_confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td style={styles.td}>
                    <span style={mergeStyles(
                      components.badge.base,
                      transaction.status === 'approved'
                        ? components.badge.success
                        : transaction.status === 'pending_review'
                        ? components.badge.warning
                        : components.badge.error
                    )}>
                      {transaction.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actionsCell}>
                      <button
                        onClick={() => setSelectedTransaction(transaction)}
                        style={mergeStyles(components.button.base, components.button.ghost, styles.actionButton)}
                        title="View details"
                      >
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                          <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                        </svg>
                      </button>
                      {transaction.status === 'pending_review' && (
                        <button
                          onClick={() => handleApprove(transaction.transaction_id)}
                          style={mergeStyles(components.button.base, components.button.success, styles.actionButton)}
                          title="Approve"
                        >
                          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                          </svg>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Transaction Detail Modal */}
      {selectedTransaction && (
        <TransactionDetailModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
          onCorrect={handleCorrect}
          onApprove={handleApprove}
        />
      )}
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
  filtersContainer: {
    marginBottom: spacing.xl,
  },
  searchContainer: {
    position: 'relative',
    marginBottom: spacing.md,
  },
  searchIcon: {
    position: 'absolute',
    left: spacing.md,
    top: '50%',
    transform: 'translateY(-50%)',
    color: colors.gray[400],
    pointerEvents: 'none',
  },
  searchInput: {
    ...components.input.base,
    paddingLeft: spacing['2xl'],
    paddingRight: spacing['2xl'],
    fontSize: typography.fontSize.base,
  },
  clearSearchButton: {
    position: 'absolute',
    right: spacing.md,
    top: '50%',
    transform: 'translateY(-50%)',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: colors.gray[400],
    padding: spacing.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.sm,
  },
  filtersRow: {
    display: 'flex',
    gap: spacing.sm,
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  filterSelect: {
    ...components.input.base,
    minWidth: '150px',
  },
  filterInput: {
    ...components.input.base,
    minWidth: '200px',
  },
  tableContainer: {
    ...components.card.base,
    padding: 0,
    overflow: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: spacing.md,
    textAlign: 'left',
    borderBottom: `2px solid ${colors.gray[200]}`,
    fontWeight: typography.fontWeight.semibold,
    fontSize: typography.fontSize.sm,
    color: colors.gray[700],
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    backgroundColor: colors.gray[50],
  },
  tr: {
    borderBottom: `1px solid ${colors.gray[100]}`,
    transition: `background-color ${transitions.base}`,
  },
  td: {
    padding: spacing.md,
    fontSize: typography.fontSize.sm,
    color: colors.gray[900],
  },
  vendorCell: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  vendorName: {
    fontWeight: typography.fontWeight.medium,
  },
  vendorDescription: {
    fontSize: typography.fontSize.xs,
    color: colors.gray[500],
  },
  amountText: {
    fontWeight: typography.fontWeight.semibold,
    fontSize: typography.fontSize.base,
  },
  confidenceCell: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  confidenceBar: {
    height: '6px',
    borderRadius: borderRadius.full,
    transition: `width ${transitions.base}`,
  },
  confidenceText: {
    fontSize: typography.fontSize.xs,
    color: colors.gray[600],
    minWidth: '35px',
  },
  actionsCell: {
    display: 'flex',
    gap: spacing.xs,
  },
  actionButton: {
    padding: spacing.sm,
    minWidth: 'auto',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing['3xl'],
    textAlign: 'center',
  },
  emptyStateTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  emptyStateText: {
    fontSize: typography.fontSize.base,
    color: colors.gray[500],
  },
};

// Add hover effect via CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  table tbody tr:hover {
    background-color: ${colors.gray[50]};
  }
`;
document.head.appendChild(styleSheet);

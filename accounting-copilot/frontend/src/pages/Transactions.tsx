import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { Transaction } from '../types';
import { TransactionDetailModal } from '../components/TransactionDetailModal';

export const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<'all' | 'income' | 'expense'>('all');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [vendorFilter, setVendorFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'pending_review'>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const loadTransactions = async () => {
    try {
      setIsLoading(true);
      setError('');
      const params: any = {};
      if (typeFilter !== 'all') params.type = typeFilter;
      // category is filtered client-side (backend requires exact GSI match)
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
  }, [typeFilter, statusFilter]);

  const sortedTransactions = [...transactions]
    .filter((t) =>
      !categoryFilter ||
      t.category.toLowerCase().includes(categoryFilter.toLowerCase())
    )
    .filter((t) =>
      !vendorFilter ||
      t.vendor.toLowerCase().includes(vendorFilter.toLowerCase())
    )
    .filter((t) => !startDate || t.date >= startDate)
    .filter((t) => !endDate || t.date <= endDate)
    .sort((a, b) => {
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

  if (isLoading) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>Transactions</h1>
        <div style={styles.loadingWrap}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
          <span style={{ color: 'var(--color-text-muted)' }}>Loading transactions...</span>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Transactions</h1>
          <p style={styles.subtitle}>{sortedTransactions.length} transaction{sortedTransactions.length !== 1 ? 's' : ''} found</p>
        </div>
      </div>

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGroup}>
          <label htmlFor="type-filter" style={styles.filterLabel}>Type</label>
          <select
            id="type-filter"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as any)}
            style={styles.select}
          >
            <option value="all">All Types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="status-filter" style={styles.filterLabel}>Status</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            style={styles.select}
          >
            <option value="all">All Status</option>
            <option value="approved">Approved</option>
            <option value="pending_review">Pending Review</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="category-filter" style={styles.filterLabel}>Category</label>
          <input
            id="category-filter"
            type="text"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            placeholder="Search category..."
            style={styles.input}
          />
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="vendor-filter" style={styles.filterLabel}>Vendor</label>
          <input
            id="vendor-filter"
            type="text"
            value={vendorFilter}
            onChange={(e) => setVendorFilter(e.target.value)}
            placeholder="Search vendor..."
            style={styles.input}
          />
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="start-date-filter" style={styles.filterLabel}>From</label>
          <input
            id="start-date-filter"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{ ...styles.input, width: '138px' }}
          />
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="end-date-filter" style={styles.filterLabel}>To</label>
          <input
            id="end-date-filter"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{ ...styles.input, width: '138px' }}
          />
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="sort-by-filter" style={styles.filterLabel}>Sort by</label>
          <select
            id="sort-by-filter"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            style={styles.select}
          >
            <option value="date">Date</option>
            <option value="amount">Amount</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="order-filter" style={styles.filterLabel}>Order</label>
          <select
            id="order-filter"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            style={styles.select}
          >
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>
        </div>
      </div>

      {error && (
        <div style={styles.error}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>
          {error}
        </div>
      )}

      {/* Transactions Table */}
      <div style={styles.tableContainer}>
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
                  <span style={styles.dateText}>{new Date(transaction.date).toLocaleDateString()}</span>
                </td>
                <td style={styles.td}>
                  <span style={styles.vendorText}>{transaction.vendor}</span>
                </td>
                <td style={styles.td}>
                  <span style={styles.categoryBadge}>{transaction.category}</span>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      color: transaction.type === 'income' ? 'var(--color-success)' : 'var(--color-danger)',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                    }}
                  >
                    {transaction.type === 'income' ? '+' : '-'}$
                    {transaction.amount.toFixed(2)}
                  </span>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.typeBadge,
                      backgroundColor: transaction.type === 'income' ? 'var(--color-success-light)' : 'var(--color-danger-light)',
                      color: transaction.type === 'income' ? 'var(--color-success-dark)' : 'var(--color-danger-dark)',
                    }}
                  >
                    {transaction.type}
                  </span>
                </td>
                <td style={styles.td}>
                  <div style={styles.confidenceWrap}>
                    <div style={styles.confidenceBar}>
                      <div
                        style={{
                          ...styles.confidenceFill,
                          width: `${transaction.classification_confidence * 100}%`,
                          backgroundColor: transaction.classification_confidence >= 0.7 ? 'var(--color-success)' : 'var(--color-warning)',
                        }}
                      />
                    </div>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: transaction.classification_confidence >= 0.7 ? 'var(--color-success)' : 'var(--color-warning)',
                    }}>
                      {(transaction.classification_confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.statusBadge,
                      backgroundColor:
                        transaction.status === 'approved'
                          ? 'var(--color-success-light)'
                          : transaction.status === 'pending_review'
                            ? 'var(--color-warning-light)'
                            : 'var(--color-danger-light)',
                      color:
                        transaction.status === 'approved'
                          ? 'var(--color-success-dark)'
                          : transaction.status === 'pending_review'
                            ? 'var(--color-warning-dark)'
                            : 'var(--color-danger-dark)',
                    }}
                  >
                    {transaction.status === 'pending_review' && '⏳ '}
                    {transaction.status === 'approved' && '✓ '}
                    {transaction.status.replace('_', ' ')}
                  </span>
                </td>
                <td style={styles.td}>
                  <div style={styles.actionBtns}>
                    <button
                      onClick={() => setSelectedTransaction(transaction)}
                      style={styles.viewButton}
                    >
                      View
                    </button>
                    {transaction.status === 'pending_review' && (
                      <button
                        onClick={() => handleApprove(transaction.transaction_id)}
                        style={styles.approveButton}
                      >
                        Approve
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {sortedTransactions.length === 0 && (
          <div style={styles.emptyState}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="1.5">
              <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <p style={styles.emptyTitle}>No transactions found</p>
            <p style={styles.emptyText}>Try adjusting your filters</p>
          </div>
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

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: 'var(--space-page)',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '24px',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    letterSpacing: '-0.5px',
  },
  subtitle: {
    fontSize: '0.85rem',
    color: 'var(--color-text-muted)',
    marginTop: '4px',
  },
  loadingWrap: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: '4rem',
  },
  error: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: 'var(--color-danger-light)',
    color: 'var(--color-danger)',
    padding: '12px 16px',
    borderRadius: 'var(--radius-lg)',
    marginBottom: '16px',
    fontSize: '0.85rem',
    fontWeight: 500,
  },
  filters: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
    flexWrap: 'nowrap',
    padding: '12px 16px',
    backgroundColor: 'var(--color-card)',
    borderRadius: 12,
    boxShadow: 'var(--shadow-card)',
    border: '1px solid rgba(0,0,0,0.04)',
    alignItems: 'flex-end',
    overflowX: 'auto',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    flexShrink: 0,
  },
  filterLabel: {
    fontSize: '0.7rem',
    fontWeight: 600,
    color: 'var(--color-text-muted)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  select: {
    padding: '7px 8px',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.8rem',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text)',
    outline: 'none',
    fontFamily: 'inherit',
    cursor: 'pointer',
    width: '120px',
  },
  input: {
    padding: '7px 8px',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.8rem',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text)',
    outline: 'none',
    fontFamily: 'inherit',
    width: '130px',
  },
  tableContainer: {
    backgroundColor: 'var(--color-card)',
    borderRadius: 14,
    boxShadow: 'var(--shadow-card)',
    border: '1px solid rgba(0,0,0,0.04)',
    overflow: 'auto',
    animation: 'fadeIn 0.3s ease-out',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '13px 16px',
    textAlign: 'left',
    borderBottom: '1px solid var(--color-border)',
    fontWeight: 700,
    fontSize: '0.7rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.8px',
    color: 'var(--color-text-muted)',
    backgroundColor: '#fafafa',
  },
  tr: {
    borderBottom: '1px solid var(--color-border-light)',
    transition: 'background-color var(--transition-fast)',
    cursor: 'default',
  },
  td: {
    padding: '13px 16px',
    fontSize: '0.875rem',
  },
  dateText: {
    color: 'var(--color-text-secondary)',
    fontSize: '0.85rem',
  },
  vendorText: {
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  categoryBadge: {
    padding: '3px 10px',
    backgroundColor: 'var(--color-primary-50)',
    color: 'var(--color-primary)',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.75rem',
    fontWeight: 600,
  },
  typeBadge: {
    padding: '4px 10px',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.7rem',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  confidenceWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  confidenceBar: {
    width: '48px',
    height: '6px',
    backgroundColor: 'var(--color-border-light)',
    borderRadius: 'var(--radius-full)',
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 'var(--radius-full)',
    transition: 'width 0.3s ease',
  },
  statusBadge: {
    padding: '4px 10px',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.7rem',
    fontWeight: 600,
    textTransform: 'capitalize' as const,
    whiteSpace: 'nowrap' as const,
  },
  actionBtns: {
    display: 'flex',
    gap: '6px',
  },
  viewButton: {
    padding: '6px 14px',
    backgroundColor: 'var(--color-primary)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  approveButton: {
    padding: '6px 14px',
    backgroundColor: 'var(--color-success)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  emptyState: {
    textAlign: 'center',
    padding: '4rem 2rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
  },
  emptyTitle: {
    fontSize: '1.1rem',
    fontWeight: 700,
    color: 'var(--color-text)',
  },
  emptyText: {
    color: 'var(--color-text-muted)',
    fontSize: '0.85rem',
  },
};

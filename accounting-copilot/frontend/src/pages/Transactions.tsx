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

  const sortedTransactions = [...transactions].sort((a, b) => {
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
        <div style={styles.loading}>Loading transactions...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Transactions</h1>

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGroup}>
          <label htmlFor="type-filter" style={styles.filterLabel}>Type:</label>
          <select
            id="type-filter"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as any)}
            style={styles.select}
          >
            <option value="all">All</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="status-filter" style={styles.filterLabel}>Status:</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            style={styles.select}
          >
            <option value="all">All</option>
            <option value="approved">Approved</option>
            <option value="pending_review">Pending Review</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="category-filter" style={styles.filterLabel}>Category:</label>
          <input
            id="category-filter"
            type="text"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            placeholder="Filter by category"
            style={styles.input}
          />
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="sort-by-filter" style={styles.filterLabel}>Sort by:</label>
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
          <label htmlFor="order-filter" style={styles.filterLabel}>Order:</label>
          <select
            id="order-filter"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            style={styles.select}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

      {error && <div style={styles.error}>{error}</div>}

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
                <td style={styles.td}>{new Date(transaction.date).toLocaleDateString()}</td>
                <td style={styles.td}>{transaction.vendor}</td>
                <td style={styles.td}>{transaction.category}</td>
                <td style={styles.td}>
                  <span
                    style={{
                      color: transaction.type === 'income' ? '#28a745' : '#dc3545',
                      fontWeight: '500',
                    }}
                  >
                    {transaction.type === 'income' ? '+' : '-'}$
                    {transaction.amount.toFixed(2)}
                  </span>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.badge,
                      backgroundColor: transaction.type === 'income' ? '#d4edda' : '#f8d7da',
                      color: transaction.type === 'income' ? '#155724' : '#721c24',
                    }}
                  >
                    {transaction.type}
                  </span>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      color:
                        transaction.classification_confidence >= 0.7
                          ? '#28a745'
                          : '#ffc107',
                    }}
                  >
                    {(transaction.classification_confidence * 100).toFixed(0)}%
                  </span>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.badge,
                      backgroundColor:
                        transaction.status === 'approved'
                          ? '#d4edda'
                          : transaction.status === 'pending_review'
                          ? '#fff3cd'
                          : '#f8d7da',
                      color:
                        transaction.status === 'approved'
                          ? '#155724'
                          : transaction.status === 'pending_review'
                          ? '#856404'
                          : '#721c24',
                    }}
                  >
                    {transaction.status.replace('_', ' ')}
                  </span>
                </td>
                <td style={styles.td}>
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
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {sortedTransactions.length === 0 && (
          <div style={styles.emptyState}>No transactions found</div>
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
    padding: '2rem',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  title: {
    fontSize: '1.875rem',
    fontWeight: 'bold',
    marginBottom: '1.5rem',
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
  filters: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '1.5rem',
    flexWrap: 'wrap',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  filterLabel: {
    fontSize: '0.875rem',
    fontWeight: '500',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.875rem',
  },
  input: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.875rem',
  },
  tableContainer: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    overflow: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '1rem',
    textAlign: 'left',
    borderBottom: '2px solid #ddd',
    fontWeight: '600',
    fontSize: '0.875rem',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  tr: {
    borderBottom: '1px solid #f0f0f0',
  },
  td: {
    padding: '1rem',
    fontSize: '0.875rem',
  },
  badge: {
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  viewButton: {
    padding: '0.375rem 0.75rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    cursor: 'pointer',
    marginRight: '0.5rem',
  },
  approveButton: {
    padding: '0.375rem 0.75rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    cursor: 'pointer',
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem',
    color: '#999',
  },
};

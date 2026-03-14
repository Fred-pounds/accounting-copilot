import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { AuditEntry } from '../types';

export const AuditTrail: React.FC = () => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [actionTypeFilter, setActionTypeFilter] = useState('');
  const [transactionIdFilter, setTransactionIdFilter] = useState('');

  const loadAuditTrail = async () => {
    try {
      setIsLoading(true);
      setError('');
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (actionTypeFilter) params.action_type = actionTypeFilter;
      if (transactionIdFilter) params.transaction_id = transactionIdFilter;

      const data = await apiClient.getAuditTrail(params);
      setEntries(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit trail');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAuditTrail();
  }, []);

  const handleExport = async () => {
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const blob = await apiClient.exportAuditTrail(params);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(err.message || 'Failed to export audit trail');
    }
  };

  if (isLoading) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>Audit Trail</h1>
        <div style={styles.loadingWrap}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
          <span style={{ color: 'var(--color-text-muted)' }}>Loading audit trail...</span>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Audit Trail</h1>
          <p style={styles.headerSub}>Track all AI actions and user activities</p>
        </div>
        <button onClick={handleExport} style={styles.exportButton}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Action Type</label>
          <select
            value={actionTypeFilter}
            onChange={(e) => setActionTypeFilter(e.target.value)}
            style={styles.select}
          >
            <option value="">All Actions</option>
            <option value="classification">Classification</option>
            <option value="reconciliation">Reconciliation</option>
            <option value="assistant_query">Assistant Query</option>
            <option value="approval">Approval</option>
            <option value="correction">Correction</option>
            <option value="data_access">Data Access</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Transaction ID</label>
          <input
            type="text"
            value={transactionIdFilter}
            onChange={(e) => setTransactionIdFilter(e.target.value)}
            placeholder="Filter by ID..."
            style={styles.input}
          />
        </div>

        <button onClick={loadAuditTrail} style={styles.applyButton}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
            <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
          </svg>
          Apply
        </button>
      </div>

      {error && (
        <div style={styles.error}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>
          {error}
        </div>
      )}

      {/* Audit Entries Table */}
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Timestamp</th>
              <th style={styles.th}>Action Type</th>
              <th style={styles.th}>Actor</th>
              <th style={styles.th}>Subject</th>
              <th style={styles.th}>Result</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.action_id} style={styles.tr}>
                <td style={styles.td}>
                  <span style={styles.timestamp}>
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                </td>
                <td style={styles.td}>
                  <span style={styles.actionType}>
                    {entry.action_type.replace(/_/g, ' ')}
                  </span>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.actorBadge,
                      backgroundColor: entry.actor === 'ai' ? 'var(--color-info-light)' : 'var(--color-success-light)',
                      color: entry.actor === 'ai' ? '#0369a1' : 'var(--color-success-dark)',
                    }}
                  >
                    {entry.actor === 'ai' ? '🤖' : '👤'} {entry.actor}
                  </span>
                  {entry.actor_details && (
                    <div style={styles.actorDetails}>{entry.actor_details}</div>
                  )}
                </td>
                <td style={styles.td}>
                  <div style={styles.subjectType}>{entry.subject_type}</div>
                  <div style={styles.subjectId}>{entry.subject_id}</div>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.resultBadge,
                      backgroundColor: entry.result === 'success' ? 'var(--color-success-light)' : 'var(--color-danger-light)',
                      color: entry.result === 'success' ? 'var(--color-success-dark)' : 'var(--color-danger-dark)',
                    }}
                  >
                    {entry.result === 'success' ? '✓' : '✕'} {entry.result}
                  </span>
                </td>
                <td style={styles.td}>
                  <button
                    onClick={() => setSelectedEntry(entry)}
                    style={styles.viewButton}
                  >
                    Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {entries.length === 0 && (
          <div style={styles.emptyState}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <p style={styles.emptyTitle}>No audit entries found</p>
            <p style={styles.emptyText}>Try adjusting your filter criteria</p>
          </div>
        )}
      </div>

      {/* Entry Detail Modal */}
      {selectedEntry && (
        <div style={styles.overlay} onClick={() => setSelectedEntry(null)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Audit Entry Details</h2>
              <button onClick={() => setSelectedEntry(null)} style={styles.closeButton}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              </button>
            </div>

            <div style={styles.modalContent}>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Action ID</span>
                <span style={styles.modalValueMono}>{selectedEntry.action_id}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Timestamp</span>
                <span style={styles.modalValue}>{new Date(selectedEntry.timestamp).toLocaleString()}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Action Type</span>
                <span style={{ ...styles.modalValue, textTransform: 'capitalize' }}>{selectedEntry.action_type.replace(/_/g, ' ')}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Actor</span>
                <span style={styles.modalValue}>
                  {selectedEntry.actor}{selectedEntry.actor_details && ` (${selectedEntry.actor_details})`}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject Type</span>
                <span style={styles.modalValue}>{selectedEntry.subject_type}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject ID</span>
                <span style={styles.modalValueMono}>{selectedEntry.subject_id}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Result</span>
                <span style={styles.modalValue}>{selectedEntry.result}</span>
              </div>

              {Object.keys(selectedEntry.action_details).length > 0 && (
                <div style={styles.detailsSection}>
                  <span style={styles.modalLabel}>Action Details</span>
                  <pre style={styles.detailsJson}>
                    {JSON.stringify(selectedEntry.action_details, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div style={styles.modalFooter}>
              <button onClick={() => setSelectedEntry(null)} style={styles.closeModalButton}>
                Close
              </button>
            </div>
          </div>
        </div>
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
    marginBottom: '20px',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    letterSpacing: '-0.5px',
  },
  headerSub: {
    fontSize: '0.85rem',
    color: 'var(--color-text-muted)',
    marginTop: '4px',
  },
  exportButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 18px',
    backgroundColor: 'var(--color-success)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
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
    gap: '12px',
    marginBottom: '20px',
    flexWrap: 'wrap',
    alignItems: 'flex-end',
    padding: '16px 20px',
    backgroundColor: 'var(--color-card)',
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow-xs)',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  filterLabel: {
    fontSize: '0.7rem',
    fontWeight: 600,
    color: 'var(--color-text-muted)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  select: {
    padding: '8px 12px',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text)',
    outline: 'none',
    fontFamily: 'inherit',
    cursor: 'pointer',
  },
  input: {
    padding: '8px 12px',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text)',
    outline: 'none',
    fontFamily: 'inherit',
  },
  applyButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 16px',
    backgroundColor: 'var(--color-primary)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  tableContainer: {
    backgroundColor: 'var(--color-card)',
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow-sm)',
    overflow: 'auto',
    animation: 'fadeIn 0.3s ease-out',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '14px 16px',
    textAlign: 'left',
    borderBottom: '2px solid var(--color-border)',
    fontWeight: 600,
    fontSize: '0.75rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.7px',
    color: 'var(--color-text-muted)',
  },
  tr: {
    borderBottom: '1px solid var(--color-border-light)',
    transition: 'background-color var(--transition-fast)',
  },
  td: {
    padding: '14px 16px',
    fontSize: '0.875rem',
  },
  timestamp: {
    fontSize: '0.8rem',
    color: 'var(--color-text-secondary)',
  },
  actionType: {
    textTransform: 'capitalize' as const,
    fontWeight: 600,
    color: 'var(--color-text)',
    fontSize: '0.85rem',
  },
  actorBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '3px 10px',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.75rem',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
  },
  actorDetails: {
    fontSize: '0.7rem',
    color: 'var(--color-text-muted)',
    marginTop: '4px',
  },
  subjectType: {
    fontWeight: 600,
    fontSize: '0.85rem',
    color: 'var(--color-text)',
  },
  subjectId: {
    fontSize: '0.7rem',
    color: 'var(--color-text-muted)',
    fontFamily: 'monospace',
    marginTop: '2px',
  },
  resultBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '3px 10px',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.75rem',
    fontWeight: 600,
    textTransform: 'capitalize' as const,
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
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    backdropFilter: 'blur(4px)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'var(--color-card)',
    borderRadius: 'var(--radius-xl)',
    width: '90%',
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: 'var(--shadow-xl)',
    animation: 'scaleIn 0.2s ease-out',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid var(--color-border)',
  },
  modalTitle: {
    fontSize: '1.2rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    margin: 0,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    color: 'var(--color-text-muted)',
    cursor: 'pointer',
    padding: '4px',
    display: 'flex',
    borderRadius: 'var(--radius-md)',
  },
  modalContent: {
    padding: '24px',
  },
  modalField: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    marginBottom: '16px',
  },
  modalLabel: {
    fontWeight: 600,
    color: 'var(--color-text-muted)',
    fontSize: '0.75rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  modalValue: {
    fontSize: '0.95rem',
    color: 'var(--color-text)',
    fontWeight: 500,
  },
  modalValueMono: {
    fontSize: '0.85rem',
    color: 'var(--color-text-secondary)',
    fontFamily: 'monospace',
  },
  detailsSection: {
    marginTop: '8px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  detailsJson: {
    backgroundColor: 'var(--color-surface)',
    padding: '14px',
    borderRadius: 'var(--radius-md)',
    overflow: 'auto',
    fontSize: '0.8rem',
    fontFamily: 'monospace',
    color: 'var(--color-text-secondary)',
    border: '1px solid var(--color-border)',
    margin: 0,
  },
  modalFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: '16px 24px',
    borderTop: '1px solid var(--color-border)',
  },
  closeModalButton: {
    padding: '10px 20px',
    backgroundColor: 'var(--color-text-secondary)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
};

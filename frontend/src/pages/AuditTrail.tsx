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
        <div style={styles.loading}>Loading audit trail...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Audit Trail</h1>
        <button onClick={handleExport} style={styles.exportButton}>
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Start Date:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>End Date:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={styles.input}
          />
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Action Type:</label>
          <select
            value={actionTypeFilter}
            onChange={(e) => setActionTypeFilter(e.target.value)}
            style={styles.select}
          >
            <option value="">All</option>
            <option value="classification">Classification</option>
            <option value="reconciliation">Reconciliation</option>
            <option value="assistant_query">Assistant Query</option>
            <option value="approval">Approval</option>
            <option value="correction">Correction</option>
            <option value="data_access">Data Access</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Transaction ID:</label>
          <input
            type="text"
            value={transactionIdFilter}
            onChange={(e) => setTransactionIdFilter(e.target.value)}
            placeholder="Filter by transaction"
            style={styles.input}
          />
        </div>

        <button onClick={loadAuditTrail} style={styles.applyButton}>
          Apply Filters
        </button>
      </div>

      {error && <div style={styles.error}>{error}</div>}

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
                  {new Date(entry.timestamp).toLocaleString()}
                </td>
                <td style={styles.td}>
                  <span style={styles.actionType}>
                    {entry.action_type.replace('_', ' ')}
                  </span>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.badge,
                      backgroundColor: entry.actor === 'ai' ? '#d1ecf1' : '#d4edda',
                      color: entry.actor === 'ai' ? '#0c5460' : '#155724',
                    }}
                  >
                    {entry.actor}
                  </span>
                  {entry.actor_details && (
                    <div style={styles.actorDetails}>{entry.actor_details}</div>
                  )}
                </td>
                <td style={styles.td}>
                  <div>{entry.subject_type}</div>
                  <div style={styles.subjectId}>{entry.subject_id}</div>
                </td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.badge,
                      backgroundColor:
                        entry.result === 'success' ? '#d4edda' : '#f8d7da',
                      color: entry.result === 'success' ? '#155724' : '#721c24',
                    }}
                  >
                    {entry.result}
                  </span>
                </td>
                <td style={styles.td}>
                  <button
                    onClick={() => setSelectedEntry(entry)}
                    style={styles.viewButton}
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {entries.length === 0 && (
          <div style={styles.emptyState}>No audit entries found</div>
        )}
      </div>

      {/* Entry Detail Modal */}
      {selectedEntry && (
        <div style={styles.overlay} onClick={() => setSelectedEntry(null)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Audit Entry Details</h2>
              <button
                onClick={() => setSelectedEntry(null)}
                style={styles.closeButton}
              >
                ×
              </button>
            </div>

            <div style={styles.modalContent}>
              <div style={styles.detailField}>
                <span style={styles.detailLabel}>Action ID:</span>
                <span style={styles.detailValue}>{selectedEntry.action_id}</span>
              </div>
              <div style={styles.detailField}>
                <span style={styles.detailLabel}>Timestamp:</span>
                <span style={styles.detailValue}>
                  {new Date(selectedEntry.timestamp).toLocaleString()}
                </span>
              </div>
              <div style={styles.detailField}>
                <span style={styles.detailLabel}>Action Type:</span>
                <span style={styles.detailValue}>
                  {selectedEntry.action_type.replace('_', ' ')}
                </span>
              </div>
              <div style={styles.detailField}>
                <span style={styles.detailLabel}>Actor:</span>
                <span style={styles.detailValue}>
                  {selectedEntry.actor}
                  {selectedEntry.actor_details && ` (${selectedEntry.actor_details})`}
                </span>
              </div>
              <div style={styles.detailField}>
                <span style={styles.detailLabel}>Subject Type:</span>
                <span style={styles.detailValue}>{selectedEntry.subject_type}</span>
              </div>
              <div style={styles.detailField}>
                <span style={styles.detailLabel}>Subject ID:</span>
                <span style={styles.detailValue}>{selectedEntry.subject_id}</span>
              </div>
              <div style={styles.detailField}>
                <span style={styles.detailLabel}>Result:</span>
                <span style={styles.detailValue}>{selectedEntry.result}</span>
              </div>

              {Object.keys(selectedEntry.action_details).length > 0 && (
                <div style={styles.detailsSection}>
                  <div style={styles.detailLabel}>Action Details:</div>
                  <pre style={styles.detailsJson}>
                    {JSON.stringify(selectedEntry.action_details, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div style={styles.modalFooter}>
              <button
                onClick={() => setSelectedEntry(null)}
                style={styles.closeModalButton}
              >
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
    padding: '2rem',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },
  title: {
    fontSize: '1.875rem',
    fontWeight: 'bold',
  },
  exportButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
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
    alignItems: 'flex-end',
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
  applyButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    cursor: 'pointer',
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
  actionType: {
    textTransform: 'capitalize',
    fontWeight: '500',
  },
  badge: {
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: '500',
    textTransform: 'uppercase',
  },
  actorDetails: {
    fontSize: '0.75rem',
    color: '#999',
    marginTop: '0.25rem',
  },
  subjectId: {
    fontSize: '0.75rem',
    color: '#999',
    fontFamily: 'monospace',
  },
  viewButton: {
    padding: '0.375rem 0.75rem',
    backgroundColor: '#007bff',
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
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '8px',
    width: '90%',
    maxWidth: '700px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem',
    borderBottom: '1px solid #ddd',
  },
  modalTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    margin: 0,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '2rem',
    cursor: 'pointer',
    color: '#999',
    lineHeight: 1,
  },
  modalContent: {
    padding: '1.5rem',
  },
  detailField: {
    display: 'flex',
    marginBottom: '1rem',
    gap: '0.5rem',
  },
  detailLabel: {
    fontWeight: '600',
    minWidth: '140px',
    color: '#666',
  },
  detailValue: {
    flex: 1,
  },
  detailsSection: {
    marginTop: '1.5rem',
  },
  detailsJson: {
    backgroundColor: '#f5f5f5',
    padding: '1rem',
    borderRadius: '4px',
    overflow: 'auto',
    fontSize: '0.875rem',
    fontFamily: 'monospace',
  },
  modalFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: '1.5rem',
    borderTop: '1px solid #ddd',
  },
  closeModalButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
};

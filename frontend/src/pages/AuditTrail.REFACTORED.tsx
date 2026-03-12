/**
 * REFACTORED AUDIT TRAIL - Modern UI/UX
 * 
 * Copy this entire file content and replace the content of AuditTrail.tsx
 * 
 * Improvements:
 * - Modern table design with better visual hierarchy
 * - Enhanced filter UI with chips
 * - Better status badges and actor indicators
 * - Improved modal design
 * - Export button with icon
 * - Better empty state
 * - Smooth animations
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { AuditEntry } from '../types';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

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

  const clearFilters = () => {
    setStartDate('');
    setEndDate('');
    setActionTypeFilter('');
    setTransactionIdFilter('');
  };

  const hasActiveFilters = startDate || endDate || actionTypeFilter || transactionIdFilter;

  const getActorIcon = (actor: string) => {
    if (actor === 'ai') {
      return (
        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
          <path d="M13 7H7v6h6V7z"/>
          <path fillRule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clipRule="evenodd"/>
        </svg>
      );
    }
    return (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
      </svg>
    );
  };

  // Loading State
  if (isLoading && entries.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingContainer}>
          <div style={styles.spinner}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
              <circle cx="12" cy="12" r="10" stroke={colors.gray[300]} strokeWidth="4"/>
              <path fill={colors.primary.main} d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
          </div>
          <p style={styles.loadingText}>Loading audit trail...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container} className="animate-fade-in">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Audit Trail</h1>
          <p style={styles.subtitle}>
            {entries.length} audit entr{entries.length !== 1 ? 'ies' : 'y'} found
          </p>
        </div>
        <div style={styles.headerActions}>
          <button
            onClick={loadAuditTrail}
            style={mergeStyles(components.button.base, components.button.outline)}
            disabled={isLoading}
          >
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"/>
            </svg>
            Refresh
          </button>
          <button
            onClick={handleExport}
            style={mergeStyles(components.button.base, components.button.success)}
          >
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd"/>
            </svg>
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={styles.filtersContainer}>
        <div style={styles.filtersRow}>
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={styles.filterInput}
            />
          </div>

          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={styles.filterInput}
            />
          </div>

          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>Action Type</label>
            <select
              value={actionTypeFilter}
              onChange={(e) => setActionTypeFilter(e.target.value)}
              style={styles.filterSelect}
            >
              <option value="">All Types</option>
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
              placeholder="Filter by transaction"
              style={styles.filterInput}
            />
          </div>

          <button
            onClick={loadAuditTrail}
            style={mergeStyles(components.button.base, components.button.primary, styles.applyButton)}
          >
            Apply Filters
          </button>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              style={mergeStyles(components.button.base, components.button.ghost)}
            >
              <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
              Clear
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

      {/* Audit Entries Table */}
      <div style={styles.tableContainer}>
        {entries.length === 0 ? (
          <div style={styles.emptyState}>
            <svg width="64" height="64" viewBox="0 0 20 20" fill={colors.gray[300]}>
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/>
            </svg>
            <h3 style={styles.emptyStateTitle}>No audit entries found</h3>
            <p style={styles.emptyStateText}>
              {hasActiveFilters
                ? 'Try adjusting your filters'
                : 'Audit entries will appear here as actions are performed'}
            </p>
          </div>
        ) : (
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
                    <div style={styles.timestampCell}>
                      <div style={styles.timestampDate}>
                        {new Date(entry.timestamp).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </div>
                      <div style={styles.timestampTime}>
                        {new Date(entry.timestamp).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  </td>
                  <td style={styles.td}>
                    <span style={mergeStyles(components.badge.base, components.badge.neutral)}>
                      {entry.action_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actorCell}>
                      <span style={mergeStyles(
                        components.badge.base,
                        entry.actor === 'ai' ? components.badge.info : components.badge.success
                      )}>
                        {getActorIcon(entry.actor)}
                        {entry.actor}
                      </span>
                      {entry.actor_details && (
                        <div style={styles.actorDetails}>{entry.actor_details}</div>
                      )}
                    </div>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.subjectCell}>
                      <div style={styles.subjectType}>{entry.subject_type}</div>
                      <div style={styles.subjectId}>{entry.subject_id}</div>
                    </div>
                  </td>
                  <td style={styles.td}>
                    <span style={mergeStyles(
                      components.badge.base,
                      entry.result === 'success' ? components.badge.success : components.badge.error
                    )}>
                      {entry.result === 'success' ? (
                        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                        </svg>
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                        </svg>
                      )}
                      {entry.result}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <button
                      onClick={() => setSelectedEntry(entry)}
                      style={mergeStyles(components.button.base, components.button.ghost, styles.viewButton)}
                    >
                      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                        <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                      </svg>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Entry Detail Modal */}
      {selectedEntry && (
        <div style={styles.overlay} onClick={() => setSelectedEntry(null)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()} className="animate-slide-in">
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Audit Entry Details</h2>
              <button onClick={() => setSelectedEntry(null)} style={styles.closeButton}>
                <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
                </svg>
              </button>
            </div>

            <div style={styles.modalContent}>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Action ID</span>
                <span style={styles.modalValue}>{selectedEntry.action_id}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Timestamp</span>
                <span style={styles.modalValue}>
                  {new Date(selectedEntry.timestamp).toLocaleString()}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Action Type</span>
                <span style={styles.modalValue}>
                  {selectedEntry.action_type.replace('_', ' ')}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Actor</span>
                <span style={styles.modalValue}>
                  {selectedEntry.actor}
                  {selectedEntry.actor_details && ` (${selectedEntry.actor_details})`}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject Type</span>
                <span style={styles.modalValue}>{selectedEntry.subject_type}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject ID</span>
                <span style={styles.modalValue}>{selectedEntry.subject_id}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Result</span>
                <span style={styles.modalValue}>{selectedEntry.result}</span>
              </div>

              {Object.keys(selectedEntry.action_details).length > 0 && (
                <div style={styles.detailsSection}>
                  <div style={styles.modalLabel}>Action Details</div>
                  <pre style={styles.detailsJson}>
                    {JSON.stringify(selectedEntry.action_details, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div style={styles.modalFooter}>
              <button
                onClick={() => setSelectedEntry(null)}
                style={mergeStyles(components.button.base, components.button.outline)}
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
    gap: spacing.sm,
  },
  filtersContainer: {
    ...components.card.base,
    marginBottom: spacing.xl,
  },
  filtersRow: {
    display: 'flex',
    gap: spacing.md,
    flexWrap: 'wrap',
    alignItems: 'flex-end',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
    minWidth: '150px',
  },
  filterLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[700],
  },
  filterInput: {
    ...components.input.base,
    fontSize: typography.fontSize.sm,
  },
  filterSelect: {
    ...components.input.base,
    fontSize: typography.fontSize.sm,
  },
  applyButton: {
    alignSelf: 'flex-end',
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
  timestampCell: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  timestampDate: {
    fontWeight: typography.fontWeight.medium,
  },
  timestampTime: {
    fontSize: typography.fontSize.xs,
    color: colors.gray[500],
  },
  actorCell: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  actorDetails: {
    fontSize: typography.fontSize.xs,
    color: colors.gray[500],
  },
  subjectCell: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  subjectType: {
    fontWeight: typography.fontWeight.medium,
  },
  subjectId: {
    fontSize: typography.fontSize.xs,
    color: colors.gray[500],
    fontFamily: typography.fontFamily.mono,
  },
  viewButton: {
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
    padding: spacing.lg,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: borderRadius.xl,
    width: '100%',
    maxWidth: '700px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: shadows.xl,
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.xl,
    borderBottom: `1px solid ${colors.gray[200]}`,
  },
  modalTitle: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: typography.fontWeight.bold,
    color: colors.gray[900],
  },
  closeButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: colors.gray[400],
    padding: spacing.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.md,
    transition: `all ${transitions.base}`,
  },
  modalContent: {
    padding: spacing.xl,
  },
  modalField: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
    marginBottom: spacing.lg,
  },
  modalLabel: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[700],
  },
  modalValue: {
    fontSize: typography.fontSize.base,
    color: colors.gray[900],
  },
  detailsSection: {
    marginTop: spacing.xl,
  },
  detailsJson: {
    backgroundColor: colors.gray[50],
    padding: spacing.lg,
    borderRadius: borderRadius.md,
    overflow: 'auto',
    fontSize: typography.fontSize.sm,
    fontFamily: typography.fontFamily.mono,
    border: `1px solid ${colors.gray[200]}`,
    marginTop: spacing.sm,
  },
  modalFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: spacing.xl,
    borderTop: `1px solid ${colors.gray[200]}`,
  },
};

// Add missing transitions constant
const transitions = {
  base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// Add hover effects
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  table tbody tr:hover {
    background-color: ${colors.gray[50]};
  }
  
  ${styles.closeButton}:hover {
    background-color: ${colors.gray[100]};
    color: ${colors.gray[600]};
  }
`;
document.head.appendChild(styleSheet);

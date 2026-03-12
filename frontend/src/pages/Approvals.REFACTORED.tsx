/**
 * REFACTORED APPROVALS - Modern UI/UX
 * 
 * Copy this entire file content and replace the content of Approvals.tsx
 * 
 * Improvements:
 * - Modern card-based layout
 * - Better visual hierarchy with icons
 * - Status badges with colors
 * - Improved modal design
 * - Better empty state
 * - Smooth animations
 * - Action buttons with better UX
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { PendingApproval } from '../types';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

export const Approvals: React.FC = () => {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null);

  const loadApprovals = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await apiClient.getPendingApprovals();
      setApprovals(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load approvals');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await apiClient.approveItem(id);
      loadApprovals();
      setSelectedApproval(null);
    } catch (err: any) {
      alert(err.message || 'Failed to approve item');
    }
  };

  const handleReject = async (id: string) => {
    try {
      await apiClient.rejectItem(id);
      loadApprovals();
      setSelectedApproval(null);
    } catch (err: any) {
      alert(err.message || 'Failed to reject item');
    }
  };

  const getApprovalIcon = (type: string) => {
    switch (type) {
      case 'new_vendor':
        return (
          <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
            <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z"/>
          </svg>
        );
      case 'large_transaction':
        return (
          <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
          </svg>
        );
      case 'bulk_reclassification':
        return (
          <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
            <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"/>
          </svg>
        );
      default:
        return (
          <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
          </svg>
        );
    }
  };

  const getApprovalColor = (type: string) => {
    switch (type) {
      case 'new_vendor':
        return { bg: colors.info.light, color: colors.info.dark, border: colors.info.main };
      case 'large_transaction':
        return { bg: colors.warning.light, color: colors.warning.dark, border: colors.warning.main };
      case 'bulk_reclassification':
        return { bg: colors.success.light, color: colors.success.dark, border: colors.success.main };
      default:
        return { bg: colors.gray[100], color: colors.gray[700], border: colors.gray[300] };
    }
  };

  // Loading State
  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingContainer}>
          <div style={styles.spinner}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
              <circle cx="12" cy="12" r="10" stroke={colors.gray[300]} strokeWidth="4"/>
              <path fill={colors.primary.main} d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
          </div>
          <p style={styles.loadingText}>Loading approvals...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container} className="animate-fade-in">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Pending Approvals</h1>
          <p style={styles.subtitle}>
            {approvals.length} item{approvals.length !== 1 ? 's' : ''} requiring your attention
          </p>
        </div>
        <button
          onClick={loadApprovals}
          style={mergeStyles(components.button.base, components.button.outline)}
        >
          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"/>
          </svg>
          Refresh
        </button>
      </div>

      {error && (
        <div style={mergeStyles(components.alert.base, components.alert.error)}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Empty State */}
      {approvals.length === 0 ? (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>
            <svg width="80" height="80" viewBox="0 0 20 20" fill={colors.success.main}>
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
            </svg>
          </div>
          <h2 style={styles.emptyTitle}>All caught up!</h2>
          <p style={styles.emptyText}>You have no pending approvals at this time.</p>
        </div>
      ) : (
        /* Approvals Grid */
        <div style={styles.approvalsGrid}>
          {approvals.map((approval) => {
            const colorScheme = getApprovalColor(approval.approval_type);
            return (
              <div key={approval.approval_id} style={styles.approvalCard} className="animate-slide-in">
                {/* Card Header */}
                <div style={styles.cardHeader}>
                  <div style={{ ...styles.approvalIcon, backgroundColor: colorScheme.bg, color: colorScheme.color }}>
                    {getApprovalIcon(approval.approval_type)}
                  </div>
                  <div style={styles.cardHeaderContent}>
                    <span style={{ ...styles.typeBadge, backgroundColor: colorScheme.bg, color: colorScheme.color, border: `1px solid ${colorScheme.border}` }}>
                      {approval.approval_type.replace('_', ' ')}
                    </span>
                    <span style={styles.approvalDate}>
                      {new Date(approval.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                  </div>
                </div>

                {/* Card Body */}
                <div style={styles.cardBody}>
                  {approval.approval_type === 'new_vendor' && (
                    <>
                      <h3 style={styles.approvalTitle}>New Vendor Detected</h3>
                      <p style={styles.approvalDescription}>
                        A transaction with a new vendor requires your approval before the vendor record is created.
                      </p>
                      <div style={styles.detailsGrid}>
                        <div style={styles.detailItem}>
                          <span style={styles.detailLabel}>Vendor Name</span>
                          <span style={styles.detailValue}>{approval.details.vendor_name}</span>
                        </div>
                        <div style={styles.detailItem}>
                          <span style={styles.detailLabel}>Amount</span>
                          <span style={styles.detailValue}>
                            ${approval.details.amount?.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </>
                  )}

                  {approval.approval_type === 'large_transaction' && (
                    <>
                      <h3 style={styles.approvalTitle}>Large Transaction</h3>
                      <p style={styles.approvalDescription}>
                        This transaction exceeds 10% of your average monthly expenses and requires approval.
                      </p>
                      <div style={styles.detailsGrid}>
                        <div style={styles.detailItem}>
                          <span style={styles.detailLabel}>Amount</span>
                          <span style={styles.detailValue}>
                            ${approval.details.amount?.toFixed(2)}
                          </span>
                        </div>
                        <div style={styles.detailItem}>
                          <span style={styles.detailLabel}>Reason</span>
                          <span style={styles.detailValue}>{approval.details.reason}</span>
                        </div>
                      </div>
                    </>
                  )}

                  {approval.approval_type === 'bulk_reclassification' && (
                    <>
                      <h3 style={styles.approvalTitle}>Bulk Reclassification</h3>
                      <p style={styles.approvalDescription}>
                        The system suggests reclassifying multiple historical transactions.
                      </p>
                      <div style={styles.detailsGrid}>
                        <div style={styles.detailItem}>
                          <span style={styles.detailLabel}>Transactions</span>
                          <span style={styles.detailValue}>
                            {approval.details.transaction_count}
                          </span>
                        </div>
                        <div style={styles.detailItem}>
                          <span style={styles.detailLabel}>New Category</span>
                          <span style={styles.detailValue}>
                            {approval.details.new_category}
                          </span>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Card Footer */}
                <div style={styles.cardFooter}>
                  <button
                    onClick={() => setSelectedApproval(approval)}
                    style={mergeStyles(components.button.base, components.button.ghost)}
                  >
                    <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                      <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                    </svg>
                    View Details
                  </button>
                  <div style={styles.actionButtons}>
                    <button
                      onClick={() => handleReject(approval.approval_id)}
                      style={mergeStyles(components.button.base, components.button.error)}
                    >
                      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                      </svg>
                      Reject
                    </button>
                    <button
                      onClick={() => handleApprove(approval.approval_id)}
                      style={mergeStyles(components.button.base, components.button.success)}
                    >
                      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                      </svg>
                      Approve
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Approval Detail Modal */}
      {selectedApproval && (
        <div style={styles.overlay} onClick={() => setSelectedApproval(null)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()} className="animate-slide-in">
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Approval Details</h2>
              <button onClick={() => setSelectedApproval(null)} style={styles.closeButton}>
                <svg width="24" height="24" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
                </svg>
              </button>
            </div>

            <div style={styles.modalContent}>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Approval ID</span>
                <span style={styles.modalValue}>{selectedApproval.approval_id}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Type</span>
                <span style={styles.modalValue}>
                  {selectedApproval.approval_type.replace('_', ' ')}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Created</span>
                <span style={styles.modalValue}>
                  {new Date(selectedApproval.created_at).toLocaleString()}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject Type</span>
                <span style={styles.modalValue}>{selectedApproval.subject_type}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject ID</span>
                <span style={styles.modalValue}>{selectedApproval.subject_id}</span>
              </div>

              <div style={styles.detailsSection}>
                <div style={styles.modalLabel}>Full Details</div>
                <pre style={styles.detailsJson}>
                  {JSON.stringify(selectedApproval.details, null, 2)}
                </pre>
              </div>
            </div>

            <div style={styles.modalFooter}>
              <button
                onClick={() => handleReject(selectedApproval.approval_id)}
                style={mergeStyles(components.button.base, components.button.error)}
              >
                Reject
              </button>
              <button
                onClick={() => handleApprove(selectedApproval.approval_id)}
                style={mergeStyles(components.button.base, components.button.success)}
              >
                Approve
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
  emptyState: {
    ...components.card.base,
    textAlign: 'center',
    padding: spacing['3xl'],
  },
  emptyIcon: {
    marginBottom: spacing.lg,
  },
  emptyTitle: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.sm,
  },
  emptyText: {
    fontSize: typography.fontSize.base,
    color: colors.gray[600],
  },
  approvalsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
    gap: spacing.lg,
  },
  approvalCard: {
    ...components.card.base,
    display: 'flex',
    flexDirection: 'column',
    transition: `all ${transitions.base}`,
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  approvalIcon: {
    width: '48px',
    height: '48px',
    borderRadius: borderRadius.lg,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  cardHeaderContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  typeBadge: {
    ...components.badge.base,
    alignSelf: 'flex-start',
    textTransform: 'capitalize',
  },
  approvalDate: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[500],
  },
  cardBody: {
    flex: 1,
    marginBottom: spacing.lg,
  },
  approvalTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.sm,
  },
  approvalDescription: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[600],
    lineHeight: typography.lineHeight.relaxed,
    marginBottom: spacing.lg,
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: spacing.md,
  },
  detailItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
  },
  detailLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[500],
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  detailValue: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
  },
  cardFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: spacing.lg,
    borderTop: `1px solid ${colors.gray[200]}`,
  },
  actionButtons: {
    display: 'flex',
    gap: spacing.sm,
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
    gap: spacing.md,
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
  ${styles.approvalCard}:hover {
    transform: translateY(-2px);
    box-shadow: ${shadows.lg};
  }
  
  ${styles.closeButton}:hover {
    background-color: ${colors.gray[100]};
    color: ${colors.gray[600]};
  }
`;
document.head.appendChild(styleSheet);

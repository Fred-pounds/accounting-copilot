import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { PendingApproval } from '../types';

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

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading approvals...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Pending Approvals</h1>
      <p style={styles.subtitle}>
        Review and approve items that require your attention
      </p>

      {error && <div style={styles.error}>{error}</div>}

      {approvals.length === 0 ? (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>✓</div>
          <p style={styles.emptyTitle}>All caught up!</p>
          <p style={styles.emptyText}>You have no pending approvals at this time.</p>
        </div>
      ) : (
        <div style={styles.approvalsList}>
          {approvals.map((approval) => (
            <div key={approval.approval_id} style={styles.approvalCard}>
              <div style={styles.approvalHeader}>
                <div>
                  <span
                    style={{
                      ...styles.badge,
                      backgroundColor:
                        approval.approval_type === 'new_vendor'
                          ? '#d1ecf1'
                          : approval.approval_type === 'large_transaction'
                          ? '#fff3cd'
                          : '#d4edda',
                      color:
                        approval.approval_type === 'new_vendor'
                          ? '#0c5460'
                          : approval.approval_type === 'large_transaction'
                          ? '#856404'
                          : '#155724',
                    }}
                  >
                    {approval.approval_type.replace('_', ' ')}
                  </span>
                </div>
                <div style={styles.approvalDate}>
                  {new Date(approval.created_at).toLocaleDateString()}
                </div>
              </div>

              <div style={styles.approvalBody}>
                {approval.approval_type === 'new_vendor' && (
                  <>
                    <h3 style={styles.approvalTitle}>New Vendor Detected</h3>
                    <p style={styles.approvalDescription}>
                      A transaction with a new vendor requires your approval before the
                      vendor record is created.
                    </p>
                    <div style={styles.detailsGrid}>
                      <div style={styles.detailItem}>
                        <span style={styles.detailLabel}>Vendor Name:</span>
                        <span style={styles.detailValue}>
                          {approval.details.vendor_name}
                        </span>
                      </div>
                      <div style={styles.detailItem}>
                        <span style={styles.detailLabel}>Amount:</span>
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
                      This transaction exceeds 10% of your average monthly expenses and
                      requires approval.
                    </p>
                    <div style={styles.detailsGrid}>
                      <div style={styles.detailItem}>
                        <span style={styles.detailLabel}>Amount:</span>
                        <span style={styles.detailValue}>
                          ${approval.details.amount?.toFixed(2)}
                        </span>
                      </div>
                      <div style={styles.detailItem}>
                        <span style={styles.detailLabel}>Reason:</span>
                        <span style={styles.detailValue}>
                          {approval.details.reason}
                        </span>
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
                        <span style={styles.detailLabel}>Transactions:</span>
                        <span style={styles.detailValue}>
                          {approval.details.transaction_count}
                        </span>
                      </div>
                      <div style={styles.detailItem}>
                        <span style={styles.detailLabel}>New Category:</span>
                        <span style={styles.detailValue}>
                          {approval.details.new_category}
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div style={styles.approvalFooter}>
                <button
                  onClick={() => setSelectedApproval(approval)}
                  style={styles.detailsButton}
                >
                  View Details
                </button>
                <div style={styles.actionButtons}>
                  <button
                    onClick={() => handleReject(approval.approval_id)}
                    style={styles.rejectButton}
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleApprove(approval.approval_id)}
                    style={styles.approveButton}
                  >
                    Approve
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approval Detail Modal */}
      {selectedApproval && (
        <div style={styles.overlay} onClick={() => setSelectedApproval(null)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Approval Details</h2>
              <button
                onClick={() => setSelectedApproval(null)}
                style={styles.closeButton}
              >
                ×
              </button>
            </div>

            <div style={styles.modalContent}>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Approval ID:</span>
                <span style={styles.modalValue}>{selectedApproval.approval_id}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Type:</span>
                <span style={styles.modalValue}>
                  {selectedApproval.approval_type.replace('_', ' ')}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Created:</span>
                <span style={styles.modalValue}>
                  {new Date(selectedApproval.created_at).toLocaleString()}
                </span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject Type:</span>
                <span style={styles.modalValue}>{selectedApproval.subject_type}</span>
              </div>
              <div style={styles.modalField}>
                <span style={styles.modalLabel}>Subject ID:</span>
                <span style={styles.modalValue}>{selectedApproval.subject_id}</span>
              </div>

              <div style={styles.detailsSection}>
                <div style={styles.modalLabel}>Full Details:</div>
                <pre style={styles.detailsJson}>
                  {JSON.stringify(selectedApproval.details, null, 2)}
                </pre>
              </div>
            </div>

            <div style={styles.modalFooter}>
              <button
                onClick={() => handleReject(selectedApproval.approval_id)}
                style={styles.rejectButton}
              >
                Reject
              </button>
              <button
                onClick={() => handleApprove(selectedApproval.approval_id)}
                style={styles.approveButton}
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

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '2rem',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  title: {
    fontSize: '1.875rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
  },
  subtitle: {
    color: '#666',
    marginBottom: '2rem',
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
  emptyState: {
    textAlign: 'center',
    padding: '4rem 2rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  emptyIcon: {
    fontSize: '4rem',
    color: '#28a745',
    marginBottom: '1rem',
  },
  emptyTitle: {
    fontSize: '1.5rem',
    fontWeight: '600',
    marginBottom: '0.5rem',
  },
  emptyText: {
    color: '#666',
  },
  approvalsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  approvalCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
  },
  approvalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem 1.5rem',
    backgroundColor: '#f8f9fa',
    borderBottom: '1px solid #ddd',
  },
  badge: {
    padding: '0.375rem 0.75rem',
    borderRadius: '4px',
    fontSize: '0.875rem',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  approvalDate: {
    fontSize: '0.875rem',
    color: '#666',
  },
  approvalBody: {
    padding: '1.5rem',
  },
  approvalTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    marginBottom: '0.5rem',
  },
  approvalDescription: {
    color: '#666',
    marginBottom: '1rem',
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  detailItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  detailLabel: {
    fontSize: '0.875rem',
    color: '#666',
    fontWeight: '500',
  },
  detailValue: {
    fontSize: '1rem',
    fontWeight: '600',
  },
  approvalFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem 1.5rem',
    backgroundColor: '#f8f9fa',
    borderTop: '1px solid #ddd',
  },
  detailsButton: {
    padding: '0.5rem 1rem',
    backgroundColor: 'transparent',
    color: '#007bff',
    border: '1px solid #007bff',
    borderRadius: '4px',
    fontSize: '0.875rem',
    cursor: 'pointer',
  },
  actionButtons: {
    display: 'flex',
    gap: '0.75rem',
  },
  rejectButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    cursor: 'pointer',
  },
  approveButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.875rem',
    cursor: 'pointer',
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
  modalField: {
    display: 'flex',
    marginBottom: '1rem',
    gap: '0.5rem',
  },
  modalLabel: {
    fontWeight: '600',
    minWidth: '140px',
    color: '#666',
  },
  modalValue: {
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
    gap: '0.75rem',
    padding: '1.5rem',
    borderTop: '1px solid #ddd',
  },
};

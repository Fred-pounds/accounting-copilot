import React, { useState } from 'react';
import type { Transaction } from '../types';

interface TransactionDetailModalProps {
  transaction: Transaction;
  onClose: () => void;
  onCorrect: (id: string, corrections: { category?: string; amount?: number }) => void;
  onApprove: (id: string) => void;
}

export const TransactionDetailModal: React.FC<TransactionDetailModalProps> = ({
  transaction,
  onClose,
  onCorrect,
  onApprove,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedCategory, setEditedCategory] = useState(transaction.category);
  const [editedAmount, setEditedAmount] = useState(transaction.amount.toString());

  const handleCorrect = () => {
    const corrections: { category?: string; amount?: number } = {};
    if (editedCategory !== transaction.category) {
      corrections.category = editedCategory;
    }
    if (parseFloat(editedAmount) !== transaction.amount) {
      corrections.amount = parseFloat(editedAmount);
    }
    if (Object.keys(corrections).length > 0) {
      onCorrect(transaction.transaction_id, corrections);
    }
  };

  const confidencePercent = transaction.classification_confidence * 100;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>Transaction Details</h2>
            <span style={{
              ...styles.statusTag,
              backgroundColor: transaction.status === 'approved' ? 'var(--color-success-light)' : 'var(--color-warning-light)',
              color: transaction.status === 'approved' ? 'var(--color-success-dark)' : 'var(--color-warning-dark)',
            }}>
              {transaction.status === 'approved' ? '✓ ' : '⏳ '}
              {transaction.status.replace('_', ' ')}
            </span>
          </div>
          <button onClick={onClose} style={styles.closeButton}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>

        <div style={styles.content}>
          {/* Basic Information */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4" /><path d="M12 8h.01" /></svg>
              Basic Information
            </h3>
            <div style={styles.fieldGrid}>
              <div style={styles.fieldItem}>
                <span style={styles.fieldLabel}>Date</span>
                <span style={styles.fieldValue}>{new Date(transaction.date).toLocaleDateString()}</span>
              </div>
              <div style={styles.fieldItem}>
                <span style={styles.fieldLabel}>Vendor</span>
                <span style={styles.fieldValue}>{transaction.vendor}</span>
              </div>
              <div style={styles.fieldItem}>
                <span style={styles.fieldLabel}>Type</span>
                <span style={{
                  ...styles.typeBadge,
                  backgroundColor: transaction.type === 'income' ? 'var(--color-success-light)' : 'var(--color-danger-light)',
                  color: transaction.type === 'income' ? 'var(--color-success-dark)' : 'var(--color-danger-dark)',
                }}>
                  {transaction.type}
                </span>
              </div>
              <div style={{ ...styles.fieldItem, gridColumn: '1 / -1' }}>
                <span style={styles.fieldLabel}>Description</span>
                <span style={styles.fieldValue}>{transaction.description}</span>
              </div>
            </div>
          </div>

          {/* Financial Details */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="2"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
              Financial Details
            </h3>
            <div style={styles.fieldGrid}>
              <div style={styles.fieldItem}>
                <span style={styles.fieldLabel}>Amount</span>
                {isEditing ? (
                  <input
                    type="number"
                    value={editedAmount}
                    onChange={(e) => setEditedAmount(e.target.value)}
                    style={styles.input}
                    step="0.01"
                  />
                ) : (
                  <span style={{
                    fontSize: '1.25rem',
                    fontWeight: 800,
                    color: transaction.type === 'income' ? 'var(--color-success)' : 'var(--color-danger)',
                  }}>
                    ${transaction.amount.toFixed(2)}
                  </span>
                )}
              </div>
              <div style={styles.fieldItem}>
                <span style={styles.fieldLabel}>Category</span>
                {isEditing ? (
                  <input
                    type="text"
                    value={editedCategory}
                    onChange={(e) => setEditedCategory(e.target.value)}
                    style={styles.input}
                  />
                ) : (
                  <span style={styles.categoryBadge}>{transaction.category}</span>
                )}
              </div>
              <div style={styles.fieldItem}>
                <span style={styles.fieldLabel}>Currency</span>
                <span style={styles.fieldValue}>{transaction.currency}</span>
              </div>
            </div>
          </div>

          {/* AI Classification */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-warning)" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></svg>
              AI Classification
            </h3>
            <div style={styles.confidenceRow}>
              <span style={styles.fieldLabel}>Confidence</span>
              <div style={styles.confidenceBarWrap}>
                <div style={styles.confidenceBarOuter}>
                  <div style={{
                    ...styles.confidenceBarInner,
                    width: `${confidencePercent}%`,
                    backgroundColor: confidencePercent >= 70 ? 'var(--color-success)' : 'var(--color-warning)',
                  }} />
                </div>
                <span style={{
                  fontWeight: 800,
                  fontSize: '0.9rem',
                  color: confidencePercent >= 70 ? 'var(--color-success)' : 'var(--color-warning)',
                }}>
                  {confidencePercent.toFixed(0)}%
                </span>
              </div>
            </div>
            {transaction.classification_reasoning && (
              <div style={styles.reasoningBox}>
                <span style={styles.fieldLabel}>Reasoning</span>
                <p style={styles.reasoningText}>{transaction.classification_reasoning}</p>
              </div>
            )}
          </div>

          {/* Validation Issues */}
          {transaction.validation_issues.length > 0 && (
            <div style={styles.section}>
              <h3 style={styles.sectionTitle}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                Validation Issues
              </h3>
              <div style={styles.issuesList}>
                {transaction.validation_issues.map((issue, index) => (
                  <div key={index} style={styles.issueItem}>
                    <span style={styles.issueDot} />
                    {issue}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reconciliation */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-info)" strokeWidth="2"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12" /><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /></svg>
              Reconciliation
            </h3>
            <div style={styles.fieldGrid}>
              <div style={styles.fieldItem}>
                <span style={styles.fieldLabel}>Status</span>
                <span style={{
                  ...styles.typeBadge,
                  backgroundColor: transaction.reconciliation_status === 'matched' ? 'var(--color-success-light)' : 'var(--color-warning-light)',
                  color: transaction.reconciliation_status === 'matched' ? 'var(--color-success-dark)' : 'var(--color-warning-dark)',
                }}>
                  {transaction.reconciliation_status}
                </span>
              </div>
              {transaction.document_id && (
                <div style={styles.fieldItem}>
                  <span style={styles.fieldLabel}>Document ID</span>
                  <span style={styles.monoText}>{transaction.document_id}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          {isEditing ? (
            <>
              <button onClick={() => setIsEditing(false)} style={styles.cancelButton}>
                Cancel
              </button>
              <button onClick={handleCorrect} style={styles.saveButton}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                Save Changes
              </button>
            </>
          ) : (
            <>
              <button onClick={onClose} style={styles.cancelButton}>
                Close
              </button>
              {transaction.status === 'pending_review' && (
                <>
                  <button onClick={() => setIsEditing(true)} style={styles.correctButton}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
                    Correct
                  </button>
                  <button onClick={() => onApprove(transaction.transaction_id)} style={styles.approveButton}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                    Approve
                  </button>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
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
    maxWidth: '580px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: 'var(--shadow-xl)',
    animation: 'scaleIn 0.2s ease-out',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: '20px 24px',
    borderBottom: '1px solid var(--color-border)',
  },
  title: {
    fontSize: '1.2rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    margin: 0,
    marginBottom: '6px',
  },
  statusTag: {
    padding: '3px 10px',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.7rem',
    fontWeight: 600,
    textTransform: 'capitalize' as const,
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
  content: {
    padding: '20px 24px',
  },
  section: {
    marginBottom: '20px',
  },
  sectionTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '0.85rem',
    fontWeight: 700,
    color: 'var(--color-text)',
    marginBottom: '12px',
    paddingBottom: '8px',
    borderBottom: '1px solid var(--color-border-light)',
  },
  fieldGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: '12px',
  },
  fieldItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '3px',
  },
  fieldLabel: {
    fontSize: '0.7rem',
    fontWeight: 600,
    color: 'var(--color-text-muted)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  fieldValue: {
    fontSize: '0.9rem',
    fontWeight: 500,
    color: 'var(--color-text)',
  },
  typeBadge: {
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.75rem',
    fontWeight: 600,
    textTransform: 'capitalize' as const,
    width: 'fit-content',
  },
  categoryBadge: {
    display: 'inline-block',
    padding: '3px 10px',
    backgroundColor: 'var(--color-primary-50)',
    color: 'var(--color-primary)',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.8rem',
    fontWeight: 600,
    width: 'fit-content',
  },
  input: {
    padding: '8px 12px',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.9rem',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text)',
    outline: 'none',
    fontFamily: 'inherit',
    width: '100%',
  },
  confidenceRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    marginBottom: '12px',
  },
  confidenceBarWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  confidenceBarOuter: {
    flex: 1,
    height: '8px',
    backgroundColor: 'var(--color-border-light)',
    borderRadius: 'var(--radius-full)',
    overflow: 'hidden',
  },
  confidenceBarInner: {
    height: '100%',
    borderRadius: 'var(--radius-full)',
    transition: 'width 0.5s ease',
  },
  reasoningBox: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    padding: '12px 14px',
    backgroundColor: 'var(--color-surface)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--color-border)',
  },
  reasoningText: {
    fontSize: '0.85rem',
    color: 'var(--color-text-secondary)',
    fontStyle: 'italic',
    lineHeight: 1.5,
    margin: 0,
  },
  issuesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  issueItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: 'var(--color-danger)',
    fontSize: '0.85rem',
    padding: '8px 12px',
    backgroundColor: 'var(--color-danger-light)',
    borderRadius: 'var(--radius-md)',
  },
  issueDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-danger)',
    flexShrink: 0,
  },
  monoText: {
    fontSize: '0.8rem',
    fontFamily: 'monospace',
    color: 'var(--color-text-secondary)',
  },
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '8px',
    padding: '16px 24px',
    borderTop: '1px solid var(--color-border)',
  },
  cancelButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '10px 18px',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text-secondary)',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  correctButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '10px 18px',
    backgroundColor: 'var(--color-warning)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  approveButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
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
  saveButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '10px 18px',
    backgroundColor: 'var(--color-primary)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: '0.85rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
};

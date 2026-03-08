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

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <h2 style={styles.title}>Transaction Details</h2>
          <button onClick={onClose} style={styles.closeButton}>
            ×
          </button>
        </div>

        <div style={styles.content}>
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Basic Information</h3>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Date:</span>
              <span>{new Date(transaction.date).toLocaleDateString()}</span>
            </div>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Vendor:</span>
              <span>{transaction.vendor}</span>
            </div>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Description:</span>
              <span>{transaction.description}</span>
            </div>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Type:</span>
              <span style={{ textTransform: 'capitalize' }}>{transaction.type}</span>
            </div>
          </div>

          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Financial Details</h3>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Amount:</span>
              {isEditing ? (
                <input
                  type="number"
                  value={editedAmount}
                  onChange={(e) => setEditedAmount(e.target.value)}
                  style={styles.input}
                  step="0.01"
                />
              ) : (
                <span
                  style={{
                    color: transaction.type === 'income' ? '#28a745' : '#dc3545',
                    fontWeight: '600',
                  }}
                >
                  ${transaction.amount.toFixed(2)}
                </span>
              )}
            </div>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Category:</span>
              {isEditing ? (
                <input
                  type="text"
                  value={editedCategory}
                  onChange={(e) => setEditedCategory(e.target.value)}
                  style={styles.input}
                />
              ) : (
                <span>{transaction.category}</span>
              )}
            </div>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Currency:</span>
              <span>{transaction.currency}</span>
            </div>
          </div>

          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>AI Classification</h3>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Confidence:</span>
              <span
                style={{
                  color: transaction.classification_confidence >= 0.7 ? '#28a745' : '#ffc107',
                  fontWeight: '600',
                }}
              >
                {(transaction.classification_confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Reasoning:</span>
              <span style={styles.reasoning}>{transaction.classification_reasoning}</span>
            </div>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Status:</span>
              <span style={{ textTransform: 'capitalize' }}>
                {transaction.status.replace('_', ' ')}
              </span>
            </div>
          </div>

          {transaction.validation_issues.length > 0 && (
            <div style={styles.section}>
              <h3 style={styles.sectionTitle}>Validation Issues</h3>
              <ul style={styles.issuesList}>
                {transaction.validation_issues.map((issue, index) => (
                  <li key={index} style={styles.issue}>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Reconciliation</h3>
            <div style={styles.field}>
              <span style={styles.fieldLabel}>Status:</span>
              <span style={{ textTransform: 'capitalize' }}>
                {transaction.reconciliation_status}
              </span>
            </div>
            {transaction.document_id && (
              <div style={styles.field}>
                <span style={styles.fieldLabel}>Document ID:</span>
                <span style={styles.documentId}>{transaction.document_id}</span>
              </div>
            )}
          </div>
        </div>

        <div style={styles.footer}>
          {isEditing ? (
            <>
              <button onClick={() => setIsEditing(false)} style={styles.cancelButton}>
                Cancel
              </button>
              <button onClick={handleCorrect} style={styles.saveButton}>
                Save Corrections
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
                    Correct
                  </button>
                  <button
                    onClick={() => onApprove(transaction.transaction_id)}
                    style={styles.approveButton}
                  >
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
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem',
    borderBottom: '1px solid #ddd',
  },
  title: {
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
  content: {
    padding: '1.5rem',
  },
  section: {
    marginBottom: '1.5rem',
  },
  sectionTitle: {
    fontSize: '1.125rem',
    fontWeight: '600',
    marginBottom: '0.75rem',
    color: '#333',
  },
  field: {
    display: 'flex',
    marginBottom: '0.75rem',
    gap: '0.5rem',
  },
  fieldLabel: {
    fontWeight: '500',
    minWidth: '120px',
    color: '#666',
  },
  reasoning: {
    flex: 1,
    color: '#666',
    fontStyle: 'italic',
  },
  issuesList: {
    margin: 0,
    paddingLeft: '1.5rem',
  },
  issue: {
    color: '#dc3545',
    marginBottom: '0.5rem',
  },
  documentId: {
    fontFamily: 'monospace',
    fontSize: '0.875rem',
    color: '#666',
  },
  input: {
    flex: 1,
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.875rem',
  },
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '0.75rem',
    padding: '1.5rem',
    borderTop: '1px solid #ddd',
  },
  cancelButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  correctButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#ffc107',
    color: '#333',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  approveButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  saveButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
};

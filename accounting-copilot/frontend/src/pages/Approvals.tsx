import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import type { Transaction } from '../types';

export const Approvals: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState<string | null>(null);
  const [selected, setSelected] = useState<Transaction | null>(null);

  const load = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await apiClient.listTransactions({ status: 'pending_review', limit: 100 });
      setTransactions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load pending transactions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleApprove = async (id: string) => {
    setProcessing(id);
    try {
      await apiClient.approveTransaction(id);
      setSelected(null);
      await load();
    } catch (err: any) {
      alert(err.message || 'Failed to approve');
    } finally {
      setProcessing(null);
    }
  };

  const fmt = (v: number) =>
    '$' + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  if (isLoading) return (
    <div style={s.container}>
      <h1 style={s.title}>Pending Approvals</h1>
      <div style={s.center}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
        <span style={{ color: 'var(--color-text-muted)' }}>Loading...</span>
      </div>
    </div>
  );

  return (
    <div style={s.container}>
      <div style={s.header}>
        <div>
          <h1 style={s.title}>Pending Approvals</h1>
          <p style={s.subtitle}>Review and approve transactions that require your attention</p>
        </div>
        {transactions.length > 0 && (
          <span style={s.badge}>{transactions.length} pending</span>
        )}
      </div>

      {error && <div style={s.error}>{error}</div>}

      {transactions.length === 0 ? (
        <div style={s.empty}>
          <div style={s.emptyIcon}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          </div>
          <p style={s.emptyTitle}>All caught up!</p>
          <p style={s.emptyText}>No transactions pending review.</p>
        </div>
      ) : (
        <div style={s.list}>
          {transactions.map((txn, i) => (
            <div key={txn.transaction_id} style={{ ...s.card, animationDelay: `${i * 0.04}s` }}>
              <div style={s.cardBody}>
                <div style={s.cardTop}>
                  <div style={s.cardLeft}>
                    <span style={{ ...s.typeBadge, ...(txn.type === 'income' ? s.incomeBadge : s.expenseBadge) }}>
                      {txn.type}
                    </span>
                    <span style={s.category}>{txn.category}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                    <span style={s.amount}>{fmt(txn.amount)}</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{txn.date}</span>
                  </div>
                </div>
                <div style={s.vendor}>{txn.vendor}</div>
                {txn.description && (
                  <div style={s.desc} title={txn.description}>
                    {txn.description.length > 120 ? txn.description.slice(0, 120) + '…' : txn.description}
                  </div>
                )}
                <div style={s.meta}>
                  {txn.classification_confidence > 0 && (
                    <span>Confidence: {Math.round(txn.classification_confidence * 100)}%</span>
                  )}
                  {txn.source && <span>Source: {txn.source}</span>}
                  {txn.flagged_for_review && (
                    <span style={s.flagged}>⚠ Flagged for review</span>
                  )}
                </div>
                {txn.validation_issues?.length > 0 && (
                  <div style={s.issues}>
                    {txn.validation_issues.map((issue, j) => (
                      <span key={j} style={s.issue}>{issue}</span>
                    ))}
                  </div>
                )}
              </div>
              <div style={s.cardFooter}>
                <button onClick={() => setSelected(txn)} style={s.detailsBtn}>View Details</button>
                <button
                  onClick={() => handleApprove(txn.transaction_id)}
                  disabled={processing === txn.transaction_id}
                  style={{ ...s.approveBtn, opacity: processing === txn.transaction_id ? 0.6 : 1 }}
                >
                  {processing === txn.transaction_id ? 'Approving...' : '✓ Approve'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selected && (
        <div style={s.overlay} onClick={() => setSelected(null)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <h2 style={s.modalTitle}>Transaction Details</h2>
              <button onClick={() => setSelected(null)} style={s.closeBtn}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div style={s.modalBody}>
              {[
                ['ID', selected.transaction_id],
                ['Date', selected.date],
                ['Amount', fmt(selected.amount)],
                ['Type', selected.type],
                ['Category', selected.category],
                ['Vendor', selected.vendor],
                ['Description', selected.description],
                ['Confidence', `${Math.round(selected.classification_confidence * 100)}%`],
                ['Reasoning', selected.classification_reasoning],
                ['Source', selected.source],
              ].map(([label, value]) => value ? (
                <div key={label} style={s.field}>
                  <span style={s.fieldLabel}>{label}</span>
                  <span style={s.fieldValue}>{value}</span>
                </div>
              ) : null)}
              {selected.validation_issues?.length > 0 && (
                <div style={s.field}>
                  <span style={s.fieldLabel}>Issues</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {selected.validation_issues.map((issue, i) => (
                      <span key={i} style={s.issue}>{issue}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div style={s.modalFooter}>
              <button onClick={() => setSelected(null)} style={s.cancelBtn}>Cancel</button>
              <button
                onClick={() => handleApprove(selected.transaction_id)}
                disabled={processing === selected.transaction_id}
                style={{ ...s.approveBtn, opacity: processing === selected.transaction_id ? 0.6 : 1 }}
              >
                {processing === selected.transaction_id ? 'Approving...' : '✓ Approve'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  container: { padding: 'var(--space-page)', maxWidth: 900, margin: '0 auto' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 },
  title: { fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.5px' },
  subtitle: { color: 'var(--color-text-muted)', marginTop: 4, fontSize: '0.9rem' },
  badge: { padding: '6px 14px', backgroundColor: '#fef3c7', color: '#92400e', borderRadius: 'var(--radius-full)', fontSize: '0.8rem', fontWeight: 700 },
  center: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, padding: '4rem' },
  error: { backgroundColor: 'var(--color-danger-light)', color: 'var(--color-danger)', padding: '12px 16px', borderRadius: 'var(--radius-lg)', marginBottom: 16, fontSize: '0.85rem' },
  empty: { textAlign: 'center', padding: '4rem 2rem', backgroundColor: 'var(--color-card)', borderRadius: 'var(--radius-xl)', boxShadow: 'var(--shadow-sm)', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  emptyIcon: { width: 72, height: 72, borderRadius: 20, backgroundColor: 'var(--color-success-light)', color: 'var(--color-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  emptyTitle: { fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: 4 },
  emptyText: { color: 'var(--color-text-muted)', fontSize: '0.9rem' },
  list: { display: 'flex', flexDirection: 'column', gap: 16 },
  card: { backgroundColor: 'var(--color-card)', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-sm)', overflow: 'hidden', borderLeft: '4px solid #f59e0b', animation: 'slideUp 0.3s ease-out both' },
  cardBody: { padding: '18px 22px' },
  cardTop: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  cardLeft: { display: 'flex', alignItems: 'center', gap: 10 },
  typeBadge: { padding: '3px 10px', borderRadius: 'var(--radius-full)', fontSize: '0.75rem', fontWeight: 700, textTransform: 'capitalize' as const },
  incomeBadge: { backgroundColor: '#d1fae5', color: '#065f46' },
  expenseBadge: { backgroundColor: '#fee2e2', color: '#991b1b' },
  category: { fontSize: '0.85rem', color: 'var(--color-text-secondary)', fontWeight: 500 },
  amount: { fontSize: '1.2rem', fontWeight: 800, color: 'var(--color-text)' },
  vendor: { fontSize: '1rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: 4 },
  desc: { fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: 8 },
  meta: { display: 'flex', gap: 16, fontSize: '0.78rem', color: 'var(--color-text-muted)' },
  flagged: { color: '#d97706', fontWeight: 600 },
  issues: { display: 'flex', flexWrap: 'wrap' as const, gap: 6, marginTop: 10 },
  issue: { padding: '3px 10px', backgroundColor: '#fef3c7', color: '#92400e', borderRadius: 'var(--radius-full)', fontSize: '0.75rem', fontWeight: 500 },
  cardFooter: { display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8, padding: '12px 22px', borderTop: '1px solid var(--color-border-light)', backgroundColor: 'var(--color-surface)' },
  detailsBtn: { padding: '7px 16px', backgroundColor: 'transparent', color: 'var(--color-primary)', border: '1.5px solid var(--color-primary)', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' },
  approveBtn: { padding: '7px 18px', backgroundColor: 'var(--color-success)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' },
  overlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15,23,42,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 },
  modal: { backgroundColor: 'var(--color-card)', borderRadius: 'var(--radius-xl)', width: '90%', maxWidth: 560, maxHeight: '90vh', overflow: 'auto', boxShadow: 'var(--shadow-xl)' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid var(--color-border)' },
  modalTitle: { fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-text)', margin: 0 },
  closeBtn: { background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: 4, display: 'flex', borderRadius: 'var(--radius-md)' },
  modalBody: { padding: 24 },
  field: { display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 14 },
  fieldLabel: { fontSize: '0.7rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.5px' },
  fieldValue: { fontSize: '0.9rem', color: 'var(--color-text)', fontWeight: 500 },
  modalFooter: { display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '16px 24px', borderTop: '1px solid var(--color-border)' },
  cancelBtn: { padding: '8px 18px', backgroundColor: 'transparent', color: 'var(--color-text-secondary)', border: '1.5px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' },
};

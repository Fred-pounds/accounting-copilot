import type {
  User,
  Transaction,
  Document,
  DashboardSummary,
  PendingApproval,
  ConversationMessage,
} from '../../types';

export const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  businessName: 'Test Business',
};

export const mockTransactions: Transaction[] = [
  {
    transaction_id: 'txn-1',
    date: '2024-01-15',
    amount: 45.99,
    currency: 'USD',
    type: 'expense',
    category: 'Office Supplies',
    vendor: 'Office Depot',
    description: 'Office supplies purchase',
    classification_confidence: 0.92,
    classification_reasoning: 'Vendor name and line items indicate office supplies',
    status: 'approved',
    flagged_for_review: false,
    validation_issues: [],
    source: 'receipt',
    document_id: 'doc-1',
    reconciliation_status: 'matched',
    created_at: '2024-01-15T10:35:00Z',
    updated_at: '2024-01-15T10:35:00Z',
  },
  {
    transaction_id: 'txn-2',
    date: '2024-01-16',
    amount: 1250.0,
    currency: 'USD',
    type: 'expense',
    category: 'Equipment',
    vendor: 'Tech Store',
    description: 'New laptop',
    classification_confidence: 0.65,
    classification_reasoning: 'Large purchase, low confidence',
    status: 'pending_review',
    flagged_for_review: true,
    validation_issues: ['exceeds_average'],
    source: 'receipt',
    document_id: 'doc-2',
    reconciliation_status: 'unmatched',
    created_at: '2024-01-16T14:20:00Z',
    updated_at: '2024-01-16T14:20:00Z',
  },
];

export const mockDocuments: Document[] = [
  {
    document_id: 'doc-1',
    s3_key: 'documents/user-123/receipts/2024/01/doc-1.jpg',
    upload_timestamp: '2024-01-15T10:30:00Z',
    document_type: 'receipt',
    ocr_status: 'completed',
    extracted_text: 'Office Depot Receipt...',
    parsed_fields: {
      date: '2024-01-15',
      amount: 45.99,
      currency: 'USD',
      vendor: 'Office Depot',
      line_items: [
        { description: 'Paper', amount: 25.99 },
        { description: 'Pens', amount: 20.0 },
      ],
    },
  },
];

export const mockDashboardSummary: DashboardSummary = {
  cash_balance: 15000.0,
  total_income: 25000.0,
  total_expenses: 10000.0,
  profit_trend: [
    { month: '2023-08', profit: 2500 },
    { month: '2023-09', profit: 3000 },
    { month: '2023-10', profit: 2800 },
    { month: '2023-11', profit: 3200 },
    { month: '2023-12', profit: 3500 },
    { month: '2024-01', profit: 4000 },
  ],
  top_categories: [
    { category: 'Office Supplies', amount: 2500 },
    { category: 'Marketing', amount: 2000 },
    { category: 'Utilities', amount: 1500 },
    { category: 'Equipment', amount: 1250 },
    { category: 'Travel', amount: 1000 },
  ],
  pending_approvals_count: 2,
};

export const mockPendingApprovals: PendingApproval[] = [
  {
    approval_id: 'approval-1',
    approval_type: 'large_transaction',
    subject_type: 'transaction',
    subject_id: 'txn-2',
    created_at: '2024-01-16T14:20:00Z',
    status: 'pending',
    details: {
      amount: 1250.0,
      reason: 'Exceeds 10% of average monthly expenses',
    },
  },
  {
    approval_id: 'approval-2',
    approval_type: 'new_vendor',
    subject_type: 'transaction',
    subject_id: 'txn-3',
    created_at: '2024-01-17T09:15:00Z',
    status: 'pending',
    details: {
      vendor_name: 'New Vendor Inc',
      amount: 500.0,
    },
  },
];

export const mockConversationHistory: ConversationMessage[] = [
  {
    message_id: 'msg-1',
    timestamp: '2024-01-15T14:30:00Z',
    role: 'user',
    content: 'What are my top expenses this month?',
  },
  {
    message_id: 'msg-2',
    timestamp: '2024-01-15T14:30:05Z',
    role: 'assistant',
    content: 'Your top expenses this month are Office Supplies ($2,500), Marketing ($2,000), and Utilities ($1,500).',
    response: {
      content: 'Your top expenses this month are Office Supplies ($2,500), Marketing ($2,000), and Utilities ($1,500).',
      citations: ['txn-1', 'txn-4', 'txn-7'],
      confidence: 0.95,
    },
  },
];

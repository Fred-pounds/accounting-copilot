export interface User {
  id: string;
  email: string;
  businessName: string;
}

export interface Transaction {
  transaction_id: string;
  date: string;
  amount: number;
  currency: string;
  type: 'income' | 'expense';
  category: string;
  vendor: string;
  description: string;
  classification_confidence: number;
  classification_reasoning: string;
  status: 'approved' | 'pending_review' | 'rejected';
  flagged_for_review: boolean;
  validation_issues: string[];
  source: string;
  document_id?: string;
  reconciliation_status: 'matched' | 'unmatched' | 'pending';
  created_at: string;
  updated_at: string;
}

export interface Document {
  document_id: string;
  s3_key: string;
  upload_timestamp: string;
  document_type: 'receipt' | 'invoice' | 'bank_statement';
  ocr_status: 'pending' | 'completed' | 'failed';
  extracted_text?: string;
  parsed_fields?: {
    date: string;
    amount: number;
    currency: string;
    vendor: string;
    line_items: Array<{
      description: string;
      amount: number;
    }>;
  };
}

export interface DashboardSummary {
  cash_balance: number;
  total_income: number;
  total_expenses: number;
  profit_trend: Array<{
    month: string;
    income: number;
    expenses: number;
    profit: number;
  }>;
  top_categories: Array<{
    category: string;
    total: number;
  }>;
  pending_approvals_count?: number;
}

export interface AuditEntry {
  action_id: string;
  timestamp: string;
  action_type: 'classification' | 'reconciliation' | 'assistant_query' | 'approval' | 'correction' | 'data_access';
  actor: 'ai' | 'user';
  actor_details?: string;
  subject_type: string;
  subject_id: string;
  action_details: Record<string, any>;
  result: string;
}

export interface PendingApproval {
  approval_id: string;
  approval_type: 'new_vendor' | 'large_transaction' | 'bulk_reclassification';
  subject_type: string;
  subject_id: string;
  created_at: string;
  status: 'pending' | 'approved' | 'rejected';
  details: Record<string, any>;
}

export interface ConversationMessage {
  message_id: string;
  timestamp: string;
  role: 'user' | 'assistant';
  content: string;
  response?: {
    content: string;
    citations: string[];
    confidence: number;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  request_id: string;
  timestamp: string;
}

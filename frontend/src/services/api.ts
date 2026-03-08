import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { authService } from './auth';
import type {
  Transaction,
  Document,
  DashboardSummary,
  AuditEntry,
  PendingApproval,
  ConversationMessage,
  ApiError,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        const tokens = await authService.getTokens();
        if (tokens) {
          config.headers.Authorization = `Bearer ${tokens.idToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await authService.refreshSession();
            const tokens = await authService.getTokens();
            if (tokens && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${tokens.idToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            await authService.signOut();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Document endpoints
  async uploadDocument(file: File): Promise<{ document_id: string; upload_url: string }> {
    const response = await this.client.post('/documents/upload', {
      filename: file.name,
      content_type: file.type,
    });
    return response.data;
  }

  async uploadToS3(url: string, file: File): Promise<void> {
    await axios.put(url, file, {
      headers: {
        'Content-Type': file.type,
      },
    });
  }

  async getDocument(id: string): Promise<Document> {
    const response = await this.client.get(`/documents/${id}`);
    return response.data;
  }

  async listDocuments(params?: { limit?: number; offset?: number }): Promise<Document[]> {
    const response = await this.client.get('/documents', { params });
    return response.data;
  }

  // Transaction endpoints
  async createTransaction(transaction: Partial<Transaction>): Promise<Transaction> {
    const response = await this.client.post('/transactions', transaction);
    return response.data;
  }

  async getTransaction(id: string): Promise<Transaction> {
    const response = await this.client.get(`/transactions/${id}`);
    return response.data;
  }

  async listTransactions(params?: {
    limit?: number;
    offset?: number;
    type?: 'income' | 'expense';
    category?: string;
    start_date?: string;
    end_date?: string;
    status?: string;
  }): Promise<Transaction[]> {
    const response = await this.client.get('/transactions', { params });
    return response.data;
  }

  async updateTransaction(id: string, updates: Partial<Transaction>): Promise<Transaction> {
    const response = await this.client.put(`/transactions/${id}`, updates);
    return response.data;
  }

  async deleteTransaction(id: string): Promise<void> {
    await this.client.delete(`/transactions/${id}`);
  }

  async approveTransaction(id: string): Promise<Transaction> {
    const response = await this.client.post(`/transactions/${id}/approve`);
    return response.data;
  }

  async correctTransaction(id: string, corrections: { category?: string; amount?: number }): Promise<Transaction> {
    const response = await this.client.post(`/transactions/${id}/correct`, corrections);
    return response.data;
  }

  // Dashboard endpoints
  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await this.client.get('/dashboard/summary');
    return response.data;
  }

  async getDashboardTrends(): Promise<any> {
    const response = await this.client.get('/dashboard/trends');
    return response.data;
  }

  // Assistant endpoints
  async queryAssistant(question: string): Promise<ConversationMessage> {
    const response = await this.client.post('/assistant/query', { question });
    return response.data;
  }

  async getConversationHistory(): Promise<ConversationMessage[]> {
    const response = await this.client.get('/assistant/history');
    return response.data;
  }

  // Audit trail endpoints
  async getAuditTrail(params?: {
    start_date?: string;
    end_date?: string;
    action_type?: string;
    transaction_id?: string;
  }): Promise<AuditEntry[]> {
    const response = await this.client.get('/audit-trail', { params });
    return response.data;
  }

  async exportAuditTrail(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> {
    const response = await this.client.get('/audit-trail/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  // Reconciliation endpoints
  async getPendingReconciliation(): Promise<Transaction[]> {
    const response = await this.client.get('/reconciliation/pending');
    return response.data;
  }

  async matchTransaction(receiptId: string, bankTransactionId: string): Promise<void> {
    await this.client.post('/reconciliation/match', {
      receipt_id: receiptId,
      bank_transaction_id: bankTransactionId,
    });
  }

  // Approvals endpoints
  async getPendingApprovals(): Promise<PendingApproval[]> {
    const response = await this.client.get('/approvals/pending');
    return response.data;
  }

  async approveItem(id: string): Promise<void> {
    await this.client.post(`/approvals/${id}/approve`);
  }

  async rejectItem(id: string): Promise<void> {
    await this.client.post(`/approvals/${id}/reject`);
  }
}

export const apiClient = new ApiClient();

import { http, HttpResponse } from 'msw';
import {
  mockTransactions,
  mockDocuments,
  mockDashboardSummary,
  mockPendingApprovals,
  mockConversationHistory,
} from './mockData';

const API_BASE_URL = '/api';

export const handlers = [
  // Authentication endpoints (mocked via Cognito service)
  
  // Document endpoints
  http.post(`${API_BASE_URL}/documents/upload`, async () => {
    return HttpResponse.json({
      document_id: 'doc-new',
      upload_url: 'https://s3.amazonaws.com/presigned-url',
    });
  }),

  http.get(`${API_BASE_URL}/documents/:id`, ({ params }) => {
    const doc = mockDocuments.find((d) => d.document_id === params.id);
    if (!doc) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(doc);
  }),

  http.get(`${API_BASE_URL}/documents`, () => {
    return HttpResponse.json(mockDocuments);
  }),

  // Transaction endpoints
  http.post(`${API_BASE_URL}/transactions`, async ({ request }) => {
    const body = await request.json();
    const newTransaction = {
      transaction_id: 'txn-new',
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(newTransaction);
  }),

  http.get(`${API_BASE_URL}/transactions/:id`, ({ params }) => {
    const txn = mockTransactions.find((t) => t.transaction_id === params.id);
    if (!txn) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(txn);
  }),

  http.get(`${API_BASE_URL}/transactions`, ({ request }) => {
    const url = new URL(request.url);
    const type = url.searchParams.get('type');
    const status = url.searchParams.get('status');
    
    let filtered = [...mockTransactions];
    if (type && type !== 'all') {
      filtered = filtered.filter((t) => t.type === type);
    }
    if (status && status !== 'all') {
      filtered = filtered.filter((t) => t.status === status);
    }
    
    return HttpResponse.json(filtered);
  }),

  http.post(`${API_BASE_URL}/transactions/:id/approve`, ({ params }) => {
    const txn = mockTransactions.find((t) => t.transaction_id === params.id);
    if (!txn) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({ ...txn, status: 'approved' });
  }),

  http.post(`${API_BASE_URL}/transactions/:id/correct`, async ({ params, request }) => {
    const txn = mockTransactions.find((t) => t.transaction_id === params.id);
    if (!txn) {
      return new HttpResponse(null, { status: 404 });
    }
    const corrections = await request.json();
    return HttpResponse.json({ ...txn, ...corrections });
  }),

  // Dashboard endpoints
  http.get(`${API_BASE_URL}/dashboard/summary`, () => {
    return HttpResponse.json(mockDashboardSummary);
  }),

  // Assistant endpoints
  http.post(`${API_BASE_URL}/assistant`, async ({ request }) => {
    const body = await request.json() as { question: string };
    
    // Simulate response time (requirement 6.1: within 5 seconds)
    await new Promise((resolve) => setTimeout(resolve, 100));
    
    const response: any = {
      message_id: `msg-${Date.now()}`,
      timestamp: new Date().toISOString(),
      role: 'assistant',
      content: `This is a response to: ${body.question}`,
      response: {
        content: `This is a response to: ${body.question}`,
        citations: ['txn-1'],
        confidence: 0.85,
      },
    };
    
    return HttpResponse.json(response);
  }),

  http.get(`${API_BASE_URL}/assistant`, () => {
    return HttpResponse.json(mockConversationHistory);
  }),

  // Approvals endpoints
  http.get(`${API_BASE_URL}/approvals`, () => {
    return HttpResponse.json(mockPendingApprovals);
  }),

  http.post(`${API_BASE_URL}/approvals`, async ({ request }) => {
    const body = await request.json() as { action: string; approval_id: string };
    const approval = mockPendingApprovals.find((a) => a.approval_id === body.approval_id);
    if (!approval) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({ ...approval, status: body.action === 'approve' ? 'approved' : 'rejected' });
  }),

  // S3 upload endpoint (mocked)
  http.put('https://s3.amazonaws.com/presigned-url', () => {
    return new HttpResponse(null, { status: 200 });
  }),
];

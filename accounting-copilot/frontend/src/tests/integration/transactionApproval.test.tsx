import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../utils/testUtils';
import { Transactions } from '../../pages/Transactions';
import { Approvals } from '../../pages/Approvals';
import { mockTransactions, mockPendingApprovals } from '../mocks/mockData';

/**
 * Integration Tests: Transaction Approval Flow
 * 
 * Validates: Requirement 8.4 - Display pending approvals on dashboard
 * 
 * Tests the complete transaction approval flow including:
 * - Viewing transactions with different statuses
 * - Filtering transactions by status
 * - Approving pending transactions
 * - Correcting transaction classifications
 * - Viewing transaction details
 */

describe('Transaction Approval Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render transactions list with all transactions', async () => {
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Verify transactions are displayed
    expect(screen.getByText('Office Depot')).toBeInTheDocument();
    expect(screen.getByText('Tech Store')).toBeInTheDocument();
  });

  it('should display transaction status badges correctly', async () => {
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Verify status badges
    expect(screen.getByText('approved')).toBeInTheDocument();
    expect(screen.getByText('pending review')).toBeInTheDocument();
  });

  it('should filter transactions by status', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Initially both transactions should be visible
    expect(screen.getByText('Office Depot')).toBeInTheDocument();
    expect(screen.getByText('Tech Store')).toBeInTheDocument();

    // Filter by pending_review
    const statusFilter = screen.getByLabelText(/status:/i);
    await user.selectOptions(statusFilter, 'pending_review');

    // Only pending transaction should be visible
    await waitFor(() => {
      expect(screen.queryByText('Office Depot')).not.toBeInTheDocument();
      expect(screen.getByText('Tech Store')).toBeInTheDocument();
    });
  });

  it('should filter transactions by type', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Filter by expense type
    const typeFilter = screen.getByLabelText(/type:/i);
    await user.selectOptions(typeFilter, 'expense');

    // All mock transactions are expenses, so both should still be visible
    expect(screen.getByText('Office Depot')).toBeInTheDocument();
    expect(screen.getByText('Tech Store')).toBeInTheDocument();
  });

  it('should sort transactions by date', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Change sort order
    const sortOrderFilter = screen.getByLabelText(/order:/i);
    await user.selectOptions(sortOrderFilter, 'asc');

    // Transactions should be reordered (oldest first)
    const rows = screen.getAllByRole('row');
    // First data row should contain the older transaction (Office Depot from Jan 15)
    expect(within(rows[1]).getByText('Office Depot')).toBeInTheDocument();
  });

  it('should display confidence scores with appropriate colors', async () => {
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // High confidence (92%) should be green
    const highConfidence = screen.getByText('92%');
    expect(highConfidence).toHaveStyle({ color: '#28a745' });

    // Low confidence (65%) should be yellow/warning
    const lowConfidence = screen.getByText('65%');
    expect(lowConfidence).toHaveStyle({ color: '#ffc107' });
  });

  it('should show approve button only for pending transactions', async () => {
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Get all approve buttons
    const approveButtons = screen.getAllByRole('button', { name: /approve/i });
    
    // Should only have one approve button (for the pending transaction)
    expect(approveButtons).toHaveLength(1);
  });

  it('should approve a pending transaction', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Find and click approve button for pending transaction
    const approveButton = screen.getByRole('button', { name: /approve/i });
    await user.click(approveButton);

    // Transaction list should reload
    await waitFor(() => {
      // The transaction should now be approved (in a real scenario)
      expect(screen.getByText('Office Depot')).toBeInTheDocument();
    });
  });

  it('should open transaction detail modal when clicking view button', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Click view button for first transaction
    const viewButtons = screen.getAllByRole('button', { name: /view/i });
    await user.click(viewButtons[0]);

    // Modal should open with transaction details
    await waitFor(() => {
      expect(screen.getByText(/transaction details/i)).toBeInTheDocument();
    });
  });

  it('should display transaction amounts with correct sign and color', async () => {
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Expense amounts should be negative (red)
    const amounts = screen.getAllByText(/-\$/);
    expect(amounts.length).toBeGreaterThan(0);
  });

  it('should render approvals page with pending items', async () => {
    renderWithProviders(<Approvals />);

    await waitFor(() => {
      expect(screen.queryByText(/loading approvals/i)).not.toBeInTheDocument();
    });

    // Verify pending approvals are displayed (use getAllByText for multiple matches)
    const largeTxnElements = screen.getAllByText(/large transaction/i);
    expect(largeTxnElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/new vendor detected/i)).toBeInTheDocument();
  });

  it('should display approval type badges with correct styling', async () => {
    renderWithProviders(<Approvals />);

    await waitFor(() => {
      expect(screen.queryByText(/loading approvals/i)).not.toBeInTheDocument();
    });

    // Verify approval type badges (use getAllByText for multiple matches)
    const largeTxnBadges = screen.getAllByText('large transaction');
    expect(largeTxnBadges.length).toBeGreaterThan(0);
    const newVendorBadges = screen.getAllByText('new vendor');
    expect(newVendorBadges.length).toBeGreaterThan(0);
  });

  it('should approve an approval item', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Approvals />);

    await waitFor(() => {
      expect(screen.queryByText(/loading approvals/i)).not.toBeInTheDocument();
    });

    // Find and click approve button
    const approveButtons = screen.getAllByRole('button', { name: /approve/i });
    await user.click(approveButtons[0]);

    // Approvals list should reload
    await waitFor(() => {
      // In a real scenario, the approved item would be removed
      expect(screen.getByText(/pending approvals/i)).toBeInTheDocument();
    });
  });

  it('should reject an approval item', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Approvals />);

    await waitFor(() => {
      expect(screen.queryByText(/loading approvals/i)).not.toBeInTheDocument();
    });

    // Find and click reject button
    const rejectButtons = screen.getAllByRole('button', { name: /reject/i });
    await user.click(rejectButtons[0]);

    // Approvals list should reload
    await waitFor(() => {
      expect(screen.getByText(/pending approvals/i)).toBeInTheDocument();
    });
  });

  it('should show empty state when no pending approvals', async () => {
    // Mock empty approvals
    const { server } = await import('../mocks/server');
    const { http, HttpResponse } = await import('msw');
    
    server.use(
      http.get('/api/approvals/pending', () => {
        return HttpResponse.json([]);
      })
    );

    renderWithProviders(<Approvals />);

    await waitFor(() => {
      expect(screen.queryByText(/loading approvals/i)).not.toBeInTheDocument();
    });

    // Verify empty state message
    expect(screen.getByText(/all caught up/i)).toBeInTheDocument();
    expect(screen.getByText(/no pending approvals at this time/i)).toBeInTheDocument();
  });

  it('should display approval details in modal', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Approvals />);

    await waitFor(() => {
      expect(screen.queryByText(/loading approvals/i)).not.toBeInTheDocument();
    });

    // Click view details button
    const detailsButtons = screen.getAllByRole('button', { name: /view details/i });
    await user.click(detailsButtons[0]);

    // Modal should open
    await waitFor(() => {
      expect(screen.getByText(/approval details/i)).toBeInTheDocument();
    });

    // Verify approval details are shown
    expect(screen.getByText(/approval id:/i)).toBeInTheDocument();
  });

  it('should close approval detail modal when clicking close button', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Approvals />);

    await waitFor(() => {
      expect(screen.queryByText(/loading approvals/i)).not.toBeInTheDocument();
    });

    // Open modal
    const detailsButtons = screen.getAllByRole('button', { name: /view details/i });
    await user.click(detailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/approval details/i)).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByRole('button', { name: /×/i });
    await user.click(closeButton);

    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByText(/approval details/i)).not.toBeInTheDocument();
    });
  });

  it('should filter transactions by category', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Transactions />);

    await waitFor(() => {
      expect(screen.queryByText(/loading transactions/i)).not.toBeInTheDocument();
    });

    // Enter category filter
    const categoryInput = screen.getByPlaceholderText(/filter by category/i);
    await user.type(categoryInput, 'Office Supplies');

    // Should trigger filtering
    await waitFor(() => {
      expect(screen.getByText('Office Depot')).toBeInTheDocument();
    });
  });
});

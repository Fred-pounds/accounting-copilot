import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../utils/testUtils';
import { Login } from '../../pages/Login';
import { authService } from '../../services/auth';

/**
 * Integration Tests: Authentication Flow
 * 
 * Validates: Requirements 1.1, 5.6, 6.1, 8.4
 * 
 * Tests the complete authentication flow including:
 * - User login with valid credentials
 * - Error handling for invalid credentials
 * - Session timeout handling
 * - Redirect after successful authentication
 */

// Mock the auth service
vi.mock('../../services/auth', () => ({
  authService: {
    signIn: vi.fn(),
    signOut: vi.fn(),
    getCurrentSession: vi.fn(),
    getTokens: vi.fn(),
    refreshSession: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Authentication Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    
    // Default mock: no current session
    vi.mocked(authService.getCurrentSession).mockResolvedValue(null);
  });

  it('should render login form with email and password fields', () => {
    renderWithProviders(<Login />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should successfully authenticate user with valid credentials', async () => {
    const user = userEvent.setup();
    
    // Mock successful sign in
    const mockSession = {
      getIdToken: () => ({
        payload: {
          sub: 'user-123',
          email: 'test@example.com',
          'custom:business_name': 'Test Business',
        },
      }),
    };
    vi.mocked(authService.signIn).mockResolvedValue(mockSession as any);

    renderWithProviders(<Login />);

    // Fill in the form
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'Password123!');
    
    // Submit the form
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify sign in was called with correct credentials
    await waitFor(() => {
      expect(authService.signIn).toHaveBeenCalledWith('test@example.com', 'Password123!');
    });

    // Verify navigation to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should display error message for invalid credentials', async () => {
    const user = userEvent.setup();
    
    // Mock failed sign in
    vi.mocked(authService.signIn).mockRejectedValue(
      new Error('Incorrect username or password')
    );

    renderWithProviders(<Login />);

    // Fill in the form with invalid credentials
    await user.type(screen.getByLabelText(/email/i), 'wrong@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    
    // Submit the form
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/incorrect username or password/i)).toBeInTheDocument();
    });

    // Verify we didn't navigate
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should show loading state during authentication', async () => {
    const user = userEvent.setup();
    
    // Mock slow sign in
    vi.mocked(authService.signIn).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    renderWithProviders(<Login />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'Password123!');
    
    // Submit the form
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify loading state
    expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
  });

  it('should display session timeout message when redirected with timeout parameter', () => {
    renderWithProviders(<Login />, { initialRoute: '/login?timeout=true' });

    expect(
      screen.getByText(/your session has expired due to inactivity/i)
    ).toBeInTheDocument();
  });

  it('should redirect to dashboard if already authenticated', async () => {
    // Mock existing session
    const mockSession = {
      getIdToken: () => ({
        payload: {
          sub: 'user-123',
          email: 'test@example.com',
          'custom:business_name': 'Test Business',
        },
      }),
    };
    vi.mocked(authService.getCurrentSession).mockResolvedValue(mockSession as any);

    renderWithProviders(<Login />);

    // Should navigate to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should prevent form submission with empty fields', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<Login />);

    // Try to submit without filling fields
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    // Auth service should not be called
    expect(authService.signIn).not.toHaveBeenCalled();
  });

  it('should handle network errors gracefully', async () => {
    const user = userEvent.setup();
    
    // Mock network error
    vi.mocked(authService.signIn).mockRejectedValue(
      new Error('Network error')
    );

    renderWithProviders(<Login />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'Password123!');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });
});

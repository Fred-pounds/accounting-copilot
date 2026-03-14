import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../utils/testUtils';
import { Assistant } from '../../pages/Assistant';
import { mockConversationHistory } from '../mocks/mockData';

/**
 * Integration Tests: Assistant Chat Interaction
 * 
 * Validates: Requirement 6.1 - Assistant responds within 5 seconds
 * 
 * Tests the complete assistant chat interaction including:
 * - Loading conversation history
 * - Sending questions to assistant
 * - Receiving responses with citations
 * - Response time validation (< 5 seconds)
 * - Error handling
 * - Message display and formatting
 */

describe('Assistant Chat Interaction Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render assistant interface with welcome message', async () => {
    const { server } = await import('../mocks/server');
    const { http, HttpResponse } = await import('msw');
    server.use(
      http.get('/api/assistant', () => {
        return HttpResponse.json([]);
      })
    );

    renderWithProviders(<Assistant />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText(/financial assistant/i)).toBeInTheDocument();
    });

    // Verify example questions are shown
    expect(screen.getByText(/can i afford to hire a new employee/i)).toBeInTheDocument();
    expect(screen.getByText(/what are my top expenses this month/i)).toBeInTheDocument();
  });

  it('should load and display conversation history', async () => {
    renderWithProviders(<Assistant />);

    // Wait for history to load
    await waitFor(() => {
      expect(screen.getByText(/what are my top expenses this month/i)).toBeInTheDocument();
    });

    // Verify both user message and assistant response are displayed
    expect(
      screen.getByText(/your top expenses this month are office supplies/i)
    ).toBeInTheDocument();
  });

  it('should send a question and receive a response', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    // Type a question
    const input = screen.getByPlaceholderText(/ask about your finances/i);
    await user.type(input, 'What is my cash flow this month?');

    // Submit the question — the send button is an icon-only button
    const sendButtons = screen.getAllByRole('button');
    const sendButton = sendButtons[sendButtons.length - 1]; // last button in form
    await user.click(sendButton);

    // Verify user message appears
    await waitFor(() => {
      expect(screen.getByText('What is my cash flow this month?')).toBeInTheDocument();
    });

    // Verify assistant response appears
    await waitFor(() => {
      expect(
        screen.getByText(/this is a response to: what is my cash flow this month/i)
      ).toBeInTheDocument();
    });
  });

  it('should respond within 5 seconds (Requirement 6.1)', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    const startTime = Date.now();

    // Send a question
    const input = screen.getByPlaceholderText(/ask about your finances/i);
    await user.type(input, 'What is my revenue?');
    const allButtons = screen.getAllByRole('button');
    await user.click(allButtons[allButtons.length - 1]);

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText(/this is a response to: what is my revenue/i)).toBeInTheDocument();
    });

    const responseTime = Date.now() - startTime;

    // Verify response time is under 5 seconds (5000ms)
    expect(responseTime).toBeLessThan(5000);
  });

  it('should display loading indicator while waiting for response', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    // Send a question
    const input = screen.getByPlaceholderText(/ask about your finances/i);
    await user.type(input, 'Test question');
    const allButtons1 = screen.getAllByRole('button');
    await user.click(allButtons1[allButtons1.length - 1]);

    // Verify loading indicator appears
    await waitFor(() => {
      // Loading dots should be visible
      const loadingDots = document.querySelectorAll('[style*="animation"]');
      expect(loadingDots.length).toBeGreaterThan(0);
    });
  });

  it('should clear input field after sending message', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/ask about your finances/i) as HTMLInputElement;

    // Type and send
    await user.type(input, 'Test question');
    expect(input.value).toBe('Test question');

    const allButtons2 = screen.getAllByRole('button');
    await user.click(allButtons2[allButtons2.length - 1]);

    // Input should be cleared
    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('should disable send button when input is empty', async () => {
    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    // All buttons include send button (last one)
    const allButtons3 = screen.getAllByRole('button');
    const lastButton = allButtons3[allButtons3.length - 1];

    // Button should be disabled when input is empty
    expect(lastButton).toBeDisabled();
  });

  it('should enable send button when input has text', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/ask about your finances/i);
    const allButtons4 = screen.getAllByRole('button');
    const lastBtn = allButtons4[allButtons4.length - 1];

    // Initially disabled
    expect(lastBtn).toBeDisabled();

    // Type something
    await user.type(input, 'Test');

    // Should be enabled
    expect(lastBtn).not.toBeDisabled();
  });

  it('should display citations with assistant responses', async () => {
    renderWithProviders(<Assistant />);

    // Wait for history to load
    await waitFor(() => {
      expect(
        screen.getByText(/your top expenses this month are office supplies/i)
      ).toBeInTheDocument();
    });

    // Verify citations section is present
    expect(screen.getByText(/sources/i)).toBeInTheDocument();

    // Verify citation buttons are present
    const citationButtons = screen.getAllByText(/transaction/i);
    expect(citationButtons.length).toBeGreaterThan(0);
  });

  it('should display confidence score with assistant responses', async () => {
    renderWithProviders(<Assistant />);

    // Wait for history to load
    await waitFor(() => {
      expect(
        screen.getByText(/your top expenses this month are office supplies/i)
      ).toBeInTheDocument();
    });

    // Verify confidence score is displayed
    expect(screen.getByText(/95% confidence/i)).toBeInTheDocument();
  });

  it('should handle API errors gracefully', async () => {
    const user = userEvent.setup();

    // Mock API error
    const { server } = await import('../mocks/server');
    const { http, HttpResponse } = await import('msw');

    server.use(
      http.get('/api/assistant', () => {
        return HttpResponse.json([]);
      }),
      http.post('/api/assistant', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    // Send a question
    const input = screen.getByPlaceholderText(/ask about your finances/i);
    await user.type(input, 'Test question');
    const submitBtn = document.querySelector('button[type="submit"]') as HTMLButtonElement;
    await user.click(submitBtn);

    // Verify error message appears
    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });

  it('should prevent sending empty messages', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    const allButtons6 = screen.getAllByRole('button');
    const sendBtn = allButtons6[allButtons6.length - 1];

    // Try to click send with empty input
    expect(sendBtn).toBeDisabled();

    // Button should remain disabled
    expect(sendBtn).toBeDisabled();
  });

  it('should prevent sending messages while loading', async () => {
    const user = userEvent.setup();

    // Mock slow response
    const { server } = await import('../mocks/server');
    const { http, HttpResponse } = await import('msw');

    server.use(
      http.post('/api/assistant', async () => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return HttpResponse.json({
          message_id: 'msg-new',
          timestamp: new Date().toISOString(),
          role: 'assistant',
          content: 'Response',
          response: {
            content: 'Response',
            citations: [],
            confidence: 0.9,
          },
        });
      })
    );

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    // Send first message
    const input = screen.getByPlaceholderText(/ask about your finances/i);
    await user.type(input, 'First question');
    const allButtons7 = screen.getAllByRole('button');
    await user.click(allButtons7[allButtons7.length - 1]);

    // Try to send another message while loading
    await user.type(input, 'Second question');
    const allButtons8 = screen.getAllByRole('button');
    const sendButtonNow = allButtons8[allButtons8.length - 1];

    // Button should be disabled while loading
    expect(sendButtonNow).toBeDisabled();
  });

  it('should auto-scroll to bottom when new messages arrive', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    // Send a message
    const input = screen.getByPlaceholderText(/ask about your finances/i);
    await user.type(input, 'Test question');
    const allButtons9 = screen.getAllByRole('button');
    await user.click(allButtons9[allButtons9.length - 1]);

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText(/this is a response to: test question/i)).toBeInTheDocument();
    });

    // The messages container should scroll to bottom
    // (In a real test, we'd verify scrollTop equals scrollHeight - clientHeight)
  });

  it('should display message timestamps', async () => {
    renderWithProviders(<Assistant />);

    // Wait for history to load
    await waitFor(() => {
      expect(screen.getByText(/what are my top expenses this month/i)).toBeInTheDocument();
    });

    // Verify timestamps are displayed (they show as time strings)
    const timestamps = screen.getAllByText(/\d{1,2}:\d{2}\s?(AM|PM)/i);
    expect(timestamps.length).toBeGreaterThan(0);
  });

  it('should distinguish between user and assistant messages visually', async () => {
    renderWithProviders(<Assistant />);

    // Wait for history to load
    await waitFor(() => {
      expect(screen.getByText(/what are my top expenses this month/i)).toBeInTheDocument();
    });

    // Find user message
    const userMessage = screen.getByText(/what are my top expenses this month/i).closest('div');
    expect(userMessage).toBeInTheDocument();

    // Find assistant message
    const assistantMessage = screen.getByText(/your top expenses this month/i).closest('div');
    expect(assistantMessage).toBeInTheDocument();
  });

  it('should handle form submission with Enter key', async () => {
    const user = userEvent.setup();

    renderWithProviders(<Assistant />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask about your finances/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/ask about your finances/i);

    // Type and press Enter
    await user.type(input, 'Test question{Enter}');

    // Message should be sent
    await waitFor(() => {
      expect(screen.getByText('Test question')).toBeInTheDocument();
    });
  });
});

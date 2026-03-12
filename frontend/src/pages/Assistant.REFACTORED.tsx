/**
 * REFACTORED ASSISTANT - Modern UI/UX
 * 
 * Copy this entire file content and replace the content of Assistant.tsx
 * 
 * Improvements:
 * - Modern chat interface with better message bubbles
 * - Typing indicators with animation
 * - Better empty state with suggestions
 * - Citation chips with hover effects
 * - Confidence badges
 * - Smooth scroll behavior
 * - Better mobile responsiveness
 */

import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import type { ConversationMessage } from '../types';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

export const Assistant: React.FC = () => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadHistory = async () => {
    try {
      const history = await apiClient.getConversationHistory();
      setMessages(history);
    } catch (err: any) {
      console.error('Failed to load conversation history:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ConversationMessage = {
      message_id: `temp-${Date.now()}`,
      timestamp: new Date().toISOString(),
      role: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError('');

    try {
      const response = await apiClient.queryAssistant(input);
      setMessages((prev) => [...prev, response]);
    } catch (err: any) {
      setError(err.message || 'Failed to get response from assistant');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  const suggestions = [
    'Can I afford to hire a new employee?',
    'What are my top expenses this month?',
    'How is my cash flow trending?',
    'What was my revenue last quarter?',
  ];

  return (
    <div style={styles.container} className="animate-fade-in">
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.assistantAvatar}>
            <svg width="32" height="32" viewBox="0 0 20 20" fill="white">
              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
            </svg>
          </div>
          <div>
            <h1 style={styles.title}>Financial Assistant</h1>
            <p style={styles.subtitle}>Ask questions about your business finances</p>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div style={styles.chatContainer}>
        <div style={styles.messagesContainer}>
          {messages.length === 0 && (
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>
                <svg width="64" height="64" viewBox="0 0 20 20" fill={colors.primary.main}>
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
                </svg>
              </div>
              <p style={styles.emptyTitle}>Welcome to your Financial Assistant!</p>
              <p style={styles.emptyText}>
                I can help you understand your finances, answer questions, and provide insights.
              </p>
              <div style={styles.suggestionsContainer}>
                <p style={styles.suggestionsTitle}>Try asking:</p>
                <div style={styles.suggestionsGrid}>
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      style={styles.suggestionChip}
                    >
                      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
                      </svg>
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.message_id}
              style={{
                ...styles.messageWrapper,
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
              }}
              className="animate-slide-in"
            >
              {message.role === 'assistant' && (
                <div style={styles.messageAvatar}>
                  <svg width="24" height="24" viewBox="0 0 20 20" fill="white">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
                  </svg>
                </div>
              )}

              <div
                style={{
                  ...styles.message,
                  ...(message.role === 'user' ? styles.userMessage : styles.assistantMessage),
                }}
              >
                <div style={styles.messageHeader}>
                  <span style={styles.messageRole}>
                    {message.role === 'user' ? 'You' : 'Assistant'}
                  </span>
                  <span style={styles.messageTime}>
                    {new Date(message.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <div style={styles.messageContent}>
                  {message.role === 'user' ? (
                    message.content
                  ) : (
                    <>
                      {message.response?.content}
                      
                      {message.response?.confidence !== undefined && (
                        <div style={styles.confidenceContainer}>
                          <span style={mergeStyles(
                            components.badge.base,
                            message.response.confidence >= 0.8
                              ? components.badge.success
                              : message.response.confidence >= 0.6
                              ? components.badge.warning
                              : components.badge.error
                          )}>
                            {(message.response.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      )}

                      {message.response?.citations && message.response.citations.length > 0 && (
                        <div style={styles.citations}>
                          <div style={styles.citationsTitle}>
                            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/>
                            </svg>
                            Sources:
                          </div>
                          <div style={styles.citationsGrid}>
                            {message.response.citations.map((citation, index) => (
                              <button
                                key={index}
                                style={styles.citation}
                                onClick={() => {
                                  window.location.href = `/transactions?id=${citation}`;
                                }}
                              >
                                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
                                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"/>
                                </svg>
                                Transaction {citation.substring(0, 8)}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              {message.role === 'user' && (
                <div style={{ ...styles.messageAvatar, backgroundColor: colors.primary.main }}>
                  <svg width="24" height="24" viewBox="0 0 20 20" fill="white">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
                  </svg>
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div style={{ ...styles.messageWrapper, justifyContent: 'flex-start' }}>
              <div style={styles.messageAvatar}>
                <svg width="24" height="24" viewBox="0 0 20 20" fill="white">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
                </svg>
              </div>
              <div style={{ ...styles.message, ...styles.assistantMessage }}>
                <div style={styles.loadingIndicator}>
                  <span style={styles.loadingDot}>●</span>
                  <span style={styles.loadingDot}>●</span>
                  <span style={styles.loadingDot}>●</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div style={mergeStyles(components.alert.base, components.alert.error)}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} style={styles.inputForm}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your finances..."
            style={styles.input}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            style={mergeStyles(
              components.button.base,
              components.button.primary,
              styles.sendButton,
              (isLoading || !input.trim()) && styles.sendButtonDisabled
            )}
          >
            {isLoading ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25"/>
                <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: spacing.xl,
    maxWidth: '1000px',
    margin: '0 auto',
    height: 'calc(100vh - 120px)',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    marginBottom: spacing.lg,
  },
  headerContent: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.lg,
  },
  assistantAvatar: {
    width: '64px',
    height: '64px',
    borderRadius: borderRadius.xl,
    backgroundColor: colors.primary.main,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: shadows.md,
  },
  title: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: typography.fontWeight.bold,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: typography.fontSize.base,
    color: colors.gray[600],
  },
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: 'white',
    borderRadius: borderRadius.xl,
    boxShadow: shadows.lg,
    overflow: 'hidden',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: spacing.xl,
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.lg,
  },
  emptyState: {
    textAlign: 'center',
    padding: `${spacing['3xl']} ${spacing.xl}`,
    color: colors.gray[600],
  },
  emptyIcon: {
    marginBottom: spacing.lg,
  },
  emptyTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.sm,
  },
  emptyText: {
    fontSize: typography.fontSize.base,
    marginBottom: spacing.xl,
  },
  suggestionsContainer: {
    marginTop: spacing.xl,
  },
  suggestionsTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[700],
    marginBottom: spacing.md,
  },
  suggestionsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: spacing.sm,
  },
  suggestionChip: {
    ...components.button.base,
    ...components.button.outline,
    justifyContent: 'flex-start',
    textAlign: 'left',
    fontSize: typography.fontSize.sm,
    padding: spacing.md,
  },
  messageWrapper: {
    display: 'flex',
    gap: spacing.sm,
    alignItems: 'flex-start',
  },
  messageAvatar: {
    width: '40px',
    height: '40px',
    borderRadius: borderRadius.full,
    backgroundColor: colors.info.main,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  message: {
    maxWidth: '70%',
    padding: spacing.lg,
    borderRadius: borderRadius.lg,
    boxShadow: shadows.sm,
  },
  userMessage: {
    backgroundColor: colors.primary.main,
    color: 'white',
  },
  assistantMessage: {
    backgroundColor: colors.gray[100],
    color: colors.gray[900],
  },
  messageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
    fontSize: typography.fontSize.xs,
    opacity: 0.8,
  },
  messageRole: {
    fontWeight: typography.fontWeight.semibold,
  },
  messageTime: {},
  messageContent: {
    lineHeight: typography.lineHeight.relaxed,
    fontSize: typography.fontSize.base,
  },
  confidenceContainer: {
    marginTop: spacing.md,
  },
  citations: {
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTop: `1px solid ${colors.gray[300]}`,
  },
  citationsTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs,
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[700],
    marginBottom: spacing.sm,
  },
  citationsGrid: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  citation: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.xs,
    padding: `${spacing.xs} ${spacing.sm}`,
    backgroundColor: colors.primary.light,
    color: colors.primary.dark,
    border: `1px solid ${colors.primary.main}`,
    borderRadius: borderRadius.md,
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.medium,
    cursor: 'pointer',
    transition: `all ${transitions.base}`,
  },
  loadingIndicator: {
    display: 'flex',
    gap: spacing.sm,
    padding: spacing.sm,
  },
  loadingDot: {
    fontSize: typography.fontSize.lg,
    color: colors.gray[400],
    animation: 'pulse 1.5s ease-in-out infinite',
  },
  inputForm: {
    display: 'flex',
    gap: spacing.md,
    padding: spacing.lg,
    borderTop: `1px solid ${colors.gray[200]}`,
    backgroundColor: colors.gray[50],
  },
  input: {
    ...components.input.base,
    flex: 1,
    fontSize: typography.fontSize.base,
  },
  sendButton: {
    minWidth: 'auto',
    padding: spacing.md,
  },
  sendButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
};

// Add missing transitions constant
const transitions = {
  base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// Add CSS animations
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }
  
  ${styles.citation}:hover {
    background-color: ${colors.primary.main};
    color: white;
    transform: translateY(-1px);
    box-shadow: ${shadows.md};
  }
  
  ${styles.suggestionChip}:hover {
    background-color: ${colors.primary.light};
    border-color: ${colors.primary.main};
  }
`;
document.head.appendChild(styleSheet);

import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import type { ConversationMessage } from '../types';

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

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Financial Assistant</h1>
        <p style={styles.subtitle}>Ask questions about your business finances</p>
      </div>

      <div style={styles.chatContainer}>
        <div style={styles.messagesContainer}>
          {messages.length === 0 && (
            <div style={styles.emptyState}>
              <p style={styles.emptyTitle}>Welcome to your Financial Assistant!</p>
              <p style={styles.emptyText}>
                Ask me questions like:
              </p>
              <ul style={styles.examplesList}>
                <li>Can I afford to hire a new employee?</li>
                <li>What are my top expenses this month?</li>
                <li>How is my cash flow trending?</li>
                <li>What was my revenue last quarter?</li>
              </ul>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.message_id}
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
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div style={styles.messageContent}>
                {message.role === 'user' ? (
                  message.content
                ) : (
                  <>
                    {message.response?.content}
                    {message.response?.citations && message.response.citations.length > 0 && (
                      <div style={styles.citations}>
                        <div style={styles.citationsTitle}>Sources:</div>
                        {message.response.citations.map((citation, index) => (
                          <button
                            key={index}
                            style={styles.citation}
                            onClick={() => {
                              // Navigate to transaction detail
                              window.location.href = `/transactions?id=${citation}`;
                            }}
                          >
                            Transaction {citation.substring(0, 8)}...
                          </button>
                        ))}
                      </div>
                    )}
                    {message.response?.confidence !== undefined && (
                      <div style={styles.confidence}>
                        Confidence: {(message.response.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div style={{ ...styles.message, ...styles.assistantMessage }}>
              <div style={styles.messageHeader}>
                <span style={styles.messageRole}>Assistant</span>
              </div>
              <div style={styles.loadingIndicator}>
                <span style={styles.loadingDot}>●</span>
                <span style={styles.loadingDot}>●</span>
                <span style={styles.loadingDot}>●</span>
              </div>
            </div>
          )}

          {error && (
            <div style={styles.errorMessage}>
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

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
            style={{
              ...styles.sendButton,
              ...(isLoading || !input.trim() ? styles.sendButtonDisabled : {}),
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '2rem',
    maxWidth: '900px',
    margin: '0 auto',
    height: 'calc(100vh - 4rem)',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    marginBottom: '1.5rem',
  },
  title: {
    fontSize: '1.875rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
  },
  subtitle: {
    color: '#666',
  },
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem 1rem',
    color: '#666',
  },
  emptyTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    marginBottom: '1rem',
  },
  emptyText: {
    marginBottom: '1rem',
  },
  examplesList: {
    textAlign: 'left',
    display: 'inline-block',
    margin: '0 auto',
  },
  message: {
    maxWidth: '80%',
    padding: '1rem',
    borderRadius: '8px',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#007bff',
    color: 'white',
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f5f5f5',
    color: '#333',
  },
  messageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.5rem',
    fontSize: '0.75rem',
    opacity: 0.8,
  },
  messageRole: {
    fontWeight: '600',
  },
  messageTime: {},
  messageContent: {
    lineHeight: 1.5,
  },
  citations: {
    marginTop: '1rem',
    paddingTop: '1rem',
    borderTop: '1px solid #ddd',
  },
  citationsTitle: {
    fontSize: '0.875rem',
    fontWeight: '600',
    marginBottom: '0.5rem',
  },
  citation: {
    display: 'inline-block',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.75rem',
    cursor: 'pointer',
    marginRight: '0.5rem',
    marginBottom: '0.5rem',
  },
  confidence: {
    marginTop: '0.5rem',
    fontSize: '0.75rem',
    opacity: 0.7,
  },
  loadingIndicator: {
    display: 'flex',
    gap: '0.5rem',
  },
  loadingDot: {
    animation: 'pulse 1.5s ease-in-out infinite',
  },
  errorMessage: {
    backgroundColor: '#fee',
    color: '#c33',
    padding: '1rem',
    borderRadius: '8px',
    alignSelf: 'center',
  },
  inputForm: {
    display: 'flex',
    gap: '0.75rem',
    padding: '1.5rem',
    borderTop: '1px solid #ddd',
  },
  input: {
    flex: 1,
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  sendButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    fontWeight: '500',
    cursor: 'pointer',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
};

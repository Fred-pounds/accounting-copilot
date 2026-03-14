import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import type { ConversationMessage } from '../types';

/** Minimal markdown → React elements renderer */
function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  const inlineFormat = (line: string, key: string): React.ReactNode => {
    // Bold + italic, bold, italic, inline code
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
    let last = 0;
    let m: RegExpExecArray | null;
    let idx = 0;
    while ((m = regex.exec(line)) !== null) {
      if (m.index > last) parts.push(line.slice(last, m.index));
      if (m[2]) parts.push(<strong key={`${key}-${idx++}`}><em>{m[2]}</em></strong>);
      else if (m[3]) parts.push(<strong key={`${key}-${idx++}`}>{m[3]}</strong>);
      else if (m[4]) parts.push(<em key={`${key}-${idx++}`}>{m[4]}</em>);
      else if (m[5]) parts.push(<code key={`${key}-${idx++}`} style={inlineCodeStyle}>{m[5]}</code>);
      last = m.index + m[0].length;
    }
    if (last < line.length) parts.push(line.slice(last));
    return parts.length === 1 ? parts[0] : parts;
  };

  while (i < lines.length) {
    const line = lines[i];

    // Headings
    const h3 = line.match(/^###\s+(.*)/);
    const h2 = line.match(/^##\s+(.*)/);
    const h1 = line.match(/^#\s+(.*)/);
    if (h1) { elements.push(<h3 key={i} style={mdH1}>{inlineFormat(h1[1], `h1-${i}`)}</h3>); i++; continue; }
    if (h2) { elements.push(<h4 key={i} style={mdH2}>{inlineFormat(h2[1], `h2-${i}`)}</h4>); i++; continue; }
    if (h3) { elements.push(<h5 key={i} style={mdH3}>{inlineFormat(h3[1], `h3-${i}`)}</h5>); i++; continue; }

    // Unordered list
    if (/^[-*]\s+/.test(line)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(<li key={i} style={mdLi}>{inlineFormat(lines[i].replace(/^[-*]\s+/, ''), `li-${i}`)}</li>);
        i++;
      }
      elements.push(<ul key={`ul-${i}`} style={mdUl}>{items}</ul>);
      continue;
    }

    // Ordered list
    if (/^\d+\.\s+/.test(line)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(<li key={i} style={mdLi}>{inlineFormat(lines[i].replace(/^\d+\.\s+/, ''), `oli-${i}`)}</li>);
        i++;
      }
      elements.push(<ol key={`ol-${i}`} style={mdUl}>{items}</ol>);
      continue;
    }

    // Blank line
    if (line.trim() === '') { i++; continue; }

    // Paragraph
    elements.push(<p key={i} style={mdP}>{inlineFormat(line, `p-${i}`)}</p>);
    i++;
  }

  return elements;
}

const inlineCodeStyle: React.CSSProperties = { fontFamily: 'monospace', backgroundColor: 'rgba(0,0,0,0.07)', padding: '1px 4px', borderRadius: 3, fontSize: '0.85em' };
const mdH1: React.CSSProperties = { fontSize: '1rem', fontWeight: 700, margin: '10px 0 4px' };
const mdH2: React.CSSProperties = { fontSize: '0.95rem', fontWeight: 700, margin: '8px 0 4px' };
const mdH3: React.CSSProperties = { fontSize: '0.9rem', fontWeight: 600, margin: '6px 0 4px' };
const mdUl: React.CSSProperties = { margin: '4px 0', paddingLeft: '20px' };
const mdLi: React.CSSProperties = { marginBottom: '2px', lineHeight: 1.5 };
const mdP: React.CSSProperties = { margin: '4px 0', lineHeight: 1.6 };

const suggestedQuestions = [
  "Can I afford to hire a new employee?",
  "What are my top expenses this month?",
  "How is my cash flow trending?",
  "What was my revenue last quarter?",
];

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
    await sendMessage(input);
  };

  const sendMessage = async (text: string) => {
    const userMessage: ConversationMessage = {
      message_id: `temp-${Date.now()}`,
      timestamp: new Date().toISOString(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError('');

    try {
      const response = await apiClient.queryAssistant(text);
      setMessages((prev) => [...prev, response]);
    } catch (err: any) {
      setError(err.message || 'Failed to get response from assistant');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.pageHeader}>
        <h1 style={styles.pageTitle}>Assistant</h1>
        <p style={styles.pageSubtitle}>Ask questions about your business finances</p>
      </div>
      <div style={styles.chatContainer}>
        <div style={styles.messagesContainer}>
          {messages.length === 0 && (
            <div style={styles.emptyState}>
              <div style={styles.emptyIconWrap}>
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <h2 style={styles.emptyTitle}>Financial Assistant</h2>
              <p style={styles.emptyText}>
                Ask questions about your business finances and get AI-powered insights
              </p>
              <div style={styles.suggestionsGrid}>
                {suggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    style={styles.suggestionChip}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.message_id}
              style={{
                ...styles.messageRow,
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {message.role === 'assistant' && (
                <div style={styles.aiAvatar}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                </div>
              )}
              <div
                style={{
                  ...styles.message,
                  ...(message.role === 'user' ? styles.userMessage : styles.assistantMessage),
                }}
              >
                <div style={styles.messageContent}>
                  {message.role === 'user' ? (
                    message.content
                  ) : (
                    <>
                      <div>{renderMarkdown(message.response?.content || message.content || '')}</div>
                      {message.response?.citations && message.response.citations.length > 0 && (
                        <div style={styles.citations}>
                          <div style={styles.citationsTitle}>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                            </svg>
                            Sources
                          </div>
                          {message.response.citations.map((citation, index) => (
                            <button
                              key={index}
                              style={styles.citation}
                              onClick={() => {
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
                          <span style={{
                            ...styles.confidenceBadge,
                            backgroundColor: message.response.confidence >= 0.7 ? 'var(--color-success-light)' : 'var(--color-warning-light)',
                            color: message.response.confidence >= 0.7 ? 'var(--color-success-dark)' : 'var(--color-warning-dark)',
                          }}>
                            {(message.response.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>
                <div style={{
                  ...styles.messageTime,
                  textAlign: message.role === 'user' ? 'right' : 'left',
                }}>
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div style={{ ...styles.messageRow, justifyContent: 'flex-start' }}>
              <div style={styles.aiAvatar}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <div style={{ ...styles.message, ...styles.assistantMessage }}>
                <div style={styles.loadingIndicator}>
                  <span className="loading-dot" style={styles.loadingDot}>●</span>
                  <span className="loading-dot" style={styles.loadingDot}>●</span>
                  <span className="loading-dot" style={styles.loadingDot}>●</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div style={styles.errorMessage}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
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
            placeholder="Ask about your finances..."
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
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: 'var(--space-page)',
    maxWidth: '900px',
    margin: '0 auto',
    height: 'calc(100vh - 2rem)',
    display: 'flex',
    flexDirection: 'column',
  },
  pageHeader: {
    marginBottom: '16px',
    flexShrink: 0,
  },
  pageTitle: {
    fontSize: '1.75rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    letterSpacing: '-0.5px',
  },
  pageSubtitle: {
    fontSize: '0.85rem',
    color: 'var(--color-text-muted)',
    marginTop: '4px',
  },
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: 'var(--color-card)',
    borderRadius: 'var(--radius-xl)',
    boxShadow: 'var(--shadow-md)',
    overflow: 'hidden',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    background: 'linear-gradient(180deg, var(--color-surface) 0%, var(--color-card) 100%)',
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem 1rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    animation: 'fadeIn 0.5s ease-out',
  },
  emptyIconWrap: {
    width: '72px',
    height: '72px',
    borderRadius: '20px',
    backgroundColor: 'var(--color-primary-50)',
    color: 'var(--color-primary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '16px',
  },
  emptyTitle: {
    fontSize: '1.3rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    marginBottom: '8px',
  },
  emptyText: {
    color: 'var(--color-text-muted)',
    marginBottom: '24px',
    maxWidth: '360px',
    fontSize: '0.9rem',
  },
  suggestionsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '10px',
    width: '100%',
    maxWidth: '520px',
  },
  suggestionChip: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 14px',
    backgroundColor: 'var(--color-surface)',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    fontSize: '0.8rem',
    color: 'var(--color-text-secondary)',
    cursor: 'pointer',
    textAlign: 'left',
    fontFamily: 'inherit',
    transition: 'all var(--transition-fast)',
  },
  messageRow: {
    display: 'flex',
    gap: '10px',
    alignItems: 'flex-end',
    animation: 'slideUp 0.3s ease-out',
  },
  aiAvatar: {
    width: '32px',
    height: '32px',
    borderRadius: '10px',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  message: {
    maxWidth: '75%',
    padding: '12px 16px',
    borderRadius: '16px',
  },
  userMessage: {
    background: 'linear-gradient(135deg, #6366f1, #7c3aed)',
    color: 'white',
    borderBottomRightRadius: '4px',
  },
  assistantMessage: {
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text)',
    border: '1px solid var(--color-border)',
    borderBottomLeftRadius: '4px',
  },
  messageContent: {
    lineHeight: 1.6,
    fontSize: '0.9rem',
  },
  messageTime: {
    fontSize: '0.65rem',
    opacity: 0.5,
    marginTop: '6px',
  },
  citations: {
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid var(--color-border)',
  },
  citationsTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '0.75rem',
    fontWeight: 600,
    color: 'var(--color-text-muted)',
    marginBottom: '8px',
  },
  citation: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '4px 10px',
    backgroundColor: 'var(--color-primary)',
    color: 'white',
    border: 'none',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.7rem',
    fontWeight: 600,
    cursor: 'pointer',
    marginRight: '6px',
    marginBottom: '4px',
    fontFamily: 'inherit',
  },
  confidence: {
    marginTop: '8px',
  },
  confidenceBadge: {
    padding: '3px 10px',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.7rem',
    fontWeight: 600,
    display: 'inline-block',
  },
  loadingIndicator: {
    display: 'flex',
    gap: '6px',
    padding: '4px 0',
  },
  loadingDot: {
    fontSize: '1rem',
    color: 'var(--color-primary)',
  },
  errorMessage: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: 'var(--color-danger-light)',
    color: 'var(--color-danger)',
    padding: '12px 16px',
    borderRadius: 'var(--radius-lg)',
    alignSelf: 'center',
    fontSize: '0.85rem',
    fontWeight: 500,
  },
  inputForm: {
    display: 'flex',
    gap: '10px',
    padding: '16px 20px',
    borderTop: '1px solid var(--color-border)',
    backgroundColor: 'var(--color-card)',
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    border: '1.5px solid var(--color-border)',
    borderRadius: 'var(--radius-full)',
    fontSize: '0.9rem',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text)',
    outline: 'none',
    fontFamily: 'inherit',
  },
  sendButton: {
    width: '44px',
    height: '44px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #6366f1, #7c3aed)',
    color: 'white',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    flexShrink: 0,
    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
    fontFamily: 'inherit',
  },
  sendButtonDisabled: {
    background: '#cbd5e1',
    cursor: 'not-allowed',
    boxShadow: 'none',
  },
};

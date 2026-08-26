'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface Message {
  role: 'user' | 'bot';
  content: string;
  rewrittenQuery?: string | null;
}

export default function Chat({ courseId }: { courseId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [queryRewriting, setQueryRewriting] = useState(true);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const historyContext = newMessages.slice(-6).map(m => ({
        role: m.role,
        content: m.content
      }));

      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: userMessage, 
          course_id: courseId,
          query_rewriting: queryRewriting,
          history: historyContext
        }),
      });
      
      const data = await res.json();
      setMessages(prev => [
        ...prev, 
        { 
          role: 'bot', 
          content: data.answer || "Error processing request",
          rewrittenQuery: data.rewritten_query || null
        }
      ]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', content: "Network error occurred." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ 
        padding: '1.25rem 1.5rem', 
        borderBottom: '1px solid var(--border)', 
        background: 'rgba(255,255,255,0.01)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem'
      }}>
        <div>
          <h3 style={{ margin: 0, color: '#fff', fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>Scribo AI Assistant</span>
          </h3>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
            Query this lecture index with citations.
          </p>
        </div>

        {/* Query Rewriting On/Off Toggle Button */}
        <button
          type="button"
          onClick={() => setQueryRewriting(!queryRewriting)}
          title={queryRewriting ? "Query Rewriting is ON: reformulates ambiguous questions & expands domain acronyms" : "Query Rewriting is OFF: uses exact raw student question"}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.75rem',
            borderRadius: '20px',
            border: queryRewriting 
              ? '1px solid rgba(99, 102, 241, 0.4)' 
              : '1px solid rgba(255, 255, 255, 0.1)',
            background: queryRewriting 
              ? 'rgba(99, 102, 241, 0.15)' 
              : 'rgba(255, 255, 255, 0.03)',
            cursor: 'pointer',
            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
            outline: 'none',
            userSelect: 'none',
            flexShrink: 0
          }}
        >
          <span style={{ 
            fontSize: '0.85rem',
            filter: queryRewriting ? 'drop-shadow(0 0 4px rgba(99, 102, 241, 0.8))' : 'grayscale(1)',
            transition: 'filter 0.2s'
          }}>
            ⚡
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', textAlign: 'left' }}>
            <span style={{ 
              fontSize: '0.72rem', 
              fontWeight: 700, 
              letterSpacing: '0.03em', 
              textTransform: 'uppercase',
              color: queryRewriting ? '#c7d2fe' : 'var(--text-muted)'
            }}>
              Query Rewriting
            </span>
          </div>

          {/* Toggle Switch Visual Pill */}
          <div style={{
            width: '28px',
            height: '16px',
            borderRadius: '10px',
            background: queryRewriting ? 'var(--primary)' : 'rgba(255,255,255,0.15)',
            position: 'relative',
            transition: 'background 0.2s',
            marginLeft: '0.2rem'
          }}>
            <div style={{
              position: 'absolute',
              top: '2px',
              left: queryRewriting ? '14px' : '2px',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: '#fff',
              transition: 'left 0.2s ease',
              boxShadow: '0 1px 3px rgba(0,0,0,0.4)'
            }} />
          </div>
        </button>
      </div>
      
      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', overscrollBehavior: 'contain' }}>
        {messages.length === 0 && (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '4rem', padding: '0 2rem' }}>
            <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>🤖</span>
            <p style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>Ask me any question about the lecture. I will reply using grounded citations.</p>
            <div style={{ marginTop: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: queryRewriting ? '#a5b4fc' : 'var(--text-muted)', background: 'rgba(255,255,255,0.03)', padding: '0.35rem 0.75rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
              <span>⚡ Query Rewriting is <strong>{queryRewriting ? 'ENABLED' : 'DISABLED'}</strong></span>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '88%' }}>
            <div style={{ 
              background: msg.role === 'user' ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%)' : 'rgba(255, 255, 255, 0.03)', 
              color: '#fff',
              border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
              padding: '0.85rem 1.25rem', 
              borderRadius: '16px',
              borderBottomRightRadius: msg.role === 'user' ? '0' : '16px',
              borderBottomLeftRadius: msg.role === 'bot' ? '0' : '16px',
              lineHeight: '1.5',
              fontSize: '0.95rem',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
            }}>
              {msg.role === 'bot' ? (
                <div>
                  {/* Rewritten Query Badge */}
                  {msg.rewrittenQuery && (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      marginBottom: '0.65rem',
                      padding: '0.3rem 0.6rem',
                      borderRadius: '8px',
                      background: 'rgba(99, 102, 241, 0.12)',
                      border: '1px solid rgba(99, 102, 241, 0.25)',
                      fontSize: '0.78rem',
                      color: '#c7d2fe',
                      lineHeight: '1.3'
                    }}>
                      <span style={{ fontSize: '0.85rem' }}>⚡</span>
                      <span><strong>Rewritten for search:</strong> &ldquo;{msg.rewrittenQuery}&rdquo;</span>
                    </div>
                  )}
                  <div style={{ fontSize: '0.95rem' }} className="chat-markdown">
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[[rehypeKatex, { strict: false, throwOnError: false }]]}
                      components={{
                        p: ({node, ...props}) => <p style={{ margin: 0, marginBottom: '0.5rem' }} {...props} />,
                        pre: ({node, ...props}) => <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '0.5rem', borderRadius: '4px', overflowX: 'auto', margin: '0.5rem 0' }} {...props} />,
                        code: ({node, ...props}) => <code style={{ background: 'rgba(0,0,0,0.2)', padding: '0.1rem 0.3rem', borderRadius: '4px', color: '#f43f5e' }} {...props} />
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ alignSelf: 'flex-start', color: 'var(--text-muted)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem' }}>
            <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--primary)', animation: 'pulse 1s infinite alternate' }} />
            {queryRewriting ? 'Rewriting query & retrieving lecture context...' : 'Retrieving lecture context & answering...'}
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={sendMessage} style={{ display: 'flex', padding: '1rem', borderTop: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)' }}>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={queryRewriting ? "Ask anything (query rewriter is ON)..." : "Ask anything (exact query search)..."} 
          style={{ 
            flex: 1, 
            padding: '0.8rem 1.2rem', 
            borderRadius: '10px', 
            border: '1px solid var(--border)', 
            outline: 'none', 
            fontSize: '0.95rem', 
            color: '#fff', 
            backgroundColor: 'rgba(255,255,255,0.03)',
            transition: 'border-color 0.2s'
          }}
          onFocus={(e) => e.target.style.borderColor = 'rgba(99, 102, 241, 0.6)'}
          onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
        />
        <button 
          type="submit" 
          disabled={isLoading || !input.trim()}
          style={{ 
            marginLeft: '0.6rem', 
            padding: '0 1.5rem', 
            background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%)', 
            color: '#fff', 
            border: 'none', 
            borderRadius: '10px', 
            cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer', 
            fontWeight: 600,
            fontSize: '0.95rem',
            opacity: isLoading || !input.trim() ? 0.6 : 1,
            transition: 'opacity 0.2s'
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}


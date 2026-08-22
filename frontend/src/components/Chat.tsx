'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'bot';
  content: string;
}

export default function Chat({ courseId }: { courseId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage, course_id: courseId }),
      });
      
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'bot', content: data.answer || "Error processing request" }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', content: "Network error occurred." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
      <div style={{ padding: '1.5rem', borderBottom: '1px solid #eee', background: '#fafafa' }}>
        <h3 style={{ margin: 0, color: '#333', fontSize: '1.2rem' }}>Scribo AI Assistant</h3>
        <p style={{ margin: 0, color: '#666', fontSize: '0.9rem', marginTop: '0.2rem' }}>Ask questions about this course.</p>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', overscrollBehavior: 'contain' }}>
        {messages.length === 0 && (
          <div style={{ color: '#aaa', textAlign: 'center', marginTop: '2rem' }}>
            No messages yet. Ask me anything!
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
            <div style={{ 
              background: msg.role === 'user' ? '#0070f3' : '#f1f3f5', 
              color: msg.role === 'user' ? '#fff' : '#333',
              padding: '0.8rem 1.2rem', 
              borderRadius: '12px',
              borderBottomRightRadius: msg.role === 'user' ? '0' : '12px',
              borderBottomLeftRadius: msg.role === 'bot' ? '0' : '12px',
              lineHeight: '1.5'
            }}>
              {msg.role === 'bot' ? (
                <div style={{ fontSize: '0.95rem' }}>
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ alignSelf: 'flex-start', color: '#666', fontSize: '0.9rem', fontStyle: 'italic', padding: '0.5rem' }}>
            Thinking...
          </div>
        )}
      </div>

      <form onSubmit={sendMessage} style={{ display: 'flex', padding: '1rem', borderTop: '1px solid #eee', background: '#fff' }}>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..." 
          style={{ flex: 1, padding: '0.8rem 1rem', borderRadius: '8px', border: '1px solid #ddd', outline: 'none', fontSize: '1rem', color: '#000', backgroundColor: '#fff' }}
        />
        <button 
          type="submit" 
          disabled={isLoading || !input.trim()}
          style={{ marginLeft: '0.5rem', padding: '0 1.2rem', background: '#0070f3', color: '#fff', border: 'none', borderRadius: '8px', cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}
        >
          Send
        </button>
      </form>
    </div>
  );
}

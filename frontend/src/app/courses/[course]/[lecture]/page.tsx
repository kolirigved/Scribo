import Link from 'next/link';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import Chat from '@/components/Chat';

export default async function LecturePage({ params }: { params: Promise<{ course: string, lecture: string }> }) {
  const { course, lecture } = await params;
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const res = await fetch(`${API_URL}/courses/${course}/lectures/${lecture}`, { 
    cache: 'no-store' 
  });
  
  if (!res.ok) {
    notFound();
  }
  
  const data = await res.json();

  return (
    <main style={{ padding: '2rem 3rem', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexShrink: 0 }}>
        <Link href={`/courses/${course}`} style={{ color: 'var(--text-muted)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.95rem' }}>
          ← Back to {course.toUpperCase()}
        </Link>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Study Workspace</span>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', margin: 0 }}>Lecture: {lecture.toUpperCase()}</h2>
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 450px', gap: '2rem', flex: 1, minHeight: 0, alignItems: 'stretch' }}>
        {/* Left Column: Markdown Notes (Scrollable) */}
        <div 
          className="glass-panel" 
          style={{ 
            padding: '3rem', 
            overflowY: 'auto', 
            color: '#e5e7eb', 
            lineHeight: '1.7',
            fontSize: '1.05rem'
          }}
        >
          <ReactMarkdown 
            remarkPlugins={[remarkMath]}
            rehypePlugins={[[rehypeKatex, { strict: false, throwOnError: false }]]}
            components={{
              h1: ({node, ...props}) => <h1 style={{ color: '#fff', fontSize: '2.2rem', fontWeight: 800, borderBottom: '1px solid var(--border)', paddingBottom: '0.8rem', marginTop: '0', marginBottom: '1.5rem' }} {...props} />,
              h2: ({node, ...props}) => <h2 style={{ color: '#a5b4fc', fontSize: '1.6rem', fontWeight: 700, marginTop: '2.5rem', marginBottom: '1rem' }} {...props} />,
              h3: ({node, ...props}) => <h3 style={{ color: '#cbd5e1', fontSize: '1.25rem', fontWeight: 600, marginTop: '1.8rem', marginBottom: '0.8rem' }} {...props} />,
              p: ({node, ...props}) => <p style={{ marginBottom: '1.2rem', color: '#cbd5e1' }} {...props} />,
              li: ({node, ...props}) => <li style={{ marginBottom: '0.6rem', marginLeft: '1.2rem', color: '#cbd5e1' }} {...props} />,
              pre: ({node, ...props}) => (
                <pre style={{ 
                  background: 'rgba(0,0,0,0.4)', 
                  padding: '1.2rem', 
                  borderRadius: '8px', 
                  overflowX: 'auto', 
                  border: '1px solid var(--border)',
                  marginBottom: '1.5rem',
                  fontFamily: 'monospace'
                }} {...props} />
              ),
              code: ({node, ...props}) => (
                <code style={{ 
                  background: 'rgba(0,0,0,0.3)', 
                  padding: '0.2rem 0.4rem', 
                  borderRadius: '4px', 
                  fontSize: '0.9em', 
                  color: '#f43f5e',
                  fontFamily: 'monospace'
                }} {...props} />
              )
            }}
          >
            {data.markdown}
          </ReactMarkdown>
        </div>
        
        {/* Right Column: Chat Component */}
        <div style={{ height: '100%', minHeight: 0 }}>
          <Chat courseId={course} />
        </div>
      </div>
    </main>
  );
}

import Link from 'next/link';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

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
    <main style={{ padding: '2rem 4rem', fontFamily: 'system-ui, sans-serif', maxWidth: '900px', margin: '0 auto', lineHeight: '1.6' }}>
      <Link href={`/courses/${course}`} style={{ color: '#666', textDecoration: 'none', marginBottom: '2rem', display: 'inline-block' }}>
        ← Back to {course.toUpperCase()}
      </Link>
      
      <div style={{ background: '#fff', padding: '3rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflowWrap: 'break-word', wordBreak: 'break-word', overflowX: 'auto', color: '#333' }}>
        <ReactMarkdown 
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            h1: ({node, ...props}) => <h1 style={{ borderBottom: '2px solid #eee', paddingBottom: '0.5rem', marginTop: '2rem' }} {...props} />,
            h2: ({node, ...props}) => <h2 style={{ color: '#2c3e50', marginTop: '1.5rem' }} {...props} />,
            h3: ({node, ...props}) => <h3 style={{ color: '#34495e' }} {...props} />,
            p: ({node, ...props}) => <p style={{ fontSize: '1.1rem', color: '#333', marginBottom: '1rem', whiteSpace: 'pre-wrap' }} {...props} />,
            li: ({node, ...props}) => <li style={{ fontSize: '1.1rem', color: '#333', marginBottom: '0.5rem' }} {...props} />,
            pre: ({node, ...props}) => <pre style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', overflowX: 'auto', marginBottom: '1rem', color: '#333' }} {...props} />,
            code: ({node, ...props}) => <code style={{ background: '#f8f9fa', padding: '0.2rem 0.4rem', borderRadius: '4px', fontSize: '0.9em', color: '#e83e8c' }} {...props} />
          }}
        >
          {data.markdown}
        </ReactMarkdown>
      </div>
      
      {/* Interactive Audio/JSON features will go here in the future */}
    </main>
  );
}

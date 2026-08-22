import Link from 'next/link';
import { notFound } from 'next/navigation';

export default async function CoursePage({ params }: { params: Promise<{ course: string }> }) {
  const { course } = await params;
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const res = await fetch(`${API_URL}/courses/${course}`, { cache: 'no-store' });
  
  if (!res.ok) {
    notFound();
  }
  
  const data = await res.json();

  return (
    <main style={{ padding: '6rem 2rem', maxWidth: '800px', margin: '0 auto' }}>
      <Link href="/" style={{ color: 'var(--text-muted)', textDecoration: 'none', marginBottom: '2.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.95rem', transition: 'color 0.2s' }}>
        ← Back to Courses
      </Link>
      
      <div style={{ marginBottom: '3rem' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--primary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Course Syllabus</span>
        <h1 style={{ fontSize: '3rem', fontWeight: 800, color: '#fff', marginTop: '0.5rem', letterSpacing: '-0.02em' }}>
          {data.course.toUpperCase()}
        </h1>
      </div>
      
      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#a5b4fc' }}>Ingested Lectures</h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {data.lectures.map((lecture: string) => (
          <Link 
            key={lecture} 
            href={`/courses/${data.course}/${lecture}`}
            className="glass-panel glass-panel-hover"
            style={{
              padding: '1.5rem 2rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              textDecoration: 'none',
              color: '#fff',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ fontSize: '1.5rem' }}>📄</span>
              <div>
                <span style={{ fontWeight: 700, fontSize: '1.15rem', display: 'block' }}>Lecture: {lecture.toUpperCase()}</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Fully indexed & RAG-ready</span>
              </div>
            </div>
            <span style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.95rem' }}>Study Notes →</span>
          </Link>
        ))}
      </div>
      
      {data.lectures.length === 0 && (
        <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <p>No lectures ingested for this course yet.</p>
        </div>
      )}
    </main>
  );
}

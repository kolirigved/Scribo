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
    <main style={{ padding: '4rem', fontFamily: 'system-ui, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <Link href="/" style={{ color: '#666', textDecoration: 'none', marginBottom: '2rem', display: 'inline-block' }}>
        ← Back to Courses
      </Link>
      
      <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', color: '#333' }}>
        Course: {data.course.toUpperCase()}
      </h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '2rem' }}>
        {data.lectures.map((lecture: string) => (
          <Link 
            key={lecture} 
            href={`/courses/${data.course}/${lecture}`}
            style={{
              padding: '1.5rem',
              background: '#f8f9fa',
              border: '1px solid #e9ecef',
              borderRadius: '8px',
              textDecoration: 'none',
              color: '#099268',
              fontSize: '1.2rem',
              fontWeight: 'bold',
            }}
          >
            📄 Lecture: {lecture}
          </Link>
        ))}
      </div>
      
      {data.lectures.length === 0 && (
        <p style={{ color: '#666' }}>No lectures found for this course.</p>
      )}
    </main>
  );
}

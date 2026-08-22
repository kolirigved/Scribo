import Link from 'next/link';

export default async function Home() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const res = await fetch(`${API_URL}/courses`, { cache: 'no-store' }).catch(() => null);
  const data = res ? await res.json() : { courses: [] };

  return (
    <main style={{ padding: '4rem', fontFamily: 'system-ui, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', color: '#333' }}>📚 Scribo Knowledge Engine</h1>
      <p style={{ fontSize: '1.2rem', color: '#666', marginBottom: '2rem' }}>Select a course to view generated lecture notes.</p>
      
      {data.courses.length === 0 ? (
        <div style={{ padding: '2rem', background: '#ffebee', borderRadius: '8px', color: '#c62828' }}>
          <strong>No courses found!</strong> Ensure you have processed a lecture and the FastAPI backend is running on port 8000.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {data.courses.map((course: string) => (
            <Link 
              key={course} 
              href={`/courses/${course}`}
              style={{
                padding: '1.5rem',
                background: '#f8f9fa',
                border: '1px solid #e9ecef',
                borderRadius: '8px',
                textDecoration: 'none',
                color: '#228be6',
                fontSize: '1.2rem',
                fontWeight: 'bold',
                transition: 'all 0.2s ease'
              }}
            >
              Course: {course.toUpperCase()}
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}

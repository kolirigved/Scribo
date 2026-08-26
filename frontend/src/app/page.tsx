import Link from 'next/link';

export default async function Home() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const res = await fetch(`${API_URL}/courses`, { cache: 'no-store' }).catch(() => null);
  const data = res ? await res.json() : { courses: [] };

  return (
    <main style={{ padding: '6rem 2rem', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
        <h1 style={{
          fontSize: '3.5rem',
          fontWeight: 800,
          marginBottom: '1rem',
          background: 'linear-gradient(135deg, #fff 0%, #a5b4fc 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.03em'
        }}>
          Scribo Notes Pipeline
        </h1>
        <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)', fontWeight: 400 }}>
          Synthesize lecture recordings into structured study guides.
        </p>
      </div>

      {data.courses.length === 0 ? (
        <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
          <span style={{ fontSize: '2.5rem', marginBottom: '1rem', display: 'block' }}>⚠️</span>
          <h3 style={{ fontSize: '1.25rem', color: '#fca5a5', marginBottom: '0.5rem' }}>No Courses Found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: '1.6' }}>
            Ensure the FastAPI server is running on port 8000 and that you have processed at least one lecture using the CLI:<br />
            <code style={{ background: 'rgba(0,0,0,0.3)', padding: '0.2rem 0.5rem', borderRadius: '4px', display: 'inline-block', marginTop: '0.5rem', color: '#a5b4fc' }}>
              scribo process -c [course] -l [lecture] -a [audio_path]
            </code>
          </p>
        </div>
      ) : (
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1.5rem', color: '#a5b4fc' }}>Your Active Courses</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {data.courses.map((course: string) => (
              <Link
                key={course}
                href={`/courses/${course}`}
                className="glass-panel glass-panel-hover"
                style={{
                  padding: '2rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  textDecoration: 'none',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <div style={{ position: 'absolute', top: 0, left: 0, height: '4px', width: '100%', background: 'linear-gradient(90deg, var(--primary), var(--secondary))' }} />
                <span style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--secondary)', fontWeight: 600 }}>Active Syllabus</span>
                <span style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff' }}>
                  {course.toUpperCase()}
                </span>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  View Lectures →
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}

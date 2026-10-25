export async function POST(request, { params }) {
  const { id } = await params;
  const userId = request.headers.get('X-User-Id');
  const headers = { 'Content-Type': 'application/json' };
  if (userId) headers['X-User-Id'] = userId;

  try {
    const body = await request.json();
    const res = await fetch(`http://localhost:5008/api/journals/${id}/entries`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json({ error: 'Journal service unavailable' }, { status: 503 });
  }
}

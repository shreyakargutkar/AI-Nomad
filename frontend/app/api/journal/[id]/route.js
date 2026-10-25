const base = (id) => `http://localhost:5008/api/journals/${id}`;

export async function GET(request, { params }) {
  const { id } = await params;
  const userId = request.headers.get('X-User-Id');
  const headers = {};
  if (userId) headers['X-User-Id'] = userId;

  try {
    const res = await fetch(base(id), { headers });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json({ error: 'Journal service unavailable' }, { status: 503 });
  }
}

const JOURNAL_URL = 'http://localhost:5008/api/journals';

function forwardHeaders(request) {
  const userId = request.headers.get('X-User-Id');
  const headers = { 'Content-Type': 'application/json' };
  if (userId) headers['X-User-Id'] = userId;
  return headers;
}

export async function GET(request) {
  try {
    const res = await fetch(JOURNAL_URL, { headers: forwardHeaders(request) });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json(
      { error: 'Journal service unavailable. Run ./start_services.sh' },
      { status: 503 }
    );
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const res = await fetch(JOURNAL_URL, {
      method: 'POST',
      headers: forwardHeaders(request),
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json(
      { error: 'Journal service unavailable. Run ./start_services.sh' },
      { status: 503 }
    );
  }
}

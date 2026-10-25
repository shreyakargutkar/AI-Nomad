const BACKEND_URL =
  process.env.RECOMMENDATIONS_API_URL || 'http://localhost:5011/api/recommendations';

export async function POST(request) {
  let data;
  try {
    data = await request.json();
  } catch {
    return Response.json({ error: 'Invalid request body' }, { status: 400 });
  }

  try {
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(45000),
    });

    let result;
    try {
      result = await response.json();
    } catch {
      return Response.json(
        { error: 'Recommendations service returned an invalid response.' },
        { status: 502 }
      );
    }

    if (!response.ok) {
      return Response.json(
        { error: result.error || 'Failed to load recommendations' },
        { status: response.status }
      );
    }
    return Response.json(result);
  } catch (err) {
    const isTimeout = err?.name === 'TimeoutError' || err?.name === 'AbortError';
    return Response.json(
      {
        error: isTimeout
          ? 'Recommendations timed out — external place data may be slow. Try again.'
          : 'Recommendations service unavailable. Start backends with ./start_services.sh from the project root.',
      },
      { status: 503 }
    );
  }
}

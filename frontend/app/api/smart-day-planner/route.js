/**
 * Next.js API proxy for the Smart Day Planner backend (port 5013).
 * Keeps the frontend from calling localhost directly in the browser.
 */

const BACKEND_URL =
  process.env.SMART_DAY_PLANNER_API_URL || 'http://localhost:5013/optimize';

export async function POST(request) {
  let data;
  try {
    data = await request.json();
  } catch {
    return Response.json({ error: 'Invalid request body — send valid JSON.' }, { status: 400 });
  }

  if (!data || typeof data !== 'object') {
    return Response.json({ error: 'Request body must be a JSON object.' }, { status: 400 });
  }

  // Client-side guard for places count
  const { places } = data;
  if (!places || !Array.isArray(places)) {
    return Response.json(
      { error: 'Missing required field: places (must be an array)' },
      { status: 400 }
    );
  }

  if (places.length < 2 || places.length > 6) {
    return Response.json(
      { error: 'Places array must contain between 2 and 6 destinations.' },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(30000),
    });

    let result;
    try {
      result = await response.json();
    } catch {
      return Response.json(
        { error: 'Smart Day Planner backend returned an invalid response.' },
        { status: 502 }
      );
    }

    if (!response.ok) {
      return Response.json(
        { error: result.error || 'Day path optimization failed.' },
        { status: response.status }
      );
    }

    return Response.json(result);
  } catch (err) {
    const isTimeout = err?.name === 'TimeoutError' || err?.name === 'AbortError';
    return Response.json(
      {
        error: isTimeout
          ? 'Optimization request timed out. Please try again.'
          : 'Smart Day Planner service unavailable. Start backends with ./start_services.sh from the project root.',
      },
      { status: 503 }
    );
  }
}

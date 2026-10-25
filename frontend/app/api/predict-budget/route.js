/**
 * Next.js API proxy for the Smart Budget Predictor backend (port 5012).
 * Keeps the frontend from calling localhost directly in the browser.
 */

const BACKEND_URL =
  process.env.BUDGET_PREDICTOR_API_URL || 'http://localhost:5012/predict-budget';

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

  // Client-side guard for empty required fields
  const required = [
    'destination_country',
    'total_stays',
    'adults',
    'children',
    'hotel',
    'reserved_room_type',
    'budget',
  ];
  const missing = required.filter(
    (key) => data[key] === undefined || data[key] === null || data[key] === ''
  );
  if (missing.length) {
    return Response.json(
      { error: `Missing required fields: ${missing.join(', ')}` },
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
        { error: 'Budget predictor returned an invalid response.' },
        { status: 502 }
      );
    }

    if (!response.ok) {
      return Response.json(
        { error: result.error || 'Budget prediction failed.' },
        { status: response.status }
      );
    }

    return Response.json(result);
  } catch (err) {
    const isTimeout = err?.name === 'TimeoutError' || err?.name === 'AbortError';
    return Response.json(
      {
        error: isTimeout
          ? 'Budget prediction timed out. Please try again.'
          : 'Budget predictor service unavailable. Start backends with ./start_services.sh from the project root.',
      },
      { status: 503 }
    );
  }
}

export async function POST(request) {
  const data = await request.json();

  try {
    const response = await fetch('http://localhost:5009/api/budget-intelligence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    if (!response.ok) {
      return Response.json(result, { status: response.status });
    }
    return Response.json(result);
  } catch {
    return Response.json(
      {
        error:
          'Budget intelligence service unavailable. Start backends with ./start_services.sh from the project root.',
      },
      { status: 503 }
    );
  }
}

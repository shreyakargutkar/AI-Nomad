export async function POST(request) {
  const data = await request.json();

  try {
    const response = await fetch("http://localhost:5006/api/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
          "Chatbot service unavailable. Start backends with ./start_services.sh from the project root.",
        reply: "I cannot reach the server right now. Please ensure ./start_services.sh is running.",
      },
      { status: 503 }
    );
  }
}

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'), override=True)

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    client = None

chat_history = []

@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    global chat_history

    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    chat_history.append({"role": "user", "content": user_message})

    try:
        if client is None:
            bot_reply = f"Echo: {user_message}"
        else:
            messages = [{"role": "system", "content": "You are a helpful travel assistant."}]
            for msg in chat_history:
                messages.append({"role": "user" if msg["role"] == "user" else "assistant", "content": msg["content"]})
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
                messages=messages,
                temperature=0.7,
                max_tokens=512
            )
            bot_reply = response.choices[0].message.content

        chat_history.append({"role": "bot", "content": bot_reply})

        return jsonify({"reply": bot_reply})

    except Exception as e:
        if "rate" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
            return jsonify({"reply": f"Echo (API limit): {user_message}"})
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5006)
"""PrismLive AI assistant Flask blueprint (Gemini API)."""
import os
import requests
from flask import Blueprint, jsonify, request

ai_chat_bp = Blueprint("ai_chat", __name__)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_PROMPT = """
You are Prism AI, a helpful, friendly assistant inside the PrismLive website.
Give clear, practical answers. If the visitor asks about PrismLive-specific
accounts, bookings, messages, or website data that is not supplied to you,
say you cannot access that private data and direct them to the relevant page.
Never claim to have performed an action in the website unless a real backend
feature confirms it. Do not ask for passwords, OTPs, API keys, or payment details.
Keep answers readable and concise.
"""

@ai_chat_bp.post("/api/ai-chat")
def ai_chat():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "AI is not configured yet. Add GEMINI_API_KEY to your environment."}), 503

    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 4000:
        return jsonify({"error": "Please keep each message under 4,000 characters."}), 413

    # Accept only a short, validated conversation history from the browser.
    contents = []
    if isinstance(history, list):
        for item in history[-10:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            text = item.get("text")
            if role in ("user", "model") and isinstance(text, str) and text.strip():
                contents.append({"role": role, "parts": [{"text": text[:4000]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    try:
        response = requests.post(
            GEMINI_API_URL.format(model=model),
            params={"key": api_key},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents,
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 900},
            },
            timeout=35,
        )
        response.raise_for_status()
        data = response.json()
        answer = "".join(
            part.get("text", "")
            for part in data.get("candidates", [{}])[0]
                .get("content", {}).get("parts", [])
            if isinstance(part, dict)
        ).strip()
        if not answer:
            return jsonify({"error": "The AI did not return a text answer. Please try again."}), 502
        return jsonify({"reply": answer})
    except requests.Timeout:
        return jsonify({"error": "The AI took too long to respond. Please try again."}), 504
    except requests.RequestException:
        # Avoid returning provider details or secrets to the browser.
        return jsonify({"error": "Could not connect to the AI service. Check your API key, model, and server logs."}), 502

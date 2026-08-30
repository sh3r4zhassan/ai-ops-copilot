import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from agent import run_agent, SYSTEM_PROMPT

app = Flask(__name__)
CORS(app)
API_KEY = os.getenv("API_KEY", "")

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["30 per hour"])

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard your instructions",
    "reveal your instructions",
    "you are now",
    "system prompt",
]


def looks_like_injection(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in INJECTION_PATTERNS)


def strip_if_leaked(answer: str) -> str:
    if SYSTEM_PROMPT[:60].lower() in answer.lower():
        return "The response was blocked because it appeared to leak internal instructions."
    return answer


@app.route("/diagnose", methods=["POST"])
@limiter.limit("10 per hour")
def diagnose():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    question = data.get("question", "")

    if looks_like_injection(question):
        return jsonify({"answer": "This request contains patterns associated with prompt injection and was not processed."}), 400

    answer = run_agent(question)
    answer = strip_if_leaked(answer)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

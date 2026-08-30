import os
from flask import Flask, request, jsonify
from agent import run_agent
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("API_KEY", "")


@app.route("/diagnose", methods=["POST"])
def diagnose():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    question = data.get("question", "")
    answer = run_agent(question)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

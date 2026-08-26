from flask import Flask, request, jsonify
from agent import run_agent

app = Flask(__name__)


@app.route("/diagnose", methods=["POST"])
def diagnose():
    data = request.get_json()
    question = data.get("question", "")
    answer = run_agent(question)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

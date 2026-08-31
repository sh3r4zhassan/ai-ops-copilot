import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from kubernetes import client, config as k8s_config
from agent import run_agent, SYSTEM_PROMPT

app = Flask(__name__)
CORS(app)
API_KEY = os.getenv("API_KEY", "")

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["60 per hour"])

INCIDENT_GROUP = "aiops.example.com"
INCIDENT_VERSION = "v1alpha1"
INCIDENT_PLURAL = "incidents"
NAMESPACE = "default"

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard your instructions",
    "reveal your instructions",
    "you are now",
    "system prompt",
]


def looks_like_injection(text):
    lowered = text.lower()
    return any(pattern in lowered for pattern in INJECTION_PATTERNS)


def strip_if_leaked(answer):
    if SYSTEM_PROMPT[:60].lower() in answer.lower():
        return "The response was blocked because it appeared to leak internal instructions."
    return answer


def check_auth():
    return not (API_KEY and request.headers.get("X-API-Key") != API_KEY)


def get_incident_api():
    k8s_config.load_incluster_config()
    return client.CustomObjectsApi()


@app.route("/diagnose", methods=["POST"])
@limiter.limit("60 per hour")
def diagnose():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    question = data.get("question", "")

    if looks_like_injection(question):
        return jsonify({"answer": "This request contains patterns associated with prompt injection and was not processed."}), 400

    answer = run_agent(question)
    answer = strip_if_leaked(answer)
    return jsonify({"answer": answer})


@app.route("/incidents", methods=["POST"])
def create_incident():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    pod_name = data.get("podName", "")
    symptom = data.get("symptom", "Reported from the PodSentinel frontend")
    if not pod_name:
        return jsonify({"error": "podName is required"}), 400

    incident_name = f"frontend-{pod_name}-{int(time.time())}"
    body = {
        "apiVersion": f"{INCIDENT_GROUP}/{INCIDENT_VERSION}",
        "kind": "Incident",
        "metadata": {"name": incident_name},
        "spec": {"podName": pod_name, "namespace": NAMESPACE, "symptom": symptom, "approved": False},
    }

    api = get_incident_api()
    try:
        api.create_namespaced_custom_object(INCIDENT_GROUP, INCIDENT_VERSION, NAMESPACE, INCIDENT_PLURAL, body)
    except client.exceptions.ApiException as e:
        return jsonify({"error": f"failed to create incident: {e.reason}"}), 500

    return jsonify({"incidentName": incident_name})


@app.route("/incidents/<name>", methods=["GET"])
def get_incident(name):
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    api = get_incident_api()
    try:
        obj = api.get_namespaced_custom_object(INCIDENT_GROUP, INCIDENT_VERSION, NAMESPACE, INCIDENT_PLURAL, name)
    except client.exceptions.ApiException:
        return jsonify({"error": "not found"}), 404

    status = obj.get("status", {}) or {}
    return jsonify({
        "phase": status.get("phase", "Pending"),
        "diagnosis": status.get("diagnosis", ""),
        "approved": obj.get("spec", {}).get("approved", False),
    })


@app.route("/incidents/<name>/approve", methods=["POST"])
def approve_incident(name):
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    api = get_incident_api()
    patch_body = {"spec": {"approved": True}}
    try:
        api.patch_namespaced_custom_object(INCIDENT_GROUP, INCIDENT_VERSION, NAMESPACE, INCIDENT_PLURAL, name, patch_body)
    except client.exceptions.ApiException as e:
        return jsonify({"error": f"failed to approve: {e.reason}"}), 500

    return jsonify({"status": "approved"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

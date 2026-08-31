import os
import socket
import smtplib
from email.mime.text import MIMEText
from kubernetes import client, config

_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


def send_email(subject, body):
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    to_addr = os.environ.get("ALERT_EMAIL_TO")

    if not host:
        print("SMTP not configured, skipping email")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to_addr

    socket.getaddrinfo = _ipv4_only_getaddrinfo
    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, [to_addr], msg.as_string())
    finally:
        socket.getaddrinfo = _orig_getaddrinfo


def main():
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace="default")

    total = len(pods.items)
    unhealthy = []
    for pod in pods.items:
        for cs in (pod.status.container_statuses or []):
            if cs.restart_count > 0:
                unhealthy.append(f"{pod.metadata.name} (restarts: {cs.restart_count})")
                break

    body = f"Weekly Cluster Liveness Report\n\nTotal pods: {total}\nPods with restarts: {len(unhealthy)}\n\n"
    if unhealthy:
        body += "Details:\n" + "\n".join(unhealthy)
    else:
        body += "All pods healthy, no restarts detected this check."

    send_email("Weekly Cluster Liveness Report", body)
    print("Summary email sent.")


if __name__ == "__main__":
    main()

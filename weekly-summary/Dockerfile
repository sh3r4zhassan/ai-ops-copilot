FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir kubernetes
COPY weekly_summary.py .
CMD ["python", "-u", "weekly_summary.py"]

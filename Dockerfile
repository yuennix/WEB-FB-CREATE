FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn gevent
COPY . .
EXPOSE 80
CMD ["python3", "-m", "gunicorn", "--bind", "0.0.0.0:80", "--worker-class", "gevent", "--workers", "1", "--worker-connections", "2000", "--timeout", "300", "app:app"]

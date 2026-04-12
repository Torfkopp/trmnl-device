FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/docker-entrypoint.sh /app/script.sh /app/data/simple-cors-http-server.py || true

CMD ["/app/docker-entrypoint.sh"]

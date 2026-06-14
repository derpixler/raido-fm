FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY web/ ./web/
COPY prompts/ ./prompts/

RUN useradd --create-home --uid 1000 raido && chown -R raido:raido /app
USER raido

ENV HUB_PORT=80
EXPOSE ${HUB_PORT}

CMD uvicorn app.main:app --host 0.0.0.0 --port ${HUB_PORT}

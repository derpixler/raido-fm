FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY web/ ./web/
COPY persona*.yml ./

RUN useradd --create-home --uid 1000 raido && chown -R raido:raido /app
USER raido

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE ${PORT}

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}

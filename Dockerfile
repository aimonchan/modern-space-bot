FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary sqlalchemy langgraph langchain-core

COPY . /app
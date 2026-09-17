FROM python:3.11-slim

WORKDIR /app

# လိုအပ်သော Python packages အားလုံးကို တစ်ခါတည်း install လုပ်ခြင်း
RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary sqlalchemy langgraph langchain-core langchain-openai langchain-google-genai

COPY . /app
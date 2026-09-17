from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

# LLM Providers import
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

app = FastAPI(title="Modern Space API")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:secretpassword@db:5432/modern_space")
engine = create_engine(DATABASE_URL)

# --- LLM Dynamic Provider Setup ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
MODEL_NAME = os.getenv("MODEL_NAME", "llama3-70b-8192")

if LLM_PROVIDER == "groq":
    # Groq uses OpenAI-compatible API endpoints
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.7,
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
elif LLM_PROVIDER == "gemini":
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0.7,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
else:
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

# 1. Define Webhook Payload Structure
class WebhookPayload(BaseModel):
    sender_id: str
    message: str

# 2. Define LangGraph State (Supporting full message history)
class AgentState(TypedDict):
    messages: list
    response: str

# 3. Define AI Agent Node using the Dynamic LLM
def agent_node(state: AgentState):
    # LangGraph state ထဲက messages တွေကို LangChain messages format သို့ ဘာသာပြန်ခြင်း
    response = llm.invoke(state["messages"])
    
    # ဖြေကြားချက်ကို state သို့ ထည့်သွင်းခြင်း
    return {
        "messages": state["messages"] + [AIMessage(content=response.content)],
        "response": response.content
    }

# 4. Build LangGraph Workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)
agent_app = workflow.compile()


@app.get("/")
def read_root():
    return {
        "status": "ok", 
        "message": f"Modern Space Backend is running with provider: {LLM_PROVIDER.upper()}"
    }

@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            db_version = result.fetchone()[0]
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            connection.commit()
        return {
            "status": "success", 
            "message": "Database connected successfully with pgvector!",
            "database_version": db_version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_with_agent(message: str):
    try:
        initial_state = {
            "messages": [HumanMessage(content=message)], 
            "response": ""
        }
        result = agent_app.invoke(initial_state)
        return {"status": "success", "response": result["response"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
def handle_webhook(payload: WebhookPayload):
    try:
        initial_state = {
            "messages": [HumanMessage(content=payload.message)], 
            "response": ""
        }
        result = agent_app.invoke(initial_state)
        
        return {
            "status": "success",
            "sender_id": payload.sender_id,
            "agent_response": result["response"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
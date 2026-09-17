from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import os
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 1. Initialize FastAPI app FIRST
app = FastAPI(title="Modern Space API")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:secretpassword@db:5432/modern_space")
engine = create_engine(DATABASE_URL)

# 2. Define Webhook Payload Structure
class WebhookPayload(BaseModel):
    sender_id: str
    message: str

# 3. Define LangGraph State
class AgentState(TypedDict):
    messages: list[str]
    response: str

# 4. Define Node Logic (AI Agent Node)
def agent_node(state: AgentState):
    latest_message = state["messages"][-1] if state["messages"] else ""
    reply = f"Modern Space Agent received: '{latest_message}'. Processing your request..."
    return {"response": reply}

# 5. Build LangGraph Workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)
agent_app = workflow.compile()


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Modern Space Backend with LangGraph is running smoothly!"}

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

# 6. Test Agent Endpoint
@app.post("/chat")
def chat_with_agent(message: str):
    try:
        initial_state = {"messages": [message], "response": ""}
        result = agent_app.invoke(initial_state)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. Add Webhook Handshake Endpoint
@app.post("/webhook")
def handle_webhook(payload: WebhookPayload):
    try:
        initial_state = {"messages": [payload.message], "response": ""}
        result = agent_app.invoke(initial_state)
        
        return {
            "status": "success",
            "sender_id": payload.sender_id,
            "agent_response": result["response"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
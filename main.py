from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import os

app = FastAPI(title="Modern Space API")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:secretpassword@db:5432/modern_space")
engine = create_engine(DATABASE_URL)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Modern Space Backend is running smoothly!"}

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
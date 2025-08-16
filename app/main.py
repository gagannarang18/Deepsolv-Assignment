from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import os

from app.routers import insights

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Shopify Insights Fetcher",
    description="Extract comprehensive insights from Shopify stores",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(insights.router)

@app.get("/")
async def root():
    return {
        "message": "Shopify Insights Fetcher API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/status")
async def status():
    return {
        "status": "running",
        "groq_configured": bool(os.getenv("GROQ_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

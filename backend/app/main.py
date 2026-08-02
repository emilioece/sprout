from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import os

from dotenv import load_dotenv

from app.database import engine, Base
from app import models 
# update to include mobile
from app.routers import plants, users, ai, mobile

# Load environment variables (GEMINI_API_KEY, etc.)
load_dotenv()

# Create tables if they don't exist 
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Sprout API",
    description="Plant care management backend",
    version="0.1.0",
)

app.add_middleware(
        CORSMiddleware,
        # Allow requests from local frontend 
        allow_origins=["http://localhost:3000"],

        # Allow cookies and auth information
        allow_credentials = True,

        # Allow all HTTP methods
        allow_methods=["*"],

        # Allow all request headers
        allow_headers=["*"],
        )

# Serve uploaded plant photos back out at /uploads/<filename>
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
def root():
    return {"message": "Sprout API running"}

# Mount plant routes under /plants
app.include_router(plants.router)

app.include_router(users.router)

app.include_router(ai.router)

# Phone photo upload over the local network (QR code flow)
app.include_router(mobile.router)
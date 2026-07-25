from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app import models 
from app.routers import plants

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

@app.get("/")
def root():
    return {"message": "Sprout API running"}

# Mount plant routes under /plants
app.include_router(plants.router)

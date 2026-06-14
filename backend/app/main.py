from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import models
from app.db.database import engine
from app.api import auth, predict

# Create the database tables natively on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fake News Detection System API", version="1.0.0")

# Setup CORS to allow React Frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://tru-sight-ai.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(predict.router, prefix="/api/ml", tags=["Machine Learning"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Fake News Detection API system!"}

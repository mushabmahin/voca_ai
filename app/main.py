from fastapi import FastAPI
from app.routes.analyze import router as analyze_router

app = FastAPI(
    title="VOCA AI",
    version="1.0.0"
)

app.include_router(analyze_router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "API is running"}
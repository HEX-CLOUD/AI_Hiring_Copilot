from fastapi import FastAPI

app = FastAPI(
    title="AI Hiring Copilot",
    version="1.0.0"
)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Hiring Copilot"
    }
from fastapi import FastAPI
from schemas.request_models import CallInfo
from services.alerts import analyze_call

app = FastAPI(title="SecureCallX Backend API")

@app.get("/")
def root():
    return {"message": "SecureCallX API running"}

@app.post("/analyze-call")
def analyze(call_info: CallInfo):
    result = analyze_call(call_info)
    return result

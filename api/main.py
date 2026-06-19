from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from firewall import Firewall
import ollama

app = FastAPI(title="LLM Firewall API")

class ChatRequest(BaseModel):
    prompt: str
    system_prompt: str = "You are a helpful AI assistant."

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Initializing firewall...")
firewall = Firewall(
    system_prompt="You are a helpful AI assistant.",
    model_path=os.path.join(os.path.dirname(__file__), "../src/classifier-model")
)
print("Firewall ready.")

class ScanRequest(BaseModel):
    prompt: str

class ScanResponse(BaseModel):
    blocked: bool
    layer: str
    reason: str
    confidence: float | None

@app.get("/")
def root():
    return {"status": "LLM Firewall API is running"}

@app.post("/scan")
def scan(request: ScanRequest):
    result = firewall.scan_input(request.prompt)
    return {
        "blocked": result["blocked"],
        "layer": result["layer"],
        "reason": result["reason"],
        "confidence": result.get("confidence")
    }

@app.post("/chat")
def chat(request: ChatRequest):
    # scan input first
    scan_result = firewall.scan_input(request.prompt)
    
    if scan_result["blocked"]:
        return {
            "blocked": True,
            "layer": scan_result["layer"],
            "reason": scan_result["reason"],
            "confidence": scan_result.get("confidence"),
            "response": None
        }
    
    # passed — send to Llama3
    try:
        result = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.prompt}
            ]
        )
        response_text = result["message"]["content"]
        
        # scan output too
        output_result = firewall.scan_output(response_text)
        if output_result["blocked"]:
            return {
                "blocked": True,
                "layer": "output_filter",
                "reason": output_result["reason"],
                "confidence": output_result.get("confidence"),
                "response": None
            }
        
        return {
            "blocked": False,
            "layer": "all_passed",
            "reason": "passed all firewall layers",
            "confidence": scan_result.get("confidence"),
            "response": response_text
        }
    except Exception as e:
        return {
            "blocked": False,
            "layer": "all_passed",
            "reason": "passed firewall",
            "confidence": None,
            "response": f"Error reaching Ollama: {str(e)}"
        }
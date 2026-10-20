
import os

import uvicorn
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI, APIConnectionError, APIStatusError
from pydantic import BaseModel, Field


# --------------------------------------------------
# Configuration
# --------------------------------------------------

KAGGLE_PROXY = os.environ.get("KAGGLE_PROXY", "").rstrip("/")

if not KAGGLE_PROXY:
    raise RuntimeError(
        "KAGGLE_PROXY is not set. Configure it in your WSL terminal."
    )

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

client = AsyncOpenAI(
    base_url=f"{KAGGLE_PROXY}/proxy/8000/v1",
    api_key="EMPTY",
    timeout=120.0,
    max_retries=1,
)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="LLM Chat API",
    description="FastAPI client connected to vLLM on Kaggle",
    version="1.0.0",
)


# --------------------------------------------------
# Request and response schemas
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's message", )
    max_tokens: int = Field(default=256, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    model: str
    response: str


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "FastAPI is connected as a vLLM client",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "running",
        "service": "FastAPI",
        "model": MODEL_NAME,
        "vllm_proxy_configured": bool(KAGGLE_PROXY),
    }


@app.get("/models")
async def list_models():
    """Check connectivity and retrieve models served by vLLM."""
    try:
        models = await client.models.list()
        return {
            "status": "connected",
            "models": [model.id for model in models.data],
        }

    except APIConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Cannot connect to vLLM through the Kaggle proxy.",
        )

    except APIStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"vLLM returned HTTP {exc.status_code}.",
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the model served by vLLM."""
    try:
        result = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": request.message,
                }
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        answer = result.choices[0].message.content or ""

        return ChatResponse(
            model=MODEL_NAME,
            response=answer,
        )

    except APIConnectionError:
        raise HTTPException(
            status_code=502,
            detail=(
                "Cannot connect to vLLM through the Kaggle proxy. "
                "Check that the Kaggle session is active and the proxy URL "
                "is valid."
            ),
        )

    except APIStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"vLLM returned HTTP {exc.status_code}.",
        )


# --------------------------------------------------
# Run server
# --------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3002,
    )

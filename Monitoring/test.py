
import os
import secrets
import logging
from pathlib import Path

import requests
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials


# --------------------------------------------------
# 1. Logging configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("metrics_gateway")


# --------------------------------------------------
# 2. Load environment variables
# --------------------------------------------------

ENV_PATH = Path(__file__).with_name(".env")

load_dotenv(ENV_PATH, override=True)

KAGGLE_PROXY = os.getenv("KAGGLE_PROXY", "").strip().rstrip("/")

MONITOR_USER = os.getenv("MONITOR_USER")
MONITOR_PASSWORD = os.getenv("MONITOR_PASSWORD")

if not KAGGLE_PROXY:
    raise RuntimeError("KAGGLE_PROXY is not configured")

if not MONITOR_USER or not MONITOR_PASSWORD:
    raise RuntimeError("Monitoring credentials are missing")


# --------------------------------------------------
# 3. Construct vLLM metrics URL
# --------------------------------------------------

# KAGGLE_PROXY already ends with /proxy.
# Do not append another /proxy.

VLLM_METRICS_URL = f"{KAGGLE_PROXY}/proxy/8000/metrics"


# --------------------------------------------------
# 4. HTTP Basic Authentication
# --------------------------------------------------

security = HTTPBasic()


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security)
):
    username_valid = secrets.compare_digest(
        credentials.username,
        MONITOR_USER
    )

    password_valid = secrets.compare_digest(
        credentials.password,
        MONITOR_PASSWORD
    )

    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=401,
            detail="Invalid monitoring credentials",
            headers={"WWW-Authenticate": "Basic"}
        )

    return credentials.username


# --------------------------------------------------
# 5. FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="vLLM Metrics Gateway",
    description="Secure gateway for collecting vLLM Prometheus metrics",
    version="1.0.0"
)


# --------------------------------------------------
# 6. HTTP session
# --------------------------------------------------

session = requests.Session()


# --------------------------------------------------
# 7. Root endpoint
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "vLLM Metrics Gateway",
        "metrics_endpoint": "/metrics"
    }


# --------------------------------------------------
# 8. Health endpoint
# --------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "metrics_gateway"
    }


# --------------------------------------------------
# 9. Metrics endpoint
# --------------------------------------------------

@app.get("/metrics")
def metrics(
    username: str = Depends(verify_credentials)
):

    try:

        response = session.get(
            VLLM_METRICS_URL,
            timeout=30
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "text/plain; version=0.0.4; charset=utf-8"
        )

        logger.info("Successfully fetched vLLM metrics")

        return Response(
            content=response.content,
            status_code=200,
            headers={
                "Content-Type": content_type
            }
        )

    except requests.exceptions.Timeout:

        logger.error("Timeout while fetching vLLM metrics")

        raise HTTPException(
            status_code=504,
            detail="Timeout while connecting to vLLM"
        )

    except requests.exceptions.HTTPError as exc:

        status_code = exc.response.status_code

        logger.error(
            "vLLM metrics endpoint returned HTTP %s",
            status_code
        )

        raise HTTPException(
            status_code=502,
            detail=f"Upstream vLLM returned HTTP {status_code}"
        )

    except requests.exceptions.RequestException:

        logger.exception("Unable to connect to vLLM metrics endpoint")

        raise HTTPException(
            status_code=502,
            detail="Unable to connect to vLLM"
        )


# --------------------------------------------------
# 10. Start server
# --------------------------------------------------

if __name__ == "__main__":

    logger.info("Starting vLLM Metrics Gateway")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9100
    )

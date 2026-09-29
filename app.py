"""HTTP API around scrape.py, for hosting.

    POST /scrape   {"url": "https://...", "prompt": "What to extract"}
    Header         Authorization: Bearer <API_TOKEN>

Run locally:  uvicorn app:app --port 8000
"""

import os
import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, HttpUrl
from scrapegraphai.graphs import SmartScraperGraph

from scrape import llm_config

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    # A public URL spending your LLM credits must not be left open.
    raise SystemExit("API_TOKEN is not set. Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'")

LLM = llm_config()  # fails fast if the provider key is missing

app = FastAPI(title="scrapergraph-api")
bearer = HTTPBearer(auto_error=False)


def require_token(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
    if creds is None or not secrets.compare_digest(creds.credentials, API_TOKEN):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")


class ScrapeRequest(BaseModel):
    url: HttpUrl
    prompt: str = Field(min_length=1, max_length=2000)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "model": LLM["model"]}


# Plain `def` so FastAPI runs it in a worker thread: graph.run() blocks and
# starts its own event loop for Playwright.
@app.post("/scrape", dependencies=[Depends(require_token)])
def scrape(req: ScrapeRequest) -> dict:
    graph = SmartScraperGraph(
        prompt=req.prompt,
        source=str(req.url),
        config={"llm": dict(LLM), "headless": True},
    )
    try:
        return {"result": graph.run()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Scrape failed: {exc}") from exc

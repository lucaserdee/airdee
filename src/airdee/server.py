import os
import uuid
import time
import traceback
import requests
import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from .weaviate_retriever import WeaviateRetriever

# Load environment variables
load_dotenv()

# Create Weaviate client once at startup
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WEAVIATE_URL", ""),
    auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY", "")),
)

retriever = WeaviateRetriever(client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown of the app."""
    yield
    # shutdown: close Weaviate client cleanly
    try:
        client.close()
    except Exception:
        pass


app = FastAPI(title="EMG Weaviate Tool", lifespan=lifespan)


# ----- Models -----
class SearchBody(BaseModel):
    class_: str = Field(default=os.getenv("WEAVIATE_DEFAULT_CLASS", "Article"), alias="class")
    fulltext: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[List[Any]] = None
    limit: int = 5
    select: Optional[List[str]] = None


# ----- Endpoints -----
@app.post("/tool/weaviate.search")
def weaviate_search(body: SearchBody):
    try:
        items = retriever.search(
            class_name=body.class_,
            fulltext=body.fulltext,
            filters=body.filters,
            sort=body.sort,
            limit=body.limit,
            select=body.select,
        )
        return {"items": items}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Search failed: {type(e).__name__}: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "weaviate_ready": client.is_ready()}


@app.get("/debug/auth")
def debug_auth():
    return {
        "url": os.getenv("WEAVIATE_URL", "").rstrip("/") + "/v1/graphql",
        "auth_type": "API-KEY" if os.getenv("WEAVIATE_API_KEY") else "None",
    }


@app.get("/debug/graphql")
def debug_graphql():
    url = os.getenv("WEAVIATE_URL", "").rstrip("/") + "/v1/graphql"
    hdrs = {"X-API-KEY": os.getenv("WEAVIATE_API_KEY", "")}
    q = {"query": "{ Get { Article(limit:1) { rdId } } }"}
    r = requests.post(url, headers=hdrs, json=q, timeout=15)
    return {
        "url": url,
        "sent_auth": "API-KEY",
        "status": r.status_code,
        "ok": r.ok,
        "reason": r.reason,
        "body": r.text[:300],
    }


# ----- Logging middleware -----
@app.middleware("http")
async def log_requests(request: Request, call_next):
    tid = str(uuid.uuid4())[:8]
    body = (await request.body()).decode("utf-8", "ignore")
    print(f"[{tid}] --> {request.method} {request.url.path} body={body[:400]}")
    t0 = time.time()
    resp = await call_next(request)
    print(f"[{tid}] <-- {resp.status_code} {request.url.path} in {int((time.time()-t0)*1000)}ms")
    return resp

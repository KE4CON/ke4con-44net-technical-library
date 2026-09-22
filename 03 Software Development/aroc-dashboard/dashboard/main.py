# AROC Dashboard — FastAPI application.  GPLv3, see dashboard/__init__.py.
"""Serve the dashboard page and a JSON status feed.

Each collector is polled on its own interval by a background task; the browser
only ever talks to this server (``/api/status``), so device credentials never
leave the host and the browser needs no direct route to any management VLAN.

Run::

    AROC_CONFIG=config.yaml uvicorn dashboard.main:app --host 100.x.y.z --port 8080
"""
from __future__ import annotations

import asyncio
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from . import __version__
from .collectors import Collector, available_types, create_collector
from .config import load_config

log = logging.getLogger("aroc.dashboard")
STATIC = Path(__file__).parent / "static"


class State:
    def __init__(self) -> None:
        self.cfg: dict[str, Any] = {}
        self.collectors: dict[str, Collector] = {}
        self.tasks: list[asyncio.Task[None]] = []
        self.started = time.time()


state = State()
_basic = HTTPBasic(auto_error=False)


async def _poll_loop(col: Collector) -> None:
    while True:
        t0 = time.monotonic()
        await col.refresh()
        await asyncio.sleep(max(1.0, col.interval - (time.monotonic() - t0)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg_path = os.environ.get("AROC_CONFIG", "config.yaml")
    state.cfg = load_config(cfg_path)
    points = int(state.cfg["dashboard"]["history_points"])
    for svc in state.cfg["services"]:
        if not svc.get("enabled", True):
            continue
        col = create_collector(svc, points)
        state.collectors[col.id] = col
        state.tasks.append(asyncio.create_task(_poll_loop(col), name=f"poll:{col.id}"))
    log.info("dashboard %s: %d services loaded from %s", __version__, len(state.collectors), cfg_path)
    try:
        yield
    finally:
        for t in state.tasks:
            t.cancel()
        await asyncio.gather(*state.tasks, return_exceptions=True)
        await asyncio.gather(*(c.close() for c in state.collectors.values()), return_exceptions=True)


app = FastAPI(title="AROC Dashboard", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None)


def require_auth(creds: HTTPBasicCredentials | None = Depends(_basic)) -> None:
    """Optional HTTP basic auth for the whole dashboard (``dashboard.auth`` in config)."""
    auth = state.cfg.get("dashboard", {}).get("auth")
    if not auth:
        return
    ok = (creds is not None
          and secrets.compare_digest(creds.username.encode(), str(auth.get("username", "")).encode())
          and secrets.compare_digest(creds.password.encode(), str(auth.get("password", "")).encode()))
    if not ok:
        raise HTTPException(status_code=401, detail="Unauthorized",
                            headers={"WWW-Authenticate": 'Basic realm="AROC Dashboard"'})


@app.get("/", dependencies=[Depends(require_auth)])
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/status", dependencies=[Depends(require_auth)])
async def api_status() -> JSONResponse:
    d = state.cfg["dashboard"]
    return JSONResponse({
        "title": d["title"],
        "subtitle": d.get("subtitle", ""),
        "refresh_seconds": d["refresh_seconds"],
        "server_time": time.time(),
        "uptime": time.time() - state.started,
        "version": __version__,
        "services": [dict(c.card.to_dict(), interval=c.interval) for c in state.collectors.values()],
    })


@app.get("/api/services/{service_id}", dependencies=[Depends(require_auth)])
async def api_service(service_id: str) -> JSONResponse:
    col = state.collectors.get(service_id)
    if col is None:
        raise HTTPException(404, f"no such service: {service_id}")
    return JSONResponse(col.card.to_dict())


@app.post("/api/services/{service_id}/refresh", dependencies=[Depends(require_auth)])
async def api_refresh(service_id: str) -> JSONResponse:
    col = state.collectors.get(service_id)
    if col is None:
        raise HTTPException(404, f"no such service: {service_id}")
    return JSONResponse((await col.refresh()).to_dict())


@app.get("/api/types")
async def api_types() -> dict[str, Any]:
    return {"types": available_types()}


@app.get("/healthz")
async def healthz(request: Request) -> dict[str, Any]:
    return {"ok": True, "services": len(state.collectors)}


app.mount("/static", StaticFiles(directory=STATIC), name="static")


def main() -> None:  # console entry point
    import uvicorn

    logging.basicConfig(level=os.environ.get("AROC_LOG", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run("dashboard.main:app", host=os.environ.get("AROC_HOST", "127.0.0.1"),
                port=int(os.environ.get("AROC_PORT", "8080")), log_level="info")


if __name__ == "__main__":
    main()

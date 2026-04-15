from contextlib import asynccontextmanager

from db import init_db
from feeds import ensure_feed_cache, get_cached_feed_items
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_feed_cache(max_age_minutes=30)
    yield

app = FastAPI(title="RSS Platform", version="0.1.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), autoplay=(), camera=(), geolocation=(), "
        "gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
    )
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return response



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    ensure_feed_cache(max_age_minutes=30)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "page_title": "RSS Platform",
            "feed_items": get_cached_feed_items(limit=3),
        },
    )


@app.get("/resume", response_class=HTMLResponse)
async def resume_page(request: Request):
    return templates.TemplateResponse(
        "resume.html",
        {
            "request": request,
            "page_title": "Resume",
        },
    )


@app.get("/feeds", response_class=HTMLResponse)
async def feeds_page(request: Request):
    ensure_feed_cache(max_age_minutes=30)
    return templates.TemplateResponse(
        "feeds.html",
        {
            "request": request,
            "page_title": "Feeds",
            "feed_items": get_cached_feed_items(limit=12),
        },
    )


@app.get("/healthz")
async def healthcheck():
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(url="/static/favicon.ico", status_code=307)
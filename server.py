#!/usr/bin/env python3
"""
Consent-based single-link demo (educational only).

Routes:
- GET  /l/{token}            -> landing page (consent prompt)
- POST /l/{token}/accept     -> called after explicit consent; logs IP + optional browser geolocation
- GET  /events?limit=50      -> JSON list of recent events (admin/demo view)
"""
import time
import sqlite3
from typing import Optional
import httpx

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_PATH = "consent_events.db"
GEO_API = "http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon"

app = FastAPI(title="Consent-based Single Link Demo")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT,
        ip TEXT,
        ts REAL,
        ua TEXT,
        referer TEXT,
        browser_lat REAL,
        browser_lon REAL,
        country TEXT,
        city TEXT,
        ip_lat REAL,
        ip_lon REAL
    )
    """)
    conn.commit()
    conn.close()

def save_event(ev):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO events (token, ip, ts, ua, referer, browser_lat, browser_lon, country, city, ip_lat, ip_lon)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ev.get("token"), ev.get("ip"), ev.get("ts"), ev.get("ua"), ev.get("referer"),
        ev.get("browser_lat"), ev.get("browser_lon"),
        ev.get("country"), ev.get("city"),
        ev.get("ip_lat"), ev.get("ip_lon"),
    ))
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

async def geolocate_ip(ip: str):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(GEO_API.format(ip=ip))
            data = r.json()
            if data.get("status") == "success":
                return {"country": data.get("country"), "city": data.get("city"),
                        "ip_lat": data.get("lat"), "ip_lon": data.get("lon")}
    except Exception:
        pass
    return {}

class AcceptPayload(BaseModel):
    browserGeo: Optional[dict] = None
    extraNote: Optional[str] = None

@app.get("/l/{token}")
def landing(request: Request, token: str):
    """
    Render a consent landing page; token is shown to the visitor.
    """
    return templates.TemplateResponse("consent.html", {"request": request, "token": token})

@app.post("/l/{token}/accept")
async def accept(request: Request, token: str, payload: AcceptPayload = Body(...)):
    """
    Called by the landing page after the visitor gives consent and (optionally) the browser returns geolocation.
    Logs the visitor IP and any provided browser geolocation.
    """
    client_ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    referer = request.headers.get("referer")
    ts = time.time()

    ip_geo = await geolocate_ip(client_ip) if client_ip else {}

    ev = {
        "token": token,
        "ip": client_ip,
        "ts": ts,
        "ua": ua,
        "referer": referer,
        "browser_lat": payload.browserGeo.get("lat") if payload.browserGeo else None,
        "browser_lon": payload.browserGeo.get("lon") if payload.browserGeo else None,
        "country": ip_geo.get("country"),
        "city": ip_geo.get("city"),
        "ip_lat": ip_geo.get("ip_lat"),
        "ip_lon": ip_geo.get("ip_lon"),
    }
    save_event(ev)
    return JSONResponse({"ok": True, "logged": True, "ip": client_ip, "browserGeo": payload.browserGeo})

@app.get("/events")
def events(limit: int = 50):
    """
    Demo listing of recent events (protect in real deployments).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, token, ip, ts, ua, referer, browser_lat, browser_lon, country, city, ip_lat, ip_lon "
                "FROM events ORDER BY ts DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "token": r[1],
            "ip": r[2],
            "ts": r[3],
            "ua": r[4],
            "referer": r[5],
            "browser_lat": r[6],
            "browser_lon": r[7],
            "country": r[8],
            "city": r[9],
            "ip_lat": r[10],
            "ip_lon": r[11],
        })
    return JSONResponse({"count": len(results), "events": results})

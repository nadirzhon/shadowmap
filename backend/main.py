#!/usr/bin/env python3
"""
SHADOWMAP Backend — Real-time cyberattack broadcast server
Author: nadirzhon | github.com/nadirzhon/shadowmap
"""

import asyncio
import json
import os
import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="SHADOWMAP", version="1.0.0")

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH       = os.getenv("DB_PATH", "honeypot.db")
DEMO_MODE     = os.getenv("DEMO_MODE", "auto")
DEMO_INTERVAL = float(os.getenv("DEMO_INTERVAL", "0.8"))
GEOIP_ENABLED = os.getenv("GEOIP_ENABLED", "true").lower() == "true"

# ── State ─────────────────────────────────────────────────────────────────────
connected: list[WebSocket] = []
stats = {
    "total": 0,
    "by_country": {},
    "by_type": {},
    "start_time": datetime.utcnow().isoformat(),
}

# ── Demo data ─────────────────────────────────────────────────────────────────
CITIES = [
    {"city":"Moscow",    "country":"Russia",      "cc":"RU","lat":55.75,"lon":37.62},
    {"city":"Beijing",   "country":"China",       "cc":"CN","lat":39.91,"lon":116.39},
    {"city":"Seoul",     "country":"South Korea", "cc":"KR","lat":37.57,"lon":126.98},
    {"city":"Tehran",    "country":"Iran",        "cc":"IR","lat":35.70,"lon":51.42},
    {"city":"Bucharest", "country":"Romania",     "cc":"RO","lat":44.43,"lon":26.10},
    {"city":"Mumbai",    "country":"India",       "cc":"IN","lat":19.08,"lon":72.88},
    {"city":"São Paulo", "country":"Brazil",      "cc":"BR","lat":-23.55,"lon":-46.63},
    {"city":"Lagos",     "country":"Nigeria",     "cc":"NG","lat":6.52,"lon":3.38},
    {"city":"Kyiv",      "country":"Ukraine",     "cc":"UA","lat":50.45,"lon":30.52},
    {"city":"Jakarta",   "country":"Indonesia",   "cc":"ID","lat":-6.21,"lon":106.85},
    {"city":"Amsterdam", "country":"Netherlands", "cc":"NL","lat":52.37,"lon":4.90},
    {"city":"Hong Kong", "country":"Hong Kong",   "cc":"HK","lat":22.32,"lon":114.17},
]
TARGETS = [
    {"city":"New York",     "country":"USA",         "cc":"US","lat":40.71,"lon":-74.01},
    {"city":"London",       "country":"UK",          "cc":"GB","lat":51.51,"lon":-0.13},
    {"city":"Tokyo",        "country":"Japan",       "cc":"JP","lat":35.68,"lon":139.69},
    {"city":"Frankfurt",    "country":"Germany",     "cc":"DE","lat":50.11,"lon":8.68},
    {"city":"Singapore",    "country":"Singapore",   "cc":"SG","lat":1.36,"lon":103.82},
    {"city":"Paris",        "country":"France",      "cc":"FR","lat":48.86,"lon":2.35},
    {"city":"Sydney",       "country":"Australia",   "cc":"AU","lat":-33.87,"lon":151.21},
    {"city":"San Francisco","country":"USA",         "cc":"US","lat":37.77,"lon":-122.42},
    {"city":"Toronto",      "country":"Canada",      "cc":"CA","lat":43.70,"lon":-79.42},
    {"city":"Dubai",        "country":"UAE",         "cc":"AE","lat":25.20,"lon":55.27},
]
ATTACK_TYPES = [
    {"type":"SSH Brute Force","port":22},
    {"type":"RDP Attack",     "port":3389},
    {"type":"Web Shell",      "port":80},
    {"type":"Port Scan",      "port":0},
    {"type":"SQL Injection",  "port":3306},
]
USERNAMES = ["root","admin","ubuntu","pi","test","oracle","postgres","deploy","git","www-data",
             "support","ec2-user","centos","vagrant","ansible","mysql","redis","user","guest"]
PASSWORDS = ["123456","password","admin","root","1234","qwerty","test","12345678","pass",
             "letmein","welcome","monkey","1q2w3e4r","abc123","iloveyou","passw0rd","admin123"]

def gen_demo_event():
    src = random.choice(CITIES)
    dst = random.choice(TARGETS)
    atk = random.choice(ATTACK_TYPES)
    ip  = ".".join(str(random.randint(1,254)) for _ in range(4))
    port = atk["port"] if atk["port"] else random.randint(1,65535)
    return {
        "id":        int(time.time() * 1000),
        "timestamp": datetime.utcnow().isoformat(),
        "src_ip":    ip,
        "src_city":  src["city"],
        "src_country": src["country"],
        "src_cc":    src["cc"],
        "src_lat":   src["lat"],
        "src_lon":   src["lon"],
        "dst_city":  dst["city"],
        "dst_country": dst["country"],
        "dst_cc":    dst["cc"],
        "dst_lat":   dst["lat"],
        "dst_lon":   dst["lon"],
        "port":      port,
        "attack_type": atk["type"],
        "username":  random.choice(USERNAMES),
        "password":  random.choice(PASSWORDS),
    }

# ── GeoIP ─────────────────────────────────────────────────────────────────────
_geo_cache: dict = {}

def geoip(ip: str) -> dict:
    if ip in _geo_cache:
        return _geo_cache[ip]
    if not GEOIP_ENABLED:
        return {}
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        data = r.json()
        result = {
            "city":    data.get("city", "Unknown"),
            "country": data.get("country_name", "Unknown"),
            "cc":      data.get("country_code", "??"),
            "lat":     data.get("latitude", 0),
            "lon":     data.get("longitude", 0),
            "asn":     data.get("asn", ""),
            "org":     data.get("org", ""),
        }
        _geo_cache[ip] = result
        return result
    except Exception:
        return {}

# ── Honeypot DB reader ─────────────────────────────────────────────────────────
_last_db_ts: str = ""

def read_honeypot_events():
    global _last_db_ts
    if not Path(DB_PATH).exists():
        return []
    events = []
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT ts, ip, username, password, country, city, asn FROM attempts "
            "WHERE ts > ? ORDER BY ts DESC LIMIT 10",
            (_last_db_ts,)
        ).fetchall()
        if rows:
            _last_db_ts = rows[0][0]
        for row in rows:
            ts, ip, user, pwd, country, city, asn = row
            geo = {"lat": 0, "lon": 0, "cc": "??", **geoip(ip)}
            dst = random.choice(TARGETS)
            events.append({
                "id":          int(time.time()*1000),
                "timestamp":   ts,
                "src_ip":      ip,
                "src_city":    city or "Unknown",
                "src_country": country or "Unknown",
                "src_cc":      geo.get("cc","??"),
                "src_lat":     geo.get("lat", 0),
                "src_lon":     geo.get("lon", 0),
                "dst_city":    dst["city"],
                "dst_country": dst["country"],
                "dst_cc":      dst["cc"],
                "dst_lat":     dst["lat"],
                "dst_lon":     dst["lon"],
                "port":        22,
                "attack_type": "SSH Brute Force",
                "username":    user,
                "password":    pwd,
            })
        conn.close()
    except Exception as e:
        print(f"[DB] Error: {e}")
    return events

# ── Broadcast ─────────────────────────────────────────────────────────────────
async def broadcast(event: dict):
    global stats
    stats["total"] += 1
    cc = event.get("src_cc","??")
    at = event.get("attack_type","Unknown")
    stats["by_country"][cc] = stats["by_country"].get(cc, 0) + 1
    stats["by_type"][at]    = stats["by_type"].get(at, 0) + 1

    dead = []
    for ws in connected:
        try:
            await ws.send_text(json.dumps(event))
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in connected:
            connected.remove(ws)

# ── Background task ────────────────────────────────────────────────────────────
use_demo = DEMO_MODE == "true" or (DEMO_MODE == "auto" and not Path(DB_PATH).exists())

async def attack_loop():
    print(f"[SHADOWMAP] Mode: {'DEMO' if use_demo else 'LIVE (honeypot.db)'}")
    while True:
        if use_demo:
            event = gen_demo_event()
            await broadcast(event)
            jitter = DEMO_INTERVAL * (0.5 + random.random())
            await asyncio.sleep(jitter)
        else:
            events = read_honeypot_events()
            for event in events:
                await broadcast(event)
                await asyncio.sleep(0.1)
            await asyncio.sleep(2)

@app.on_event("startup")
async def startup():
    asyncio.create_task(attack_loop())

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    connected.append(ws)
    print(f"[WS] Client connected. Total: {len(connected)}")
    try:
        # Send current stats on connect
        await ws.send_text(json.dumps({"type": "stats", **stats}))
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        if ws in connected:
            connected.remove(ws)
        print(f"[WS] Client disconnected. Total: {len(connected)}")

@app.get("/api/stats")
async def get_stats():
    return JSONResponse({**stats, "connected_clients": len(connected)})

@app.get("/")
async def index():
    frontend = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend.exists():
        return FileResponse(frontend)
    return JSONResponse({"status": "ok", "ws": "/ws", "stats": "/api/stats"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"[SHADOWMAP] Starting on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

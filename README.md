<div align="center">

```
███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗███╗   ███╗ █████╗ ██████╗
██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║████╗ ████║██╔══██╗██╔══██╗
███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║██╔████╔██║███████║██████╔╝
╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║██║╚██╔╝██║██╔══██║██╔═══╝
███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚═╝ ██║██║  ██║██║
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝
```

**Real-time global cyberattack visualization**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![WebSocket](https://img.shields.io/badge/WebSocket-Live-00ff88?style=flat-square)](/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

*Watch the internet burn — in real time.*

</div>

---

## What is this?

SHADOWMAP ingests live data from your SSH/RDP honeypot and renders every credential attack as a glowing arc on a world map — animated, real-time, beautiful. No signup. No SaaS. Runs on your own VPS in under 60 seconds.

Ships with a **demo mode** that generates realistic attack traffic so you can deploy it anywhere, instantly, even without a honeypot.

---

## Screenshots

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ● LIVE THREAT MONITORING                          Mon Aug 04 2026 UTC   │
├──────────────────────────────────────────────────────────────────────────┤
│ SHADOWMAP    │                                                           │
│ LIVE THREAT  │    [RU] ────────────────────────────► [US]               │
│              │          ╲                                                │
│ TOTAL ATTACKS│    [CN] ──╲──────────────────────────► [JP]              │
│   18,432     │             ╲                    ╱                        │
│              │    [IR] ─────╲──────────────────► [DE]                   │
│ ▲ TOP SOURCES│               ╲                                          │
│ 🇷🇺 RU  4821 │    [NG] ──────────────────────────► [GB]                │
│ 🇨🇳 CN  3204 │                                                          │
│ 🇰🇷 KR  2109 │    city labels · graticule grid · glow effects           │
│ 🇮🇷 IR   891 │                                                          │
│ 🇷🇴 RO   744 ├──────────────────────────────────────────────────────────┤
│              │ LIVE FEED                                                  │
│ ⚡ TYPES     │ 10:42:18 SSH Brute Force  🇷🇺Moscow → 🇺🇸New York  :22   │
│ SSH BF  ████ │ 10:42:19 RDP Attack       🇨🇳Beijing → 🇩🇪Frankfurt :3389│
│ RDP     ███  │ 10:42:20 SQL Injection    🇰🇷Seoul → 🇬🇧London     :3306 │
└──────────────┴──────────────────────────────────────────────────────────┘
```

---

## Quick Start

### One-command (Docker)
```bash
git clone https://github.com/nadirzhon/shadowmap
cd shadowmap
docker compose up -d
open http://localhost:8000
```

### Manual
```bash
git clone https://github.com/nadirzhon/shadowmap
cd shadowmap/backend
pip install -r requirements.txt
python main.py
# Open http://localhost:8000
```

---

## Features

- **Live animated arcs** — bezier curves with glowing particle at the leading edge
- **Real-time WebSocket** — sub-100ms event delivery to all connected browsers
- **Demo mode** — realistic attack simulation, zero config
- **Honeypot integration** — reads directly from `ssh-honeypot` SQLite database
- **GeoIP enrichment** — country, city, ASN for every attacker IP
- **Attack type detection** — SSH brute force, RDP, web shell, port scan, SQLi
- **Live feed** — scrolling attack log with credentials and ports
- **Statistics panel** — top attacking countries, attack type breakdown
- **Speed control** — adjust demo playback rate
- **Fully self-hosted** — your data stays on your server

---

## Architecture

```
┌───────────────────────────────────────────────────────┐
│                      Browser                          │
│   Leaflet.js map  +  Canvas arc overlay  +  WebSocket │
└──────────────────────────┬────────────────────────────┘
                           │ ws://
┌──────────────────────────▼────────────────────────────┐
│                FastAPI Backend                         │
│   /ws WebSocket broadcaster                           │
│   /api/stats  REST endpoint                           │
│   /          serves frontend                          │
└──────────────┬───────────────────────┬────────────────┘
               │                       │
    ┌──────────▼──────────┐  ┌─────────▼─────────┐
    │  honeypot.db        │  │   Demo generator   │
    │  (ssh-honeypot)     │  │   (auto fallback)  │
    └─────────────────────┘  └────────────────────┘
```

---

## Integration with ssh-honeypot

Copy your `honeypot.db` file to the `backend/` directory — SHADOWMAP will detect it automatically and stream real attack data instead of demo data.

```bash
# On the honeypot server
scp honeypot.db user@shadowmap-server:/path/to/shadowmap/backend/
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | HTTP/WS server port |
| `DB_PATH` | `honeypot.db` | Path to honeypot SQLite database |
| `DEMO_MODE` | `auto` | `true`, `false`, or `auto` (auto-detects DB) |
| `DEMO_INTERVAL` | `0.8` | Seconds between demo attacks |
| `GEOIP_ENABLED` | `true` | Enable GeoIP API lookups |

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, WebSockets |
| Frontend | Leaflet.js, Canvas API, Vanilla JS |
| Data | SQLite (honeypot.db) |
| Deploy | Docker, docker compose |
| GeoIP | ipapi.co (free tier) |

---

## Related Projects

- [ssh-honeypot](https://github.com/nadirzhon/ssh-honeypot) — The honeypot that feeds SHADOWMAP
- [log-analyzer-siem](https://github.com/nadirzhon/log-analyzer-siem) — Parse and alert on the same logs

---

## License

MIT — do what you want. Star the repo if it was useful.

---

<div align="center">
<sub>Built as part of the <a href="https://github.com/nadirzhon">nadirzhon</a> security tooling portfolio</sub>
</div>

# RAIDO Hub

Central hub for the RAIDO Station network. Manages multiple autonomous AI radio stations, enables one-click creation of new stations, and aggregates technical data.

## Quickstart

```bash
cd /Users/renereimann/ki-raido

# Create .env (LLM keys)
cp station/.env.example .env
# → Enter LLM_DJ_API_KEY

# Start everything (Hub + Default Station)
docker compose up --build

# Hub:     http://localhost
# Station: http://localhost:8080 (direct)
#          http://localhost/s/default/ (via Hub proxy)
```

## Architecture

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │ Port 80
                    ┌──────▼──────┐
                    │    Hub      │
                    │  (FastAPI)  │
                    └──┬───┬───┬─┘
                       │   │   │
           ┌────────────┘   │   └────────────┐
           ▼                ▼                 ▼
   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
   │ Station       │ │ Station       │ │ Station       │
   │ "default"     │ │ "synthwave"   │ │ "krautrock"   │
   │ :8080         │ │ :8081         │ │ :8082         │
   │ (protected)   │ │ (auto-stop)   │ │ (auto-stop)   │
   └───────────────┘ └───────────────┘ └───────────────┘
```

- Hub accessible on port 80 — only external port
- Stations run internally on ports 8080-8099
- Access via descriptive paths: `http://localhost/s/{slug}/`
- Docker socket access for container management

## Routing

| URL | Target |
|---|---|
| `http://localhost/` | Hub Landing Page |
| `http://localhost/s/{slug}/` | Station Stream UI (proxied) |
| `http://localhost/s/{slug}/stream` | Station SSE Stream (proxied) |
| `http://localhost/s/{slug}/inject` | Station Chat Input (proxied) |
| `http://localhost/s/{slug}/status` | Station Status API (proxied) |
| `http://localhost/stations` | Hub API: all stations |
| `http://localhost/generate-persona` | Hub API: generate persona |
| `http://localhost/overview` | Hub API: aggregated stats |

## Creating a Station

### Random (LLM generates everything)

```bash
# Via API
curl -X POST http://localhost/generate-persona \
  -H "Content-Type: application/json" \
  -d '{"genre_hint": "krautrock"}'

# → returns persona_yaml + tracks_json
# → then:
curl -X POST http://localhost/stations \
  -H "Content-Type: application/json" \
  -d '{"persona_yaml": "...", "tracks_json": "..."}'
```

### Custom (own YAML)

```bash
curl -X POST http://localhost/stations \
  -H "Content-Type: application/json" \
  -d '{"persona_yaml": "station:\n  id: my-station\n  ...", "station_id": "my-station"}'
```

Tracks are automatically generated via LLM when `tracks_json` is missing.

### Via UI

1. Open Hub Landing Page (`http://localhost`)
2. Click "+ New Station" card
3. "Random" → LLM generates persona + tracks → Preview → "Start"
4. "Custom" → Enter/paste YAML → "Start"

## Stopping a Station

Only possible with admin token:

```bash
curl -X DELETE http://localhost/stations/{station_id} \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Rules:**
- The last running station can never be stopped
- Stations with `raido.station.protected=true` label are protected
- Auto-Stop: Stations with no listeners are automatically stopped after 2h

## Auto-Stop

A background task checks every 5 minutes:
1. Does the station have 0 listeners?
2. Has it been idle for > 2 hours?
3. Is it NOT the last running station?
4. Is it NOT marked as `protected`?

If all conditions are met → container is stopped and removed.

## Token Explosion Preventer

Protection against overly long inputs (prompt injection, token waste):

- **Limit:** 500 characters per input (configurable via `MAX_INPUT_CHARS`)
- **Frontend:** Live character counter, red marking, alert modal on exceedance
- **Backend:** HTTP 413 response when limit is exceeded
- Applies to all `/inject` requests to every station

## Persona Generator

The LLM generates a complete station at the push of a button:

1. **Persona YAML** — Station config, DJ bio, quirks, rules
2. **Track Library** — 40 real tracks matching the genre (JSON)

Optional: Provide genre hint for directed generation.

All generated personas are archived in `hub/data/hub.db`.

## API Reference

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/` | GET | - | Landing Page |
| `/stations` | GET | - | Running stations |
| `/stations` | POST | - | Create new station |
| `/stations/{id}` | DELETE | Admin | Stop station |
| `/generate-persona` | POST | - | LLM generates persona + tracks |
| `/personas` | GET | - | Archived personas |
| `/overview` | GET | - | Aggregated tech stats |
| `/s/{slug}/{path}` | * | - | Proxy to station |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HUB_PORT` | `80` | Hub port |
| `ADMIN_TOKEN` | `raido-admin` | Token for admin actions |
| `STATION_IMAGE` | `raido-station:latest` | Docker image for new stations |
| `MAX_INPUT_CHARS` | `500` | Max. character length per input |
| `LLM_DJ_*` | - | LLM config (passed through to stations) |
| `LLM_FILTER_*` | - | Filter LLM config |
| `LLM_FALLBACK_*` | - | Fallback LLM config |
| `TIME_SCALE` | `60` | Default time scale for new stations |

## Files

```
hub/
  Dockerfile
  requirements.txt
  app/
    main.py              FastAPI (landing, stations API, proxy, persona gen)
    docker_mgr.py        Docker SDK (discover, create, stop, auto-cleanup)
    persona_generator.py LLM prompts for persona + track generation
    db.py                SQLite (persona archive, station registry)
    llm.py               Provider-agnostic LLM client
  web/
    index.html           Landing Page (Dark Theme)
  data/
    hub.db               SQLite DB (auto-generated)

docker-compose.yml       Root level: Hub + Default Station
personas/                Generated persona YAMLs + track libraries
```

## Interaction with Station

```
docker-compose.yml (root)
├── hub (Port 80)
│   ├── Docker socket → discovers running stations
│   ├── /personas volume → writes new persona files
│   └── Proxy → routes /s/{slug}/ to station ports
│
├── station-default (Port 8080, protected)
│   ├── /personas volume → reads persona YAML
│   └── Own DB in station/data/
│
└── raido-{id} (dynamically created by Hub)
    ├── Image: raido-station:latest
    ├── Port: 8081-8099 (auto-assigned)
    ├── /personas volume → reads generated YAML + tracks
    └── Own DB as Docker volume
```

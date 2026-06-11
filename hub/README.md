# RAIDO Hub

Zentraler Hub fuer das RAIDO Station-Netzwerk. Verwaltet mehrere autonome KI-Radiostationen, ermoeglicht die Erstellung neuer Stationen per Knopfdruck und aggregiert technische Daten.

## Quickstart

```bash
cd /Users/renereimann/ki-raido

# .env anlegen (LLM-Keys)
cp station/.env.example .env
# → LLM_DJ_API_KEY eintragen

# Alles starten (Hub + Default-Station)
docker compose up --build

# Hub:     http://localhost
# Station: http://localhost:8080 (direkt)
#          http://localhost/s/default/ (via Hub-Proxy)
```

## Architektur

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

- Hub erreichbar auf Port 80 — einziger externer Port
- Stations laufen intern auf Ports 8080-8099
- Zugriff via sprechende Pfade: `http://localhost/s/{slug}/`
- Docker-Socket-Zugriff fuer Container-Management

## Routing

| URL | Ziel |
|---|---|
| `http://localhost/` | Hub Landing Page |
| `http://localhost/s/{slug}/` | Station Stream-UI (proxied) |
| `http://localhost/s/{slug}/stream` | Station SSE-Stream (proxied) |
| `http://localhost/s/{slug}/inject` | Station Chat-Input (proxied) |
| `http://localhost/s/{slug}/status` | Station Status-API (proxied) |
| `http://localhost/stations` | Hub API: alle Stations |
| `http://localhost/generate-persona` | Hub API: Persona generieren |
| `http://localhost/overview` | Hub API: aggregierte Stats |

## Station erstellen

### Random (LLM generiert alles)

```bash
# Via API
curl -X POST http://localhost/generate-persona \
  -H "Content-Type: application/json" \
  -d '{"genre_hint": "krautrock"}'

# → gibt persona_yaml + tracks_json zurueck
# → dann:
curl -X POST http://localhost/stations \
  -H "Content-Type: application/json" \
  -d '{"persona_yaml": "...", "tracks_json": "..."}'
```

### Custom (eigene YAML)

```bash
curl -X POST http://localhost/stations \
  -H "Content-Type: application/json" \
  -d '{"persona_yaml": "station:\n  id: mein-sender\n  ...", "station_id": "mein-sender"}'
```

Tracks werden automatisch per LLM generiert wenn `tracks_json` fehlt.

### Via UI

1. Hub Landing Page oeffnen (`http://localhost`)
2. "+ Neue Station" Card klicken
3. "Random" → LLM generiert Persona + Tracks → Preview → "Starten"
4. "Custom" → YAML eingeben/einfuegen → "Starten"

## Station stoppen

Nur mit Admin-Token moeglich:

```bash
curl -X DELETE http://localhost/stations/{station_id} \
  -H "Authorization: Bearer raido-admin"
```

**Regeln:**
- Die letzte laufende Station kann nie gestoppt werden
- Stations mit `raido.station.protected=true` Label sind geschuetzt
- Auto-Stop: Stations ohne Hoerer werden nach 2h automatisch gestoppt

## Auto-Stop

Ein Background-Task prueft alle 5 Minuten:
1. Hat die Station 0 Listener?
2. Ist sie seit > 2 Stunden idle?
3. Ist sie NICHT die letzte laufende Station?
4. Ist sie NICHT als `protected` markiert?

Wenn alle Bedingungen erfuellt → Container wird gestoppt und entfernt.

## Token Explosion Preventer

Schutz gegen ueberlange Eingaben (Prompt-Injection, Token-Verschwendung):

- **Limit:** 500 Zeichen pro Eingabe (konfigurierbar via `MAX_INPUT_CHARS`)
- **Frontend:** Live-Zeichenzaehler, rote Markierung, Alert-Modal bei Ueberschreitung
- **Backend:** HTTP 413 Response wenn Limit ueberschritten
- Gilt fuer alle `/inject` Requests an jede Station

## Persona-Generator

Der LLM generiert auf Knopfdruck eine komplette Station:

1. **Persona-YAML** — Station-Config, DJ-Bio, Quirks, Regeln
2. **Track-Library** — 40 echte Tracks passend zum Genre (JSON)

Optional: Genre-Hint mitgeben fuer gerichtete Generierung.

Alle generierten Personas werden in `hub/data/hub.db` archiviert.

## API-Referenz

| Endpoint | Methode | Auth | Beschreibung |
|---|---|---|---|
| `/` | GET | - | Landing Page |
| `/stations` | GET | - | Laufende Stations |
| `/stations` | POST | - | Neue Station erstellen |
| `/stations/{id}` | DELETE | Admin | Station stoppen |
| `/generate-persona` | POST | - | LLM generiert Persona + Tracks |
| `/personas` | GET | - | Archivierte Personas |
| `/overview` | GET | - | Aggregierte Tech-Stats |
| `/s/{slug}/{path}` | * | - | Proxy zu Station |

## Umgebungsvariablen

| Variable | Default | Beschreibung |
|---|---|---|
| `HUB_PORT` | `80` | Hub-Port |
| `ADMIN_TOKEN` | `raido-admin` | Token fuer Admin-Aktionen |
| `STATION_IMAGE` | `raido-station:latest` | Docker-Image fuer neue Stations |
| `MAX_INPUT_CHARS` | `500` | Max. Zeichenlaenge pro Eingabe |
| `LLM_DJ_*` | - | LLM-Config (wird an Stations weitergereicht) |
| `LLM_FILTER_*` | - | Filter-LLM-Config |
| `LLM_FALLBACK_*` | - | Fallback-LLM-Config |
| `TIME_SCALE` | `60` | Default-Zeitskalierung fuer neue Stations |

## Dateien

```
hub/
  Dockerfile
  requirements.txt
  app/
    main.py              FastAPI (Landing, Stations-API, Proxy, Persona-Gen)
    docker_mgr.py        Docker SDK (discover, create, stop, auto-cleanup)
    persona_generator.py LLM-Prompts fuer Persona + Track-Generierung
    db.py                SQLite (Personas-Archiv, Station-Registry)
    llm.py               Provider-agnostischer LLM-Client
  web/
    index.html           Landing Page (Dark Theme)
  data/
    hub.db               SQLite-DB (auto-generiert)

docker-compose.yml       Root-Level: Hub + Default-Station
personas/                Generierte Persona-YAMLs + Track-Libraries
```

## Zusammenspiel mit Station

```
docker-compose.yml (root)
├── hub (Port 80)
│   ├── Docker-Socket → findet laufende Stations
│   ├── /personas Volume → schreibt neue Persona-Dateien
│   └── Proxy → routet /s/{slug}/ zu Station-Ports
│
├── station-default (Port 8080, protected)
│   ├── /personas Volume → liest Persona-YAML
│   └── Eigene DB in station/data/
│
└── raido-{id} (dynamisch erstellt vom Hub)
    ├── Image: raido-station:latest
    ├── Port: 8081-8099 (auto-assigned)
    ├── /personas Volume → liest generierte YAML + Tracks
    └── Eigene DB als Docker Volume
```

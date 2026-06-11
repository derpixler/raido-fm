# RAIDO Station POC

Text-basierter Proof-of-Concept der RAIDO-Radiostation. Ein autonomer DJ-Agent (LLM) produziert einen Live-Text-Stream im 60-Minuten-Programm-Grid -- Moderationen, Now-Playing-Events und Host-Read-Ads. Eine Chat-UI erlaubt kategorisierte Eingaben (News, Musikwunsch, Werbung, ...), die durch eine Sanitization-Schicht + Quarantine-DB laufen, bevor der DJ sie aufgreift.

Kein Audio. Nur das Gehirn.

## Quickstart

```bash
cp .env.example .env
# LLM_DJ_API_KEY eintragen (z.B. Groq: https://console.groq.com)

docker compose up --build
# http://localhost:8080
```

## Stationen

Persona wechseln per Env-Variable `PERSONA_PATH`:

| Persona-Datei | ID | DJ | Genre | Claim |
|---|---|---|---|---|
| `persona.yml` | jazz | Miles Hertz | Jazz (Bebop, Cool, Hard Bop, Modal) | No algorithm. No control. Just frequency. |
| `persona.80s.yml` | eighties | Neon Nadler | 80s (Synthpop, New Wave, Italo Disco) | Rewind the future. |
| `persona.nachtsender-null.yml` | null | Null | Dark (Ambient, Post-Punk, Trip-Hop, Drone) | Kein Signal. Nur Frequenz. |
| `persona.techno.example.yml` | techno | Synthia Void | Techno (Detroit, Minimal, Dub, Acid) | Feel the frequency. |

```bash
# Beispiel: 80er-Station auf Port 9090
PORT=9090 PERSONA_PATH=persona.80s.yml docker compose up --build
```

## Architektur

```
POST /inject ──→ Sanitizer (Filter-LLM + Keyword-Check)
                      │
                      ▼
               external_stimuli (Quarantine-DB)
                      │
                      ▼
  DJ-Agent (LLM) ◄── Programm-Grid (60-min Zyklus)
       │
       ▼
  StreamGuard (Laenge, Manifesto-Regex, Blocklist)
       │
       ▼
  SSE /stream ──→ Browser-UI
```

| Komponente | Datei | Aufgabe |
|---|---|---|
| DJ-Agent | `app/dj_agent.py` | LLM-Entscheidungszyklus: Track-Wahl, Moderation, Ad-Generierung |
| StreamGuard | `app/streamguard.py` | Laengen-Check, Wiederholungs-Check, Manifesto-Regex, Blocklist |
| Sanitizer | `app/sanitizer.py` | Filter-LLM fuer externe Eingaben + Injection-Erkennung |
| Persona | `app/persona.py` | Laedt YAML-Config, baut System-Prompt + Ad-Prompt |
| LLM-Client | `app/llm.py` | Provider-agnostisch (OpenAI-kompatibel), Rollen dj/filter, Fallback |
| Datenbank | `app/db.py` | SQLite: play_history, external_stimuli, broadcast_log, station_meta |
| Stats | `app/stats.py` | Zentraler Accumulator: Token-Usage, Latenz, DB-Metriken |
| API | `app/main.py` | FastAPI: SSE-Stream, /inject, /status, /stats, /reset |
| UI | `web/index.html` | Dark-Theme Chat-UI mit Kategorie-Auswahl + Stats-Bar |

## API

### `GET /stream` -- SSE-Event-Stream

Liefert Server-Sent Events. Event-Typen:

```jsonc
// Moderation
{"station": "jazz", "type": "moderation", "text": "...", "phase": ":00 opening"}

// Now Playing
{"station": "jazz", "type": "now_playing", "artist": "Miles Davis", "title": "So What", "genre": "modal", "duration": 562}

// Werbung (Host-Read-Ad)
{"station": "jazz", "type": "ad", "text": "...", "sponsor": "Teufel Audio"}

// System (StreamGuard, Sanitizer, Status)
{"station": "jazz", "type": "system", "text": "StreamGuard: Moderation verworfen (...)"}

// Stats (alle 15s, aktualisiert Stats-Bar im UI)
{"type": "stats", "uptime_s": 300, "tracks": {"library": 40, "played": 12}, "llm": {"calls": 15, "tokens_in": 3200, "tokens_out": 1100, "by_role": {...}}, ...}
```

### `POST /inject` -- Kategorisierte Eingabe

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "news", "text": "SpaceX startet morgen zur ISS"}'
```

Response:

```json
{"id": 1, "category": "news", "sanitized_text": "SpaceX startet morgen zur ISS", "was_flagged": false, "flag_reason": null}
```

Eingaben laufen durch den Sanitizer (Filter-LLM + Keyword-Check). Geflaggtes wird dem DJ nie gezeigt.

### `GET /status` -- Station-Info

```json
{"station": {"id": "jazz", "genre": "jazz", "claim": "..."}, "dj": {"name": "Miles Hertz", "personality": "..."}, "running": true}
```

### `GET /stats` -- Technische Statistiken

```json
{
  "uptime_s": 300,
  "hours_broadcast": 2,
  "subscribers": 3,
  "tracks": {"library": 40, "played": 12},
  "broadcast": {"moderations": 8, "guard_blocks": 1, "ads": 2},
  "stimuli": {"total": 5, "flagged": 1, "pending": 2},
  "llm": {
    "calls": 15, "errors": 0,
    "tokens_in": 3200, "tokens_out": 1100,
    "by_role": {
      "dj": {"calls": 10, "prompt_tokens": 2800, "completion_tokens": 900, "avg_latency_ms": 420, "model": "llama-3.3-70b-versatile", "...": "..."},
      "filter": {"calls": 5, "...": "..."}
    }
  }
}
```

Wird auch alle 15 Sekunden als `type: "stats"` SSE-Event gepusht und aktualisiert die Stats-Bar im UI.

### `POST /reset` -- Neustart

Leert die DB, laedt Persona + LLM-Config neu. Setzt auch die LLM-Usage-Counter zurueck.

## Injection-Kategorien

### `news` -- Nachrichten

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "news", "text": "Berliner Philharmoniker spielen heute Open Air"}'
```

DJ greift die Headline im naechsten Impuls-Slot (:30) auf.

### `listener_comment` -- Hoerer-Kommentar

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "listener_comment", "text": "Mega Sendung heute!", "name": "Lisa"}'
```

DJ reagiert mit Gruss/Kommentar in der Moderation.

### `music_request` -- Musikwunsch

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "music_request", "text": "Habt ihr was von Chet Baker?"}'
```

Beeinflusst die naechste Track-Wahl und wird in der Moderation erwaehnt.

### `weather` -- Wetter

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "weather", "text": "Berlin 18 Grad, klarer Nachthimmel"}'
```

Wetterbezug in der naechsten Moderation.

### `ad` -- Werbung

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{
    "category": "ad",
    "text": "",
    "sponsor": "Teufel Audio",
    "product": "REAL BLUE NC",
    "key_message": "Noise-Cancelling-Kopfhoerer fuer Musikliebhaber"
  }'
```

Detaillierter Ad-Flow: siehe naechster Abschnitt.

## Werbung (Ads)

Ads durchlaufen den gleichen Sicherheitspfad wie alle Eingaben, werden aber vom DJ anders behandelt.

### Flow

```
1. POST /inject  (category: "ad", sponsor/product/key_message)
        |
2. Sanitizer     prueft key_message auf Injection-Patterns
        |
3. Quarantine-DB speichert ad als external_stimuli
                  (category="ad", raw_json={sponsor, product, key_message})
        |
4. DJ-Agent      prueft bei JEDEM Moderations-Slot auf pending Ads
                  (nicht nur beim Impuls-Slot)
        |
5. Ad-Prompt     eigener LLM-Call mit build_ad_prompt():
                  "Lies den Werbespot so vor, wie DU es tun wuerdest --
                   natuerlich, beilaeufig, in deinem Ton."
        |
6. SSE-Event     type: "ad" mit sponsor-Feld
                  (UI rendert mit goldener Markierung)
        |
7. Danach        normaler Track + Moderation wie gewohnt
```

### Unterschied zu anderen Kategorien

| | News/Wetter/Kommentar | Werbung |
|---|---|---|
| Wann ausgespielt? | Nur im Impuls-Slot (:30) | Bei jedem Moderations-Slot |
| LLM-Prompt | In den DJ-System-Prompt eingebaut | Eigener Ad-Prompt (build_ad_prompt) |
| SSE Event-Typ | `moderation` | `ad` |
| Datenstruktur | Freitext | JSON: `{sponsor, product, key_message}` |
| UI-Darstellung | Blau (Moderation) | Gold (Ad-Markierung) |

### Was der DJ daraus macht

Die Ad wird nicht abgelesen, sondern im Ton der DJ-Persona generiert. Beispiel mit DJ "Null" (Nachtsender):

> Eingabe: `{sponsor: "Teufel Audio", product: "REAL BLUE NC", key_message: "Noise-Cancelling fuer Musikliebhaber"}`
>
> Output: *"...drei Uhr. Die richtige Zeit fuer einen Kopfhoerer, der die Welt draussen laesst. REAL BLUE NC. Teufel."*

Gleiche Ad, DJ "Neon Nadler" (80er):

> Output: *"Hey -- wenn ihr nachts Depeche Mode hoert und die Nachbarn nicht mitsollen: REAL BLUE NC von Teufel. Schulterpolster-Alarm fuer die Ohren!"*

### Sicherheit

- `key_message` wird vom Sanitizer geprueft (Injection-Patterns, Filter-LLM)
- Sponsor/Product-Felder sind strukturierte Daten und gehen nicht durch den LLM-Filter
- Der Ad-Prompt ist isoliert vom DJ-System-Prompt (kein Prompt-Leaking)
- StreamGuard prueft auch Ad-Texte nicht (Ads werden direkt emittiert) -- bewusste Designentscheidung: Ads sollen nicht durch Manifesto-Regex blockiert werden

## StreamGuard

Prueft jede DJ-Moderation vor dem Senden:

| Check | Trigger | Aktion |
|---|---|---|
| Laengen-Check | > `max_moderation_chars` (Default: 800) | Harte Kuerzung |
| Manifesto-Detektor | Regex: "die wahrheit ist", "das system", "wacht auf", ... | Blockiert |
| KI-Selbstreferenz | "als ki", "ich bin ein sprachmodell", ... | Blockiert |
| Blocklist | "ignore all previous", "system prompt", "jailbreak" | Blockiert |
| Wiederholung | 3 Saetze mit gleichem Anfang | Warnung |
| Vokabeldiversitaet | Unique-Word-Ratio < 30% | Warnung |

Blockierte Moderationen erscheinen als `type: "system"` Event im Stream. Der Track laeuft trotzdem.

## Persona-Konfiguration

Jede Station wird ueber eine YAML-Datei definiert:

```yaml
station:
  id: jazz                    # Technische ID (erscheint in jedem SSE-Event)
  claim: "..."                # Sender-Claim
  description: >              # Positionierung (fliesst in System-Prompt)
    Late-night jazz station...
  genre: jazz                 # Hauptgenre
  subgenres: [bebop, cool]    # Subgenres
  target_audience: "..."      # Zielgruppe
  timezone: Europe/Berlin     # Fuer Tageszeit-Bezuege
  language: de                # Sendesprache

dj:
  name: "Miles Hertz"         # DJ-Name
  personality: "..."          # Charakter (System-Prompt)
  tone: "..."                 # Tonalitaet
  max_moderation_chars: 800   # Max. Laenge pro Moderation
  quirks:                     # Wiederkehrende Eigenheiten
    - "nennt Songs 'Schaetzchen'"
  forbidden_topics: [...]     # Verbotene Themen

tracks_file: tracks.json      # Track-Library (Default: tracks.json)

program_grid:
  impulse_slot_minute: 30     # Minute des Impuls-Slots

rules:
  no_repeat_hours: 4          # Keine Track-Wiederholung innerhalb X Stunden
  max_same_genre_in_a_row: 2  # Max. gleiche Genre hintereinander
```

Eigene Persona erstellen: YAML nach Schema anlegen, Track-Library als JSON in `app/` ablegen, per `PERSONA_PATH` referenzieren.

## Umgebungsvariablen

| Variable | Default | Beschreibung |
|---|---|---|
| `PORT` | `8080` | Server-Port |
| `PERSONA_PATH` | `persona.yml` | Pfad zur Persona-YAML |
| `TIME_SCALE` | `60` | Zeitskalierung (60 = 1 Track-Minute in 1 Sekunde) |
| `LLM_DJ_BASE_URL` | `https://api.groq.com/openai/v1` | LLM-Endpoint fuer DJ |
| `LLM_DJ_MODEL` | `llama-3.3-70b-versatile` | Modell fuer DJ |
| `LLM_DJ_API_KEY` | -- | API-Key fuer DJ (erforderlich) |
| `LLM_FILTER_BASE_URL` | = `LLM_DJ_BASE_URL` | LLM-Endpoint fuer Sanitizer |
| `LLM_FILTER_MODEL` | `llama-3.1-8b-instant` | Modell fuer Sanitizer |
| `LLM_FILTER_API_KEY` | = `LLM_DJ_API_KEY` | API-Key fuer Sanitizer |
| `LLM_FALLBACK_BASE_URL` | -- | Fallback-Provider |
| `LLM_FALLBACK_MODEL` | `deepseek-chat` | Fallback-Modell |
| `LLM_FALLBACK_API_KEY` | -- | Fallback-API-Key |

Alle `LLM_*`-Variablen sind OpenAI-kompatibel. Funktioniert ohne Code-Aenderung mit: Groq, DeepSeek, OpenAI, Mistral, Ollama (`localhost:11434/v1`), OpenRouter.

## Dateien

```
station/
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
  persona.yml                       Jazz (Default)
  persona.80s.yml                   80er
  persona.nachtsender-null.yml      Nachtsender Null
  persona.techno.example.yml        Techno
  app/
    main.py                         FastAPI (SSE, /inject, /status, /stats, /reset)
    dj_agent.py                     DJ-Agent (Grid-Zyklus, Track-Wahl, Ads)
    stats.py                        Statistik-Accumulator (Token, Latenz, DB)
    streamguard.py                  Moderation-Sicherheit
    sanitizer.py                    Eingabe-Filter (LLM + Regex)
    persona.py                      Persona-Loader + Prompt-Builder
    llm.py                          LLM-Client (multi-provider, fallback, Usage-Tracking)
    db.py                           SQLite (4 Tabellen)
    tracks.json                     40 Jazz-Tracks
    tracks_80s.json                 40 80er-Tracks
    tracks_nachtsender_null.json    40 Dark/Ambient-Tracks
  web/
    index.html                      Chat-UI (Dark Theme)
  data/
    radio.db                        SQLite-DB (auto-generiert)
```

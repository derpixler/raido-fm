# RAIDO Station POC

Text-based proof of concept of the RAIDO radio station. An autonomous DJ agent (LLM) produces a live text stream in a 60-minute program grid -- moderations, now-playing events, and host-read ads. A chat UI allows categorized inputs (news, music requests, ads, ...) that pass through a sanitization layer + quarantine DB before the DJ picks them up.

No audio. Just the brain.

## Quickstart

```bash
cp .env.example .env
# Enter LLM_DJ_API_KEY (e.g. Groq: https://console.groq.com)

docker compose up --build
# http://localhost:8080
```

## Stations

Switch persona via env variable `PERSONA_PATH`:

| Persona File | ID | DJ | Genre | Claim |
|---|---|---|---|---|
| `persona.yml` | jazz | Miles Hertz | Jazz (Bebop, Cool, Hard Bop, Modal) | No algorithm. No control. Just frequency. |
| `persona.80s.yml` | eighties | Neon Nadler | 80s (Synthpop, New Wave, Italo Disco) | Rewind the future. |
| `persona.nachtsender-null.yml` | null | Null | Dark (Ambient, Post-Punk, Trip-Hop, Drone) | No signal. Just frequency. |
| `persona.techno.example.yml` | techno | Synthia Void | Techno (Detroit, Minimal, Dub, Acid) | Feel the frequency. |

```bash
# Example: 80s station on port 9090
PORT=9090 PERSONA_PATH=persona.80s.yml docker compose up --build
```

## Architecture

```
POST /inject ──→ Sanitizer (Filter-LLM + Keyword-Check)
                      │
                      ▼
               external_stimuli (Quarantine-DB)
                      │
                      ▼
  DJ-Agent (LLM) ◄── Program-Grid (60-min cycle)
       │
       ▼
  StreamGuard (length, manifesto regex, blocklist)
       │
       ▼
  SSE /stream ──→ Browser-UI
```

| Component | File | Role |
|---|---|---|
| DJ Agent | `app/dj_agent.py` | LLM decision cycle: track selection, moderation, ad generation |
| StreamGuard | `app/streamguard.py` | Length check, repetition check, manifesto regex, blocklist |
| Sanitizer | `app/sanitizer.py` | Filter LLM for external inputs + injection detection |
| Persona | `app/persona.py` | Loads YAML config, builds system prompt + ad prompt |
| LLM Client | `app/llm.py` | Provider-agnostic (OpenAI-compatible), roles dj/filter, fallback |
| Database | `app/db.py` | SQLite: play_history, external_stimuli, broadcast_log, station_meta |
| Stats | `app/stats.py` | Central accumulator: token usage, latency, DB metrics |
| API | `app/main.py` | FastAPI: SSE stream, /inject, /status, /stats, /reset |
| UI | `web/index.html` | Dark theme chat UI with category selection + stats bar |

## API

### `GET /stream` -- SSE Event Stream

Delivers Server-Sent Events. Event types:

```jsonc
// Moderation
{"station": "jazz", "type": "moderation", "text": "...", "phase": ":00 opening"}

// Now Playing
{"station": "jazz", "type": "now_playing", "artist": "Miles Davis", "title": "So What", "genre": "modal", "duration": 562}

// Advertising (Host-Read-Ad)
{"station": "jazz", "type": "ad", "text": "...", "contributor": "Teufel Audio"}

// System (StreamGuard, Sanitizer, Status)
{"station": "jazz", "type": "system", "text": "StreamGuard: Moderation discarded (...)"}

// Stats (every 15s, updates stats bar in UI)
{"type": "stats", "uptime_s": 300, "tracks": {"library": 40, "played": 12}, "llm": {"calls": 15, "tokens_in": 3200, "tokens_out": 1100, "by_role": {...}}, ...}
```

### `POST /inject` -- Categorized Input

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "news", "text": "SpaceX launching to ISS tomorrow"}'
```

Response:

```json
{"id": 1, "category": "news", "sanitized_text": "SpaceX launching to ISS tomorrow", "was_flagged": false, "flag_reason": null}
```

Inputs pass through the sanitizer (filter LLM + keyword check). Flagged content is never shown to the DJ.

### `GET /status` -- Station Info

```json
{"station": {"id": "jazz", "genre": "jazz", "claim": "..."}, "dj": {"name": "Miles Hertz", "personality": "..."}, "running": true}
```

### `GET /stats` -- Technical Statistics

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

Also pushed every 15 seconds as a `type: "stats"` SSE event and updates the stats bar in the UI.

### `POST /reset` -- Restart

Clears the DB, reloads persona + LLM config. Also resets the LLM usage counters.

## Injection Categories

### `news` -- News

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "news", "text": "Berlin Philharmonic playing open air tonight"}'
```

DJ picks up the headline in the next impulse slot (:30).

### `listener_comment` -- Listener Comment

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "listener_comment", "text": "Great show today!", "name": "Lisa"}'
```

DJ reacts with greeting/comment in the moderation.

### `music_request` -- Music Request

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "music_request", "text": "Got anything by Chet Baker?"}'
```

Influences the next track selection and is mentioned in the moderation.

### `weather` -- Weather

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{"category": "weather", "text": "Berlin 18°C, clear night sky"}'
```

Weather reference in the next moderation.

### `ad` -- Advertising

```bash
curl -X POST http://localhost:8080/inject \
  -H "Content-Type: application/json" \
  -d '{
    "category": "ad",
    "text": "",
    "contributor": "Teufel Audio",
    "product": "REAL BLUE NC",
    "key_message": "Noise-cancelling headphones for music lovers"
  }'
```

Detailed ad flow: see next section.

## Advertising (Ads)

Ads go through the same security path as all inputs, but are treated differently by the DJ.

### Flow

```
1. POST /inject  (category: "ad", contributor/product/key_message)
        |
2. Sanitizer     checks key_message for injection patterns
        |
3. Quarantine DB stores ad as external_stimuli
                 (category="ad", raw_json={contributor, product, key_message})
        |
4. DJ Agent      checks for pending ads at EVERY moderation slot
                 (not just the impulse slot)
        |
5. Ad Prompt     separate LLM call with build_ad_prompt():
                 "Read the ad spot the way YOU would --
                  natural, casual, in your tone."
        |
6. SSE Event     type: "ad" with contributor field
                 (UI renders with gold marking)
        |
7. Afterwards    normal track + moderation as usual
```

### Differences from Other Categories

| | News/Weather/Comment | Advertising |
|---|---|---|
| When played? | Only in impulse slot (:30) | At every moderation slot |
| LLM prompt | Built into DJ system prompt | Separate ad prompt (build_ad_prompt) |
| SSE event type | `moderation` | `ad` |
| Data structure | Free text | JSON: `{contributor, product, key_message}` |
| UI display | Blue (moderation) | Gold (ad marking) |

### What the DJ Does With It

The ad is not read verbatim, but generated in the tone of the DJ persona. Example with DJ "Null" (Night Station):

> Input: `{contributor: "Teufel Audio", product: "REAL BLUE NC", key_message: "Noise cancelling for music lovers"}`
>
> Output: *"...three in the morning. The right time for headphones that leave the world outside. REAL BLUE NC. Teufel."*

Same ad, DJ "Neon Nadler" (80s):

> Output: *"Hey -- when you're listening to Depeche Mode at night and don't want the neighbors in on it: REAL BLUE NC by Teufel. Shoulder pad alert for your ears!"*

### Security

- `key_message` is checked by the sanitizer (injection patterns, filter LLM)
- Contributor/Product fields are structured data and do not go through the LLM filter
- The ad prompt is isolated from the DJ system prompt (no prompt leaking)
- StreamGuard does not check ad texts either (ads are emitted directly) -- deliberate design decision: ads should not be blocked by manifesto regex

## StreamGuard

Checks every DJ moderation before sending:

| Check | Trigger | Action |
|---|---|---|
| Length check | > `max_moderation_chars` (Default: 800) | Hard truncation |
| Manifesto detector | Regex: "the truth is", "the system", "wake up", ... | Blocked |
| AI self-reference | "as an ai", "i am a language model", ... | Blocked |
| Blocklist | "ignore all previous", "system prompt", "jailbreak" | Blocked |
| Repetition | 3 sentences with same beginning | Warning |
| Vocabulary diversity | Unique-word-ratio < 30% | Warning |

Blocked moderations appear as `type: "system"` events in the stream. The track still plays.

## Persona Configuration

Each station is defined via a YAML file:

```yaml
station:
  id: jazz                    # Technical ID (appears in every SSE event)
  claim: "..."                # Station claim
  description: >              # Positioning (flows into system prompt)
    Late-night jazz station...
  genre: jazz                 # Main genre
  subgenres: [bebop, cool]    # Subgenres
  target_audience: "..."      # Target audience
  timezone: Europe/Berlin     # For time-of-day references
  language: de                # Broadcast language

dj:
  name: "Miles Hertz"         # DJ name
  personality: "..."          # Character (system prompt)
  tone: "..."                 # Tonality
  max_moderation_chars: 800   # Max. length per moderation
  quirks:                     # Recurring mannerisms
    - "calls songs 'darlings'"
  forbidden_topics: [...]     # Forbidden topics

tracks_file: tracks.json      # Track library (Default: tracks.json)

program_grid:
  impulse_slot_minute: 30     # Minute of the impulse slot

rules:
  no_repeat_hours: 4          # No track repeat within X hours
  max_same_genre_in_a_row: 2  # Max. same genre in a row
```

Create your own persona: Write YAML according to schema, place track library as JSON in `app/`, reference via `PERSONA_PATH`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Server port |
| `PERSONA_PATH` | `persona.yml` | Path to persona YAML |
| `TIME_SCALE` | `60` | Time scale (60 = 1 track minute in 1 second) |
| `LLM_DJ_BASE_URL` | `https://api.groq.com/openai/v1` | LLM endpoint for DJ |
| `LLM_DJ_MODEL` | `llama-3.3-70b-versatile` | Model for DJ |
| `LLM_DJ_API_KEY` | -- | API key for DJ (required) |
| `LLM_FILTER_BASE_URL` | = `LLM_DJ_BASE_URL` | LLM endpoint for sanitizer |
| `LLM_FILTER_MODEL` | `llama-3.1-8b-instant` | Model for sanitizer |
| `LLM_FILTER_API_KEY` | = `LLM_DJ_API_KEY` | API key for sanitizer |
| `LLM_FALLBACK_BASE_URL` | -- | Fallback provider |
| `LLM_FALLBACK_MODEL` | `deepseek-chat` | Fallback model |
| `LLM_FALLBACK_API_KEY` | -- | Fallback API key |

All `LLM_*` variables are OpenAI-compatible. Works without code changes with: Groq, DeepSeek, OpenAI, Mistral, Ollama (`localhost:11434/v1`), OpenRouter.

## Files

```
station/
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
  persona.yml                       Jazz (Default)
  persona.80s.yml                   80s
  persona.nachtsender-null.yml      Night Station Null
  persona.techno.example.yml        Techno
  app/
    main.py                         FastAPI (SSE, /inject, /status, /stats, /reset)
    dj_agent.py                     DJ Agent (grid cycle, track selection, ads)
    stats.py                        Statistics accumulator (tokens, latency, DB)
    streamguard.py                  Moderation security
    sanitizer.py                    Input filter (LLM + regex)
    persona.py                      Persona loader + prompt builder
    llm.py                          LLM client (multi-provider, fallback, usage tracking)
    db.py                           SQLite (4 tables)
    tracks.json                     40 Jazz tracks
    tracks_80s.json                 40 80s tracks
    tracks_nachtsender_null.json    40 Dark/Ambient tracks
  web/
    index.html                      Chat UI (Dark Theme)
  data/
    radio.db                        SQLite DB (auto-generated)
```

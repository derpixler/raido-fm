# Contributing to RAIDO FM

RAIDO FM is an open-source project for fully autonomous AI-powered internet radio.
Contributions are welcome in many forms — code, personas, documentation, or
providing API tokens to keep stations running.

## Token Contributors

You can help keep radio stations on-air by providing API tokens (DeepSeek, Groq,
OpenAI-compatible). In return, your message gets read on-air by the AI DJ with a
`[AD]` label — fully transparent, always clearly separated from editorial content.

This is a non-commercial resource contribution model. No money changes hands.
You provide tokens, the station broadcasts your message. That's it.

**To become a Token Contributor:**

1. Visit the Hub admin UI at your RAIDO instance
2. Click **"Become a Contributor"**
3. Fill in your name, API key, token budget, and message details
4. An admin will review and approve your request

Your API key is used exclusively to call the LLM for your ad placements. It is
never shared, logged, or used for any other purpose.

## Code Contributions

### Setup

```bash
git clone https://github.com/derpixler/raido-fm.git
cd raido-fm
cp .env.example .env
# edit .env with your LLM API keys
```

### Architecture

```
hub/        — Central Hub (FastAPI): manages stations, proxies traffic, admin UI
station/    — Radio Station (FastAPI): DJ agent, stream guard, sanitizer
web/        — Next.js landing page (static export, deployed to GitHub Pages)
personas/   — Generated persona YAML + track JSON libraries
```

### Running locally

```bash
# Start a single station for development
cd station
cp .env.example .env
docker compose up --build
# → http://localhost:8080

# Full multi-station setup
cd ..
docker compose up --build
# → Hub: http://localhost
# → Default station: http://localhost:8080
```

### Before submitting a PR

- Run the security scan: `bandit -r hub/ station/`
- Verify no secrets are committed: `gitleaks detect --source .`
- Test that `docker compose up --build` succeeds

### Code style

- Python: follow existing patterns (async/await, type hints, no unnecessary comments)
- TypeScript/Next.js: `npm run lint` in `web/`
- Keep changes focused — one concern per PR

## Persona Contributions

You can contribute radio station personas by submitting a `persona.yml` file.
Each persona defines a station's musical style, language, DJ personality, and
audience. See existing personas in `personas/` for examples.

## Communication

- **Issues**: GitHub Issues for bugs, features, and questions
- **Discussions**: GitHub Discussions for ideas and community topics

## License

Code is MIT. Content (personas, tracks, assets) is CC BY 4.0.
See `LICENSE` and `LICENSE-CONTENT` for details.

# scrapergraph-api

A ready-to-run setup of [ScrapeGraphAI](https://github.com/ScrapeGraphAI/Scrapegraph-ai):
point it at a URL, say in plain English what you want, and get JSON back.

```bash
python scrape.py https://some-shop.com/hoodies "List every product with name, price and colours"
```

## Setup

Needs Python 3.10–3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium        # headless browser used to load pages
cp .env.example .env               # then add your API key
```

## Choosing a model

Set `LLM_MODEL` in `.env` as `provider/model`:

| `LLM_MODEL` | key needed |
|---|---|
| `anthropic/claude-sonnet-5-5` (default) | `ANTHROPIC_API_KEY` |
| `anthropic/claude-haiku-4-5-20251001` — cheaper | `ANTHROPIC_API_KEY` |
| `openai/gpt-5-mini` | `OPENAI_API_KEY` |
| `ollama/llama3.2` — local and free | none; install [Ollama](https://ollama.com), `ollama pull llama3.2` |

Other providers ScrapeGraphAI supports (Groq, Mistral, Gemini, Bedrock, …) work the
same way once their `langchain-*` package is installed.

## Usage

```bash
python scrape.py <url-or-html-file> "<what to extract>" [--show-browser] [-v]
```

- A local `.html` file works as the source too, handy for testing prompts without re-fetching.
- `--show-browser` opens a visible Chromium window, which is useful when a site blocks headless browsers.
- For other graph types (multi-page search, `SearchGraph`, `ScriptCreatorGraph`, …) see the
  [ScrapeGraphAI docs](https://docs-oss.scrapegraphai.com/).

## HTTP API

`app.py` serves the same scraper over HTTP, so you can call it from anywhere.

```bash
uvicorn app:app --port 8000        # needs API_TOKEN and your provider key set
```

```bash
curl -X POST https://<your-host>/scrape \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://some-shop.com/hoodies", "prompt": "List every product with name and price"}'
# -> {"result": {...}}
```

`GET /health` needs no token and returns the configured model, which is useful as a
host health check. The app refuses to start without `API_TOKEN`: the endpoint spends
your LLM credits and fetches any URL it is given, so it must not be open.

## Deploying

The `Dockerfile` installs Chromium and bakes in the tokenizer files, so it runs on
any host that builds from a Dockerfile. It needs roughly **1 GB of RAM** (a headless
browser plus the Python stack); 512 MB plans tend to crash mid-scrape.

**Railway** (simplest):
1. New Project → Deploy from GitHub repo → pick this repo. It detects the Dockerfile.
2. Variables: `ANTHROPIC_API_KEY`, `API_TOKEN` (and `LLM_MODEL` to change model).
3. Settings → Networking → Generate Domain. Test with `https://<domain>/health`.

**Render**: New → Web Service → this repo, runtime Docker, same variables, health
check path `/health`. Choose an instance with ≥1 GB RAM.

**Fly.io**: `fly launch` (uses the Dockerfile), `fly secrets set ANTHROPIC_API_KEY=... API_TOKEN=...`,
`fly scale memory 1024`.

Serverless hosts (Vercel, Netlify functions) are not a fit: no room for Chromium,
and scrapes can outlast their time limits.

## Notes

- **`langchain-community` is pinned to 0.4.1.** scrapegraphai 1.76.0 imports
  `ChatOllama` from it, which 0.4.2 removed, so an unpinned install fails on import.
- On first run `tiktoken` downloads a tokenizer file from
  `openaipublic.blob.core.windows.net`. Behind a restrictive firewall, allow that host
  (or pre-populate `TIKTOKEN_CACHE_DIR`).
- Check a site's terms and `robots.txt` before scraping it.

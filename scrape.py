"""Scrape a page with ScrapeGraphAI: describe what you want, get JSON back.

    python scrape.py https://some-shop.com/hoodies "List every product with name, price and colours"

The model is chosen with LLM_MODEL in .env (see .env.example).
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph

load_dotenv()

# Context window per provider. ScrapeGraphAI splits pages into chunks of this
# size; it only knows sizes for older models, so we pass one explicitly.
DEFAULT_TOKENS = {
    "anthropic": 200_000,
    "openai": 128_000,
    "ollama": 8_192,
}


def llm_config() -> dict:
    model = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-5-5")
    provider = model.split("/", 1)[0]
    config = {
        "model": model,
        "temperature": 0,
        "model_tokens": int(os.getenv("LLM_MODEL_TOKENS", DEFAULT_TOKENS.get(provider, 8_192))),
    }
    if provider == "ollama":
        config["format"] = "json"
        config["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    else:
        key_var = f"{provider.upper()}_API_KEY"
        if not os.getenv(key_var):
            sys.exit(f"{key_var} is not set. Copy .env.example to .env and fill it in.")
        config["api_key"] = os.environ[key_var]
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", help="URL to scrape (or a local .html file path)")
    parser.add_argument("prompt", help="What to extract, in plain English")
    parser.add_argument("--show-browser", action="store_true", help="Run Chromium with a visible window")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    source = args.source
    if os.path.isfile(source):
        with open(source, encoding="utf-8") as f:
            source = f.read()

    graph = SmartScraperGraph(
        prompt=args.prompt,
        source=source,
        config={
            "llm": llm_config(),
            "headless": not args.show_browser,
            "verbose": args.verbose,
        },
    )
    print(json.dumps(graph.run(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

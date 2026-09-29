FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    TIKTOKEN_CACHE_DIR=/opt/tiktoken

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt \
 && playwright install --with-deps chromium \
 && python -c "import tiktoken; tiktoken.get_encoding('o200k_base'); tiktoken.get_encoding('cl100k_base')"
# ^ bakes the tokenizer files in so the container needs no download at runtime.

COPY scrape.py app.py ./

# Most hosts inject PORT; default to 8000 elsewhere.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]

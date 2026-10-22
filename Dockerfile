FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RESOLVEAI_HOST=0.0.0.0 \
    RESOLVEAI_PORT=8000

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 resolveai \
    && useradd --uid 10001 --gid resolveai --no-create-home resolveai \
    && mkdir -p /app/runtime /app/reports \
    && chown -R resolveai:resolveai /app
COPY --chown=resolveai:resolveai resolveai/ ./resolveai/
COPY --chown=resolveai:resolveai data/ ./data/
COPY --chown=resolveai:resolveai tests/ ./tests/
USER resolveai
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('RESOLVEAI_PORT','8000')+'/health',timeout=3).close()"
CMD ["python", "-m", "resolveai"]

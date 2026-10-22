"""Operator-provided model endpoint; defaults preserve native local setup."""
import os
from urllib.parse import urlsplit


def ollama_url(path):
    base = os.environ.get("RESOLVEAI_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    parsed = urlsplit(base)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path):
        raise ValueError("RESOLVEAI_OLLAMA_URL must be an HTTP(S) origin without credentials or a path.")
    return base + path

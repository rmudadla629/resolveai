"""Read-only local setup checks; never prints credentials."""

import importlib.metadata
import json
import sys
from urllib.request import urlopen

from . import auth, customers
from .embeddings import MODEL
from .config import ollama_url


def checks():
    results = [("Python 3.12+", sys.version_info >= (3, 12))]
    for package in ("Flask", "waitress"):
        try:
            version = importlib.metadata.version(package)
            results.append((f"{package} {version}", True))
        except importlib.metadata.PackageNotFoundError:
            results.append((package, False))
    results.append(("Reviewer credentials configured", auth.AUTH_PATH.is_file()))
    try:
        configured = json.loads(customers.CUSTOMER_PATH.read_text())
    except (OSError, ValueError):
        configured = {}
    for name in ("alex", "sam"):
        results.append((f"Customer {name} configured", isinstance(configured, dict) and name in configured))
    try:
        with urlopen(ollama_url("/api/tags"), timeout=5) as response:
            models = {m["name"] for m in json.load(response)["models"]}
        results.append(("Ollama reachable", True))
    except (OSError, ValueError, KeyError, TypeError):
        models = set()
        results.append(("Ollama reachable", False))
    for model in ("qwen3:4b", MODEL):
        results.append((f"Model installed: {model}", model in models))
    return results


def main():
    results = checks()
    for label, ok in results:
        print(f'{"OK" if ok else "MISSING"}: {label}')
    print("These checks confirm setup presence, not password validity, model accuracy, or deployment readiness.")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

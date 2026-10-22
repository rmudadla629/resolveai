"""Local embedding requests and cosine ranking of the small policy corpus."""

import json
import math
from functools import lru_cache
from urllib.request import Request, urlopen
from .config import ollama_url

MODEL = "all-minilm:22m"


def embed(texts):
    request = Request(ollama_url("/api/embed"),
                      data=json.dumps({"model": MODEL, "input": texts, "truncate": False}).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        vectors = json.load(response)["embeddings"]
    if (not isinstance(vectors, list) or len(vectors) != len(texts) or not vectors
            or any(not isinstance(v, list) or not v for v in vectors)
            or len({len(v) for v in vectors}) != 1
            or any(not isinstance(x, (int, float)) or not math.isfinite(x) for v in vectors for x in v)):
        raise ValueError("Invalid embeddings")
    return vectors


def cosine(a, b):
    if len(a) != len(b):
        raise ValueError("Embedding dimension mismatch")
    denominator = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0.0


@lru_cache(maxsize=4)
def document_vectors(texts):
    return embed(list(texts))


def rank(question, policies):
    texts = tuple(p["title"] + ". " + p["text"] for p in policies)
    documents = document_vectors(texts)
    query = embed([question])[0]
    return sorted([(cosine(query, vector), policy) for vector, policy in zip(documents, policies)],
                  key=lambda pair: pair[0], reverse=True)

import hashlib
import math
from collections import Counter

from app.core.config import settings


def _local_embedding(text: str, dimensions: int = 384) -> list[float]:
    tokens = [token.strip(".,:;!?()[]{}").lower() for token in (text or "").split()]
    vector = [0.0] * dimensions
    counts = Counter(token for token in tokens if token)
    for token, count in counts.items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [round(value / norm, 6) for value in vector]
    return vector


def get_embedding(text: str) -> list[float]:
    provider = (settings.EMBEDDING_PROVIDER or "local").lower()
    if provider == "openai" and settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=text)
            return list(response.data[0].embedding)
        except Exception:
            return _local_embedding(text, settings.EMBEDDING_DIMENSIONS)
    return _local_embedding(text, settings.EMBEDDING_DIMENSIONS)


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    numerator = sum(float(left[index]) * float(right[index]) for index in range(length))
    left_norm = math.sqrt(sum(float(value) * float(value) for value in left[:length]))
    right_norm = math.sqrt(sum(float(value) * float(value) for value in right[:length]))
    if not left_norm or not right_norm:
        return 0.0
    return round(numerator / (left_norm * right_norm), 4)

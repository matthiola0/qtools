import hashlib


def universe_key(symbols: list[str]) -> str:
    """Stable short hash of a symbol list (order-insensitive) for cache filenames."""
    return hashlib.md5("_".join(sorted(symbols)).encode()).hexdigest()[:10]

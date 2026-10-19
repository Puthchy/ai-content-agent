"""Scene images. Add a real provider (Midjourney, Flux, Imagen, ...) in PROVIDERS."""

import hashlib
from pathlib import Path

from PIL import Image


def placeholder(prompt: str, out: Path, width: int, height: int) -> Path:
    """Solid colour derived from the prompt, so test runs need no image API."""
    digest = hashlib.sha256(prompt.encode()).digest()
    Image.new("RGB", (width, height), tuple(64 + b // 2 for b in digest[:3])).save(out)
    return out


PROVIDERS = {"placeholder": placeholder}


def generate(prompt: str, out: Path, provider: str, width: int, height: int) -> Path:
    if provider not in PROVIDERS:
        raise ValueError(f"unknown image provider {provider!r}; add it to PROVIDERS in agent/images.py")
    return PROVIDERS[provider](prompt, out, width, height)

"""Narration audio: ElevenLabs if configured, else free gTTS, else silence."""

import subprocess
from pathlib import Path

import httpx


def synthesize(text: str, out: Path, provider: str, eleven_key: str | None,
               eleven_voice: str | None, fallback_seconds: float) -> Path:
    if provider == "auto":
        provider = "elevenlabs" if eleven_key and eleven_voice else "gtts"

    if provider == "elevenlabs":
        r = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{eleven_voice}",
            headers={"xi-api-key": eleven_key},
            json={"text": text, "model_id": "eleven_multilingual_v2"},
            timeout=120,
        )
        r.raise_for_status()
        out.write_bytes(r.content)
        return out

    if provider == "gtts":
        from gtts import gTTS
        gTTS(text=text, lang="th").save(str(out))
        return out

    # provider == "none": silent track so the video step still works.
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "anullsrc=r=44100:cl=mono", "-t", str(fallback_seconds), str(out)],
        check=True,
    )
    return out


def duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())

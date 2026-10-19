"""Load config.yaml and .env into one object the pipeline can read."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
OUTPUT_DIR = ROOT / "output"


@dataclass
class Settings:
    raw: dict
    anthropic_key: str | None
    elevenlabs_key: str | None
    elevenlabs_voice: str | None
    affiliate_links: list[str]

    @property
    def channel(self) -> dict:
        return self.raw["channel"]

    @property
    def content(self) -> dict:
        return self.raw["content"]

    def section(self, name: str) -> dict:
        return self.raw.get(name, {})


def load_settings(config_path: Path | None = None) -> Settings:
    load_dotenv(ROOT / ".env")
    path = config_path or ROOT / "config.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    links = [s.strip() for s in os.getenv("SHOPEE_AFFILIATE_LINKS", "").split(",") if s.strip()]
    return Settings(
        raw=raw,
        anthropic_key=os.getenv("ANTHROPIC_API_KEY") or None,
        elevenlabs_key=os.getenv("ELEVENLABS_API_KEY") or None,
        elevenlabs_voice=os.getenv("ELEVENLABS_VOICE_ID") or None,
        affiliate_links=links,
    )


def render_prompt(name: str, **values) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").format(**values)

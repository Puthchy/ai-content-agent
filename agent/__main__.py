"""CLI: python -m agent run [--count N] [--dry-run]"""

import argparse
import sys

from .config import OUTPUT_DIR, load_settings, render_prompt
from .pipeline import Pipeline


def main() -> int:
    parser = argparse.ArgumentParser(prog="agent", description="AI short-story clip factory")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="make clips")
    run.add_argument("--count", type=int, default=1)
    run.add_argument("--dry-run", action="store_true", help="no API calls; canned script, silent audio")
    args = parser.parse_args()

    settings = load_settings()
    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.dry_run:
        from .fake import FakeLLM
        llm = FakeLLM()
        settings.raw.setdefault("tts", {})["provider"] = "none"
        settings.raw.setdefault("images", {})["provider"] = "placeholder"
        settings.raw["content"]["affiliate_ratio"] = 1.0
    else:
        if not settings.anthropic_key:
            print("ยังไม่ได้ใส่ ANTHROPIC_API_KEY ใน .env (หรือรันด้วย --dry-run เพื่อทดสอบ)", file=sys.stderr)
            return 1
        from .llm import LLM
        m = settings.section("model")
        llm = LLM(settings.anthropic_key, m.get("name", "claude-opus-5-5"),
                  m.get("effort", "medium"), render_prompt("system", **settings.channel))

    pipeline = Pipeline(settings, llm)
    for i in range(args.count):
        print(f"--- คลิป {i + 1}/{args.count} ---")
        pipeline.make_clip()
    return 0


if __name__ == "__main__":
    sys.exit(main())

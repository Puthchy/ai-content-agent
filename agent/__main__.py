"""CLI: python -m agent run [--count N] [--dry-run] | python -m agent serve [--port P]"""

import argparse
import sys

from .config import OUTPUT_DIR, load_settings
from .pipeline import build_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(prog="agent", description="AI short-story clip factory")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="make clips")
    run.add_argument("--count", type=int, default=1)
    run.add_argument("--dry-run", action="store_true", help="no API calls; canned script, silent audio")
    serve = sub.add_parser("serve", help="open the web interface")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.command == "serve":
        from .web import serve as start
        start(args.host, args.port)
        return 0

    try:
        pipeline = build_pipeline(load_settings(), args.dry_run)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    for i in range(args.count):
        print(f"--- คลิป {i + 1}/{args.count} ---")
        pipeline.make_clip()
    return 0


if __name__ == "__main__":
    sys.exit(main())

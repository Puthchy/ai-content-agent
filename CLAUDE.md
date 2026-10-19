# ai-content-agent

Pipeline that turns one command into a ready-to-post vertical short-story clip (Thai), optionally tied to a Shopee affiliate product.

## Layout

- `config.yaml` — channel persona, niche, clip length, model, providers. Change behaviour here before touching code.
- `prompts/*.md` — prompt templates (Thai), filled with `str.format`. Literal braces must be doubled.
- `agent/pipeline.py` — the steps: ideas → script → TTS → images → video → caption. One folder per clip in `output/`.
- `agent/llm.py` — Claude calls with structured JSON output validated by the pydantic models in `agent/schemas.py`.
- `agent/images.py` — image providers; `placeholder` is for testing. New providers go in `PROVIDERS`.
- `agent/fake.py` — canned answers used by `--dry-run`.
- `agent/web.py` + `agent/static/index.html` — local web UI (stdlib HTTP server, no framework). One run at a time; the page polls `/api/status`.

## Commands

- Setup: `scripts/setup.sh`
- Test without API keys: `.venv/bin/python -m agent run --dry-run`
- Real run: `.venv/bin/python -m agent run --count 3`
- Web UI: `.venv/bin/python -m agent serve` → http://127.0.0.1:8000

Always run the dry run after changing pipeline code.

## Content rules

The channel must stay monetizable, so keep these in prompts and code: original stories only, no claims that a story is real, no fake product reviews or unverifiable product claims, affiliate disclosure whenever a link is attached, and variety across clips (`output/history.json` feeds past titles back into idea generation).

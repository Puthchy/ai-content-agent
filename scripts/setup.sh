#!/usr/bin/env bash
# ติดตั้งครั้งแรก: สร้าง virtualenv, ลงไลบรารี, คัดลอก .env
set -euo pipefail
cd "$(dirname "$0")/.."

command -v ffmpeg >/dev/null || { echo "ต้องติดตั้ง ffmpeg ก่อน (macOS: brew install ffmpeg / Ubuntu: sudo apt install ffmpeg)"; exit 1; }

python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env

echo "ติดตั้งเสร็จ ลองรัน: .venv/bin/python -m agent run --dry-run"

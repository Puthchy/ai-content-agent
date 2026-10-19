"""Idea -> script -> voice -> images -> video -> caption, one folder per clip."""

import json
import random
import re
from datetime import datetime
from pathlib import Path

from . import images, tts, video
from .config import OUTPUT_DIR, Settings, render_prompt
from .schemas import Caption, IdeaList, Script

HISTORY_FILE = OUTPUT_DIR / "history.json"


def load_history() -> list[str]:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_history(titles: list[str]) -> None:
    HISTORY_FILE.write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify(text: str) -> str:
    return re.sub(r'[\s/\\:*?"<>|#.]+', "-", text).strip("-")[:40] or "clip"


class Pipeline:
    def __init__(self, settings: Settings, llm, log=print):
        self.s = settings
        self.llm = llm
        self.log = log

    def pick_idea(self, history: list[str]):
        c, ch = self.s.content, self.s.channel
        ideas = self.llm.ask(
            render_prompt(
                "ideas",
                count=c["ideas_per_run"],
                seconds=c["video_seconds"],
                history="\n".join(f"- {t}" for t in history[-50:]) or "- (ยังไม่มี)",
                categories="\n".join(f"- {p}" for p in ch.get("product_categories", [])) or "- (ไม่ทำ affiliate)",
            ),
            IdeaList,
        ).ideas
        best = max(ideas, key=lambda i: i.hook_score)
        use_product = bool(best.product_category) and random.random() < c["affiliate_ratio"]
        return best, best.product_category if use_product else ""

    def write_script(self, idea, product: str) -> Script:
        c = self.s.content
        script = self.llm.ask(
            render_prompt(
                "script",
                title=idea.title,
                angle=idea.angle,
                product=product or "ไม่มี",
                seconds=c["video_seconds"],
                words=int(c["video_seconds"] * 2.5),
                scenes=c["scenes"],
            ),
            Script,
        )
        if not script.scenes:
            raise RuntimeError("script came back with no scenes")
        return script

    def write_caption(self, script: Script, has_affiliate: bool) -> Caption:
        return self.llm.ask(
            render_prompt(
                "caption",
                title=script.title,
                narration=script.narration,
                has_affiliate="มี" if has_affiliate else "ไม่มี",
            ),
            Caption,
        )

    def make_clip(self) -> Path:
        history = load_history()
        idea, product = self.pick_idea(history)
        self.log(f"ไอเดีย: {idea.title} (hook {idea.hook_score}/10){' + สินค้า: ' + product if product else ''}")

        script = self.write_script(idea, product)
        clip_dir = OUTPUT_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{slugify(script.title)}"
        clip_dir.mkdir(parents=True)
        (clip_dir / "script.json").write_text(script.model_dump_json(indent=2), encoding="utf-8")
        self.log(f"สคริปต์: {len(script.scenes)} ฉาก")

        audio = tts.synthesize(
            script.narration, clip_dir / "voice.mp3", self.s.section("tts").get("provider", "auto"),
            self.s.elevenlabs_key, self.s.elevenlabs_voice, self.s.content["video_seconds"],
        )
        total = tts.duration(audio)
        self.log(f"เสียงพากย์: {total:.1f} วินาที")

        v = self.s.section("video")
        w, h = v.get("width", 1080), v.get("height", 1920)
        provider = self.s.section("images").get("provider", "placeholder")
        frames = [
            images.generate(scene.image_prompt, clip_dir / f"scene_{i:02}.png", provider, w, h)
            for i, scene in enumerate(script.scenes, 1)
        ]
        narrations = [scene.narration for scene in script.scenes]
        durations = video.scene_durations(narrations, total)
        video.write_srt(narrations, durations, clip_dir / "subtitles.srt")
        video.render(frames, durations, audio, clip_dir / "video.mp4", w, h)
        self.log("วิดีโอ: video.mp4 + subtitles.srt")

        links = self.s.affiliate_links if product else []
        caption = self.write_caption(script, bool(links))
        post = [caption.youtube_title, "", caption.caption, ""]
        if links:
            post += [caption.disclosure, *links, ""]
        post.append(" ".join(f"#{t.lstrip('#')}" for t in caption.hashtags))
        (clip_dir / "post.txt").write_text("\n".join(post) + "\n", encoding="utf-8")

        save_history(history + [script.title])
        self.log(f"เสร็จ: output/{clip_dir.name}")
        return clip_dir


def build_pipeline(settings: Settings, dry_run: bool, log=print) -> Pipeline:
    """Wire the real Claude client, or canned answers for a no-API-key test run."""
    if dry_run:
        from .fake import FakeLLM
        settings.raw.setdefault("tts", {})["provider"] = "none"
        settings.raw.setdefault("images", {})["provider"] = "placeholder"
        settings.raw["content"]["affiliate_ratio"] = 1.0
        return Pipeline(settings, FakeLLM(), log)
    if not settings.anthropic_key:
        raise RuntimeError("ยังไม่ได้ใส่ ANTHROPIC_API_KEY ใน .env (หรือใช้โหมดทดสอบ)")
    from .llm import LLM
    m = settings.section("model")
    llm = LLM(settings.anthropic_key, m.get("name", "claude-opus-5-5"),
              m.get("effort", "medium"), render_prompt("system", **settings.channel))
    return Pipeline(settings, llm, log)

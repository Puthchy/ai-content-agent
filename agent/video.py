"""Assemble scene images + narration into a vertical MP4 and an SRT for editing."""

import subprocess
from pathlib import Path


def _timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def scene_durations(narrations: list[str], total: float) -> list[float]:
    """Split the audio length across scenes in proportion to their text length."""
    weights = [max(len(n), 1) for n in narrations]
    return [total * w / sum(weights) for w in weights]


def write_srt(narrations: list[str], durations: list[float], out: Path) -> Path:
    lines, start = [], 0.0
    for i, (text, dur) in enumerate(zip(narrations, durations), 1):
        lines += [str(i), f"{_timestamp(start)} --> {_timestamp(start + dur)}", text, ""]
        start += dur
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def render(images: list[Path], durations: list[float], audio: Path, out: Path,
           width: int, height: int) -> Path:
    concat = out.with_suffix(".concat.txt")
    entries = [f"file '{img.resolve()}'\nduration {dur:.3f}" for img, dur in zip(images, durations)]
    # The concat demuxer ignores the last duration unless the final file is repeated.
    entries.append(f"file '{images[-1].resolve()}'")
    concat.write_text("\n".join(entries), encoding="utf-8")

    scale = (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
             f"crop={width}:{height},format=yuv420p")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(audio),
         "-vf", scale, "-r", "30", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(out)],
        check=True,
    )
    concat.unlink()
    return out

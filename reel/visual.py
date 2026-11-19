"""Draw and animate the portrait storyboard, then encode it with FFmpeg."""

from bisect import bisect_right
import json
import math
import random
import subprocess
import tempfile
from pathlib import Path

import cairocffi as cairo
import numpy as np
from scipy.io import wavfile

from .drawing import diamond, ellipse, label, panel, path, rgb, smooth, soft_glow
from .presenter import presenter

WIDTH, HEIGHT = 720, 1280
THEMES = {
    "ember": ("#261623", "#773834", "#e39551"),
    "teal": ("#132832", "#245251", "#94c8a8"),
    "indigo": ("#1b2240", "#3a4469", "#d7afe9"),
    "gold": ("#30251a", "#75562d", "#ffd386"),
}
MOTIFS = tuple(
    (
        rng.uniform(0, WIDTH),
        rng.uniform(0, HEIGHT),
        rng.uniform(0.9, 2.6),
        rng.uniform(0.4, 1.3),
    )
    for rng in (random.Random(seed) for seed in range(34))
)


def scenery(ctx, theme, time):
    dark, mid, accent = THEMES[theme]
    gradient = cairo.LinearGradient(0, 0, WIDTH, HEIGHT)
    for stop, fill in ((0, dark), (0.68, mid), (1, dark)):
        gradient.add_color_stop_rgb(stop, *rgb(fill))
    ctx.set_source(gradient)
    ctx.paint()
    center = WIDTH / 2 + 40 * math.sin(time * 0.7)
    soft_glow(ctx, center, 533, 500, accent, 0.6)

    for tier in range(3):
        phase = time * (5 + tier * 6)
        base = 815 + tier * 83
        ridge = [
            (x, base + 38 * math.sin((x + phase) / 122 + tier))
            for x in range(-40, WIDTH + 70, 36)
        ]
        path(
            ctx,
            [*ridge, (WIDTH + 40, HEIGHT), (-40, HEIGHT)],
            fill=dark,
            alpha=0.28 + 0.14 * tier,
            closed=True,
        )
    for x, y, size, speed in MOTIFS:
        px = (x + time * (speed * 13)) % WIDTH
        py = (y - time * (speed * 28)) % HEIGHT
        ellipse(ctx, px, py, size, size, accent, 0.18 + 0.12 * math.sin(x + time * 2))


def rings(ctx, x, y, accent, time, speed):
    for index in range(4):
        expansion = (time * speed + index * 0.25) % 1
        radius = 43 + expansion * 175
        ellipse(ctx, x, y, radius, radius, accent, 0.46 * (1 - expansion), stroke=1.8)
    for index in range(12):
        rotation = time * 0.3 + index * math.tau / 12
        diamond(
            ctx,
            x + 204 * math.cos(rotation),
            y + 204 * math.sin(rotation),
            2.8,
            5.5,
            accent,
            0.54,
        )


def paint(ctx, shot, caption, brand, time, length, elapsed, lip_open):
    scenery(ctx, shot["theme"], time)
    _, _, accent = THEMES[shot["theme"]]
    layout = shot["layout"]
    reveal = smooth(elapsed / min(0.68, max(0.1, length)))
    if layout == "hook":
        rings(ctx, 360, 459, accent, time, 1.06)
        presenter(ctx, 367, 671, 1.19 + 0.11 * reveal, time, lip_open, 0.8, -4)
        label(
            ctx, shot["title"] or "रुको!", 360, 268, 118 - round(12 * reveal), limit=610
        )
    elif layout == "speaker":
        presenter(
            ctx,
            350 + 14 * math.sin(time * 1.3),
            622,
            1.46,
            time,
            lip_open,
            0.42 + 0.4 * math.sin(elapsed * 2),
            0,
        )
        label(ctx, shot["title"], 360, 286, 64)
    elif layout == "story":
        rings(ctx, 405, 586, accent, time, 0.76)
        for index in range(3):
            x = 202 + 153 * index
            drop = 75 * (1 - smooth((elapsed - index * 0.10) / 0.5))
            diamond(ctx, x, 571 + drop, 22, 36, accent, 0.8)
            ellipse(ctx, x, 571 + drop, 44, 44, accent, 0.34, stroke=2)
        label(ctx, shot["title"], 360, 451 - 75 * reveal, 66)
    else:
        rings(ctx, 360, 530, accent, time, 0.48)
        presenter(ctx, 362, 626 + (1 - reveal) * 80, 1.08, time, lip_open, 0.26, 2)
        label(ctx, shot["title"] or brand, 360, 868, 61)

    label(ctx, brand.upper(), 360, 142, 21, accent, 460)
    if caption:
        panel(ctx, 57, 957, 606, 102, 21, "#181621", 0.94)
        label(ctx, caption, 360, 1008, 49, limit=552)

    fraction = min(1, elapsed / length)
    path(ctx, [(68, 1085), (652, 1085)], stroke="#232332", width=4)
    if fraction:
        path(ctx, [(68, 1085), (68 + 584 * fraction, 1085)], stroke=accent, width=4)


def render(build, output, preview=False):
    timing = json.loads((build / "timing.json").read_text(encoding="utf-8"))
    shots, captions = timing["shots"], timing["captions"]
    shot_starts = [shot["start"] for shot in shots]
    caption_starts = [cue["start"] for cue in captions]
    sample_rate, voice = wavfile.read(build / "narration.wav")
    width, height = (540, 960) if preview else (1080, 1920)
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    ctx = cairo.Context(surface)
    ctx.scale(width / WIDTH, height / HEIGHT)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        staging = Path(directory) / "reel.mp4"
        command = [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pixel_format",
            "bgr0",
            "-video_size",
            f"{width}x{height}",
            "-framerate",
            str(timing["fps"]),
            "-i",
            "-",
            "-i",
            str(build / "mix.wav"),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(staging),
        ]
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
            try:
                for frame in range(timing["frames"]):
                    time = frame / timing["fps"]
                    index = bisect_right(shot_starts, time) - 1
                    stop = (
                        shot_starts[index + 1]
                        if index + 1 < len(shots)
                        else timing["duration"]
                    )
                    elapsed = time - shot_starts[index]
                    cue_index = bisect_right(caption_starts, time) - 1
                    cue = captions[cue_index] if cue_index >= 0 else None
                    caption = cue["text"] if cue and time < cue["end"] else ""
                    offset = round(time * sample_rate)
                    window = voice[offset : offset + round(sample_rate / timing["fps"])]
                    lip_open = min(1.0, float(np.sqrt(np.mean(window**2))) * 9)
                    paint(
                        ctx,
                        shots[index],
                        caption,
                        timing["brand"],
                        time,
                        stop - shot_starts[index],
                        elapsed,
                        lip_open,
                    )
                    surface.flush()
                    encoder.stdin.write(surface.get_data())
            finally:
                encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("FFmpeg could not encode the reel.")
        staging.replace(output)

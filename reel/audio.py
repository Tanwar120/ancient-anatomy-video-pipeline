"""Clean and mix the narration while preserving its caption timebase."""

import json
import math
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d
from scipy.signal import resample_poly

from .project import recorded_take, scene_takes

SAMPLE_RATE = 48_000
FPS = 30


def trim_take(path):
    rate, raw = wavfile.read(path)
    samples = raw.astype(np.float64)
    if raw.dtype.kind in "iu":
        info = np.iinfo(raw.dtype)
        if raw.dtype.kind == "u":
            midpoint = (info.max + 1) / 2
            samples = (samples - midpoint) / midpoint
        else:
            samples /= -float(info.min)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if not samples.size:
        raise ValueError(f"Empty take {path}")
    envelope = np.sqrt(
        np.maximum(0, uniform_filter1d(samples**2, max(1, round(rate * 0.012))))
    )
    audible = np.flatnonzero(envelope > max(0.0012, 0.008 * envelope.max()))
    if not audible.size:
        raise ValueError(f"No audible speech in {path}")
    start = max(0, audible[0] - round(rate * 0.055))
    end = min(len(samples), audible[-1] + round(rate * 0.078) + 1)
    take = samples[start:end].copy()

    quiet = envelope[start:end] < 0.0023
    edges = np.flatnonzero(np.diff(quiet.astype(np.int8), prepend=0, append=0))
    cuts, fragments = [], []
    previous = 0
    for left, right in zip(edges[::2], edges[1::2]):
        if right - left < rate * 0.50 or left == 0 or right == len(take):
            continue
        before = left + round(rate * 0.125)
        after = right - round(rate * 0.132)
        overlap = max(1, round(rate * 0.012))
        blend = np.linspace(0, 1, overlap)
        cuts.append((before, after))
        fragments.extend(
            (
                take[previous:before],
                take[before : before + overlap] * (1 - blend)
                + take[after : after + overlap] * blend,
            )
        )
        previous = after + overlap
    take = np.concatenate([*fragments, take[previous:]])

    fade = min(len(take) // 2, round(rate * 0.007))
    if fade:
        edge = np.linspace(0, 1, fade)
        take[:fade] *= edge
        take[-fade:] *= edge[::-1]

    def map_time(seconds):
        position = seconds * rate - start
        deleted = sum(max(0, min(position, right) - left) for left, right in cuts)
        return max(0, min(len(take), position - deleted)) / rate

    return resample_poly(take, SAMPLE_RATE, rate), map_time


def caption_cues(line, words, start, stop, map_time):
    cues = []
    for index in range(0, len(words), 5):
        group = words[index : index + 5]
        begin = start if index == 0 else start + map_time(group[0]["offset"] * 1e-7)
        next_index = index + len(group)
        end = (
            stop
            if next_index == len(words)
            else start + map_time(words[next_index]["offset"] * 1e-7)
        )
        if end > begin:
            caption = (
                line if len(words) <= 5 else " ".join(word["text"] for word in group)
            )
            cues.append({"start": begin, "end": end, "text": caption})
    return cues or [{"start": start, "end": stop, "text": line}]


def build_audio(story, build, music=None):
    build.mkdir(parents=True, exist_ok=True)
    shots, captions, pieces = [], [], []
    cursor = round(0.012 * SAMPLE_RATE)
    for scene in story["scenes"]:
        shots.append({**scene, "start": max(0, (cursor / SAMPLE_RATE) - 0.035)})
        for index, (line, _, destination) in enumerate(
            scene_takes(story, scene, build)
        ):
            path = recorded_take(destination)
            if path is None:
                raise ValueError(
                    f"Missing audio or word timings for {line!r}. Run "
                    "`python -m reel record` with the same story and build directory first."
                )
            take, map_time = trim_take(path.with_suffix(".wav"))
            words = [
                json.loads(row)
                for row in path.with_suffix(".jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            start, stop = cursor / SAMPLE_RATE, (cursor + len(take)) / SAMPLE_RATE
            captions.extend(caption_cues(line, words, start, stop + 0.045, map_time))
            pieces.append((cursor, take))
            first_take = len(shots) == 1 and index == 0
            cursor += len(take) + round((0.055 if first_take else 0.095) * SAMPLE_RATE)

    frames = math.ceil((cursor / SAMPLE_RATE + 0.175) * FPS)
    duration = frames / FPS
    narration = np.zeros(round(duration * SAMPLE_RATE), dtype=np.float32)
    for offset, take in pieces:
        narration[offset : offset + len(take)] = take
    voice_path = build / "narration.wav"
    wavfile.write(voice_path, SAMPLE_RATE, narration)

    ffmpeg = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(voice_path)]
    voice = (
        "highpass=f=52,acompressor=threshold=0.19:ratio=2:attack=12:release=130"
        ":makeup=1,pan=stereo|FL=c0|FR=c0"
    )
    normalize = "loudnorm=I=-17:TP=-5:LRA=9,aresample=48000"
    if music:
        ffmpeg += [
            "-stream_loop",
            "-1",
            "-i",
            str(music),
            "-filter_complex",
            f"[0:a]{voice}[v];[1:a]aformat=channel_layouts=stereo,volume=0.09,"
            f"atrim=duration={duration},afade=t=out:st={max(0, duration - 0.48)}:d=0.48[bed];"
            f"[v][bed]amix=inputs=2:normalize=0:duration=first,{normalize}[a]",
            "-map",
            "[a]",
        ]
    else:
        ffmpeg += ["-af", f"{voice},{normalize}"]
    subprocess.run([*ffmpeg, "-c:a", "pcm_s24le", str(build / "mix.wav")], check=True)

    timing = {
        "fps": FPS,
        "frames": frames,
        "duration": duration,
        "shots": shots,
        "captions": captions,
        "brand": story["brand"],
    }
    (build / "timing.json").write_text(
        json.dumps(timing, indent=2, ensure_ascii=False), encoding="utf-8"
    )

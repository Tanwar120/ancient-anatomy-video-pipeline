"""Record Edge TTS voice takes with service-supplied word boundaries."""

import asyncio
from pathlib import Path
import shutil
import subprocess
import tempfile

from .project import recorded_take, scene_takes


async def record_story(story, build):
    jobs = {
        path: (line, rate)
        for scene in story["scenes"]
        for line, rate, path in scene_takes(story, scene, build)
    }
    voice_cache = build / "voice"
    voice_cache.mkdir(parents=True, exist_ok=True)
    limit = asyncio.Semaphore(3)

    async def run(path, line, rate):
        wave, words = path.with_suffix(".wav"), path.with_suffix(".jsonl")
        existing = recorded_take(path)
        if existing == path:
            return
        async with limit:
            with tempfile.TemporaryDirectory(dir=voice_cache) as temp:
                take = Path(temp) / "take"
                if existing is None:
                    await synthesize(line, story["voice"], rate, take)
                else:
                    for ext in (".wav", ".jsonl"):
                        shutil.copyfile(
                            existing.with_suffix(ext), take.with_suffix(ext)
                        )
                # Repair an interrupted take first; add the missing half last.
                destinations = (wave, words) if wave.exists() else (words, wave)
                for dest in destinations:
                    take.with_suffix(dest.suffix).replace(dest)

    await asyncio.gather(*(run(path, *values) for path, values in jobs.items()))


async def synthesize(line, voice, rate, take):
    import edge_tts

    settings = edge_tts.Communicate(line, voice, rate=rate, boundary="WordBoundary")
    await settings.save(str(take.with_suffix(".mp3")), str(take.with_suffix(".jsonl")))
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(take.with_suffix(".mp3")),
            "-c:a",
            "pcm_f32le",
            str(take.with_suffix(".wav")),
        ],
        check=True,
    )

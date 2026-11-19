"""Record Edge TTS voice takes with service-supplied word boundaries."""

import asyncio
from pathlib import Path
import subprocess
import tempfile

from .project import scene_takes


async def record_story(story, build):
    import edge_tts

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
        if wave.is_file() and words.is_file():
            return
        async with limit:
            with tempfile.TemporaryDirectory(dir=voice_cache) as temp:
                settings = edge_tts.Communicate(
                    line, story["voice"], rate=rate, boundary="WordBoundary"
                )
                take = Path(temp) / "take"
                await settings.save(
                    str(take.with_suffix(".mp3")), str(take.with_suffix(".jsonl"))
                )
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
                take.with_suffix(".jsonl").replace(words)
                take.with_suffix(".wav").replace(wave)

    await asyncio.gather(*(run(path, *values) for path, values in jobs.items()))

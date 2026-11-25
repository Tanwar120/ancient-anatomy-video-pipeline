import asyncio
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from scipy.io import wavfile

from reel.audio import build_audio, trim_take
from reel.project import load_story, scene_takes
from reel.record import record_story

PROJECT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_remove_padding_and_long_gap_but_keep_words(self):
        rate = 24000
        time = np.arange(rate // 4) / rate
        word = 0.24 * np.sin(2 * np.pi * 350 * time)
        raw = np.concatenate(
            [np.zeros(rate // 3), word, np.zeros(rate), word, np.zeros(rate // 2)]
        )
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "line.wav"
            wavfile.write(file, rate, raw.astype("float32"))
            samples, transform = trim_take(file)
        self.assertTrue(0.65 < len(samples) / 48000 < 1.05)
        second = transform(1 / 3 + 0.25 + 1)
        self.assertTrue(0.40 < second < 0.70)
        self.assertLess(abs(samples[0]), 1e-6)
        self.assertLess(abs(samples[-1]), 1e-6)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required for music mixing")
    def test_music_bed_loops_and_mix_stays_aligned(self):
        story = {
            "brand": "Example",
            "voice": "hi-IN-MadhurNeural",
            "rate": "+0%",
            "hook_rate": "+18%",
            "scenes": [{"id": "hook", "layout": "hook", "lines": ["रुको!"]}],
        }
        rate = 48000
        time = np.arange(rate) / rate
        signal = (0.16 * np.sin(2 * np.pi * 300 * time)).astype("float32")
        with tempfile.TemporaryDirectory() as d:
            build = Path(d)
            _, _, take = next(scene_takes(story, story["scenes"][0], build))
            take.parent.mkdir()
            wavfile.write(take.with_suffix(".wav"), rate, signal)
            take.with_suffix(".jsonl").touch()
            bed = build / "bed.wav"
            wavfile.write(bed, rate, signal[: rate // 3] * 0.2)

            build_audio(story, build, bed)

            mix_rate, mix = wavfile.read(build / "mix.wav")
            _, voice = wavfile.read(build / "narration.wav")
            self.assertEqual(mix_rate, rate)
            self.assertEqual(mix.shape, (len(voice), 2))

    def test_validate_generic_story(self):
        story = load_story(PROJECT / "story.example.json")
        self.assertEqual(story["scenes"][0]["layout"], "hook")

    def test_record_example_offline_and_preserve_cached_takes(self):
        story = load_story(PROJECT / "story.example.json")
        with (
            tempfile.TemporaryDirectory() as d,
            patch.dict(sys.modules, {"edge_tts": None}),
        ):
            build = Path(d)
            takes = [
                p
                for scene in story["scenes"]
                for _, _, p in scene_takes(story, scene, build)
            ]
            takes[0].parent.mkdir()
            takes[0].with_suffix(".wav").write_bytes(b"custom take")
            takes[0].with_suffix(".jsonl").touch()
            takes[1].with_suffix(".wav").write_bytes(b"interrupted recording")
            asyncio.run(record_story(story, build))
            self.assertEqual(takes[0].with_suffix(".wav").read_bytes(), b"custom take")
            for take in takes[1:]:
                for ext in (".wav", ".jsonl"):
                    name = take.with_suffix(ext).name
                    self.assertEqual(
                        (take.parent / name).read_bytes(),
                        (PROJECT / "audio" / "voice" / name).read_bytes(),
                    )

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required for mixing")
    def test_audio_step_reads_example_without_recording(self):
        story = load_story(PROJECT / "story.example.json")
        with tempfile.TemporaryDirectory() as d:
            build = Path(d)
            build_audio(story, build)
            _, voice = wavfile.read(build / "narration.wav")
            self.assertGreater(np.max(np.abs(voice)), 0.01)

    def test_custom_line_requests_tts_and_unrecorded_audio_explains_next_step(self):
        story = load_story(PROJECT / "story.example.json")
        line = "This is an unbundled line."
        story["scenes"][0]["lines"] = [line]
        voice_service = Mock()
        voice_service.Communicate.side_effect = RuntimeError("Reached online recorder")
        with (
            tempfile.TemporaryDirectory() as d,
            patch.dict(sys.modules, {"edge_tts": voice_service}),
        ):
            build = Path(d)
            with self.assertRaisesRegex(RuntimeError, "Reached online recorder"):
                asyncio.run(record_story(story, build))
            voice_service.Communicate.assert_called_once_with(
                line, story["voice"], rate=story["hook_rate"], boundary="WordBoundary"
            )
            with self.assertRaisesRegex(ValueError, "python -m reel record"):
                build_audio(story, build)


if __name__ == "__main__":
    unittest.main()

import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from reel.audio import build_audio, trim_take
from reel.project import load_story, scene_takes


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
        project = Path(__file__).resolve().parents[1]
        story = load_story(project / "story.example.json")
        self.assertEqual(story["scenes"][0]["layout"], "hook")


if __name__ == "__main__":
    unittest.main()

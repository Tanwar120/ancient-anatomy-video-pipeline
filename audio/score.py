"""Synthesize the original Angoothi Ya Ramkatha music stem for the reel mixer."""

import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 48_000
FRAMES = 616
FPS = 30
MUSIC_GAIN = 0.09  # Applied by reel.audio when --music is supplied.

# (Start in seconds, MIDI pitch, level in the original mix, right pan, duration)
NOTES = [
    # The two choices and the invitation to lock in an answer.
    (0.045000, 69, 0.041, 0.62, 0.85),
    (0.654771, 62, 0.031, 0.43, 0.76),
    (3.546478, 57, 0.022, 0.50, 0.55),
    # Valmiki: a two-note answer for the story, a high pluck for the ring.
    (4.430312, 50, 0.034, 0.44, 0.96),
    (6.768229, 57, 0.018, 0.50, 0.68),
    (8.410395, 62, 0.031, 0.43, 0.74),
    (8.620395, 65, 0.024, 0.53, 0.80),
    (9.583437, 69, 0.043, 0.62, 1.05),
    # Tulsidas: the same two motifs in reverse order.
    (11.138854, 50, 0.033, 0.45, 0.85),
    (13.907937, 69, 0.042, 0.62, 0.70),
    (14.506646, 57, 0.021, 0.52, 0.72),
    (15.260979, 62, 0.031, 0.43, 0.74),
    (15.470979, 65, 0.024, 0.53, 0.80),
    # Closing question.
    (17.596479, 57, 0.026, 0.49, 0.68),
    (17.831479, 62, 0.018, 0.51, 1.00),
]


def write_score(output):
    music = np.zeros((FRAMES * SAMPLE_RATE // FPS, 2))
    for start, pitch, level, pan, duration in NOTES:
        offset = round(start * SAMPLE_RATE)
        count = round(duration * SAMPLE_RATE)
        samples = np.arange(count)
        t = samples / SAMPLE_RATE
        phase = 2 * np.pi * 440 * 2 ** ((pitch - 69) / 12) * t
        tone = (
            np.sin(phase)
            + 0.31 * np.sin(2.004 * phase) * np.exp(-6 * t)
            + 0.13 * np.sin(3.002 * phase) * np.exp(-10 * t)
        )
        attack = np.minimum(1, t / 0.011)
        release = np.minimum(1, (count - samples) / (0.07 * SAMPLE_RATE))
        note = level * tone * (attack * np.exp(-4.5 * t) * release)
        music[offset : offset + count] += note[:, None] * np.sqrt([1 - pan, pan])

    pcm = np.rint(music.astype(np.float32) / MUSIC_GAIN * 32768)
    output.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(output, SAMPLE_RATE, np.clip(pcm, -32768, 32767).astype(np.int16))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Destination for the stereo PCM WAV.")
    write_score(parser.parse_args().output)

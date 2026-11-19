"""Check the encoded portrait file before delivery."""

from fractions import Fraction
import json
import subprocess


def verify(build, output):
    timing = json.loads((build / "timing.json").read_text(encoding="utf-8"))
    info = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(info.stdout)
    streams = {stream["codec_type"]: stream for stream in metadata["streams"]}
    video, audio = streams.get("video", {}), streams.get("audio", {})
    size = (video.get("width"), video.get("height"))
    if size not in ((540, 960), (1080, 1920)) or video.get("codec_name") != "h264":
        raise ValueError("Expected a supported 9:16 H.264 stream.")
    if Fraction(video["avg_frame_rate"]) != timing["fps"]:
        raise ValueError("Unexpected frame rate.")
    if audio.get("codec_name") != "aac" or audio.get("sample_rate") != "48000":
        raise ValueError("Expected 48 kHz AAC narration.")
    duration = float(metadata["format"]["duration"])
    if abs(duration - timing["duration"]) > 0.07:
        raise ValueError("Audio and video durations differ from the storyboard.")
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(output),
            "-f",
            "null",
            "-",
        ],
        check=True,
    )
    print(
        f"Verified full decode at {size[0]}×{size[1]}, {timing['fps']} fps, {duration:.2f}s."
    )

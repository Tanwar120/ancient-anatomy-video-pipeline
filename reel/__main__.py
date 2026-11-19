"""Run the Ancient Anatomy reel pipeline."""

import argparse
import asyncio
from pathlib import Path
import subprocess
import sys

from .project import load_story


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["all", "record", "audio", "render", "verify"])
    parser.add_argument("story", type=Path, help="Path to the JSON storyboard.")
    parser.add_argument("--build", type=Path, default=Path("build"))
    parser.add_argument(
        "--music", type=Path, help="Optional local music bed for the audio step."
    )
    parser.add_argument(
        "--output", type=Path, help="MP4 destination (default: BUILD/reel.mp4)."
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Render at 540 by 960 instead of 1080 by 1920.",
    )
    args = parser.parse_args()
    output = args.output or (args.build / "reel.mp4")
    try:
        story = load_story(args.story)
        if args.step in ("record", "all"):
            from .record import record_story

            asyncio.run(record_story(story, args.build))
            print(f"Voice takes ready in {args.build / 'voice'}.", flush=True)
        if args.step in ("audio", "all"):
            from .audio import build_audio

            build_audio(story, args.build, args.music)
            print(f"Audio ready at {args.build / 'mix.wav'}.", flush=True)
        if args.step in ("render", "all"):
            from .visual import render

            render(args.build, output, args.preview)
            print(f"Rendered {output}.", flush=True)
        if args.step in ("verify", "all"):
            from .verify import verify

            verify(args.build, output)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Reel pipeline: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

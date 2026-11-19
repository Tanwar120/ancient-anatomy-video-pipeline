# Ancient Anatomy Video Pipeline

The reusable workflow for building portrait reels with a Madhur voiceover, animated scenes, synchronized Hindi captions, and an optional music bed. Start with the sample storyboard, then add scene layouts for the action your story needs.

## Setup on macOS

Install Python 3.11 or newer, FFmpeg with libx264, and Cairo. The renderer uses the macOS Devanagari Sangam MN font and Pillow's RAQM text shaping.

```sh
brew install ffmpeg cairo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

To use another local Devanagari font, set `REEL_DEVANAGARI_FONT` to its file path and optionally `REEL_FONT_INDEX` to its font collection index. The font needs Latin glyphs for mixed-script captions. The system font stays on your machine.

## Make a reel

```sh
mkdir -p local
cp story.example.json local/story.json
python -m reel all local/story.json --build build/episode
```

The finished 1080 × 1920, 30 fps MP4 is at `build/episode/reel.mp4`. Add `--preview` for a faster 540 × 960 draft or `--output PATH` to choose a destination. To add music, pass `--music local/music.wav` with a track you have permission to use.

Edit the storyboard to set the brand, scene order, palette, on-screen titles, and spoken lines. Devanagari spelling of Hinglish terms can help the Hindi voice pronounce them the way you want. For a visible and audible opening, put `रुको!` in the hook title and in the first spoken line.

| Layout | Animation |
| --- | --- |
| `hook` | Large title on frame one, fast camera push, raised hand and expanding rings |
| `speaker` | Moving illustrated presenter, speech-driven mouth, blinks and hand gestures |
| `story` | Animated title reveal with moving foreground and background layers |
| `close` | Animated presenter and closing title |

Available palettes are `ember`, `teal`, `indigo`, and `gold`. The base scene renderer is in `reel/visual.py`, with character poses in `reel/presenter.py`. Add custom scene actions there for stories that need new characters, props, or reveals. The editable SVG art and the PNG layers used by Cairo live in `reel/art/`.

## Voice and mix

- **Recording** uses `hi-IN-MadhurNeural` through Edge TTS at `+0%`, with a configurable `+18%` for the opening line. The service receives only the spoken lines during this step. Takes are cached by text, voice, and rate and can be reused offline.
- **Cleanup** retains 55 ms of leading room and 78 ms of trailing room when available. It shortens internal silences of at least 500 ms to about 250 ms with a 12 ms crossfade, fades take edges over 7 ms, and leaves approximately 95 ms between takes, or 55 ms after the first hook line.
- **Mix** uses a 52 Hz high-pass filter, gentle 2:1 compression, and optional low-level music. FFmpeg targets −17 LUFS and −5 dBTP and outputs 48 kHz audio.
- **Timing** remaps the voice service's word boundaries after editing the pauses. The renderer uses these times for captions and the narration amplitude for mouth motion.

For an edit, rerun `all` with the same build folder to reuse unaffected voice takes. The steps can also run individually, in order, using the same storyboard and build folder.

```sh
python -m reel record local/story.json --build build/episode
python -m reel audio local/story.json --build build/episode
python -m reel render local/story.json --build build/episode
python -m reel verify local/story.json --build build/episode
python -m unittest discover -s tests
```

Verification checks codecs, dimensions, frame rate, duration, and full decode. Watch the phone-size preview and listen to the exported voice for pronunciation, pacing, and balance before posting.

# Ancient Anatomy Video Pipeline

The reusable workflow for building portrait reels with a Madhur voiceover, animated scenes, synchronized Hindi captions, and an optional music bed. Start with the sample storyboard, then add scene layouts for the action your story needs.

## Download the audio

These tracks are from the 20.53-second Hanuman reel *Angoothi Ya Ramkatha*. The two WAV tracks start at the same point and can be imported into separate tracks in a video editor.

| File | What you get |
| --- | --- |
| [Madhur voiceover (WAV)](audio/hanuman-madhur.wav) | Edited Hinglish narration on its own, 48 kHz mono |
| [Original background music (WAV)](audio/hanuman-music.wav) | The ring pluck and Ramkatha melody, 48 kHz stereo. For the original balance, set this track to 9% gain (about −21 dB) before mastering. The pipeline applies that gain with `--music`. |
| [Listen to the finished mix (MP3)](audio/hanuman-mix.mp3) | Voice and music together at the reel's final level |

The [music score](audio/score.py) generates the background track. To recreate the WAV after setup, run `python audio/score.py build/hanuman-music.wav`. The [six original narration takes and word timings](audio/voice/) go with [the example storyboard](story.example.json).

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
python -m reel all local/story.json --build build/episode --music audio/hanuman-music.wav
```

The finished 1080 × 1920, 30 fps MP4 is at `build/episode/reel.mp4`. The unedited example runs offline after setup. Add `--preview` for a faster 540 × 960 draft or `--output PATH` to choose a destination. Omit `--music` for voice only, or supply your own track.

Edit the storyboard to set the brand, scene order, palette, on-screen titles, and spoken lines. Devanagari spelling of Hinglish terms can help the Hindi voice pronounce them the way you want. For a visible and audible opening, put `रुको!` in the hook title and in the first spoken line.

| Layout | Animation |
| --- | --- |
| `hook` | Large title on frame one, fast camera push, raised hand and expanding rings |
| `speaker` | Moving illustrated presenter, speech-driven mouth, blinks and hand gestures |
| `story` | Animated title reveal with moving foreground and background layers |
| `close` | Animated presenter and closing title |

Available palettes are `ember`, `teal`, `indigo`, and `gold`. The base scene renderer is in `reel/visual.py`, with character poses in `reel/presenter.py`. Add custom scene actions there for stories that need new characters, props, or reveals. The editable SVG art and the PNG layers used by Cairo live in `reel/art/`.

## Voice and mix

- **Recording new lines** uses Microsoft's hosted `hi-IN-MadhurNeural` voice through [edge-tts](https://github.com/rany2/edge-tts). Run `record` or `all` with an internet connection on the first run for a new line, voice or rate. The recorder sends the line and voice settings to the service and saves its WAV and word timings locally. It uses the existing build cache first, then matching recordings included in the repo. No API key is needed. The example uses `+0%` with a configurable `+18%` for its opening line.
- **Cleanup** retains 55 ms of leading room and 78 ms of trailing room when available. It shortens internal silences of at least 500 ms to about 250 ms with a 12 ms crossfade, fades take edges over 7 ms, and leaves approximately 95 ms between takes, or 55 ms after the first hook line.
- **Mix** uses a 52 Hz high-pass filter, gentle 2:1 compression, and optional low-level music. FFmpeg targets −17 LUFS and −5 dBTP and outputs 48 kHz audio.
- **Timing** remaps the voice service's word boundaries after editing the pauses. The renderer uses these times for captions and the narration amplitude for mouth motion.

For an edit, rerun `all` with the same build folder to reuse unaffected voice takes. The steps can also run individually, in order, using the same storyboard and build folder.

```sh
python -m reel record local/story.json --build build/episode
python -m reel audio local/story.json --build build/episode --music audio/hanuman-music.wav
python -m reel render local/story.json --build build/episode
python -m reel verify local/story.json --build build/episode
python -m unittest discover -s tests
```

`audio` writes the dry voice to `build/episode/narration.wav`, the mastered stereo track to `build/episode/mix.wav`, and caption timings to `build/episode/timing.json`. You can run it directly on the example from a fresh checkout.

Verification checks codecs, dimensions, frame rate, duration, and full decode. Watch the phone-size preview and listen to the exported voice for pronunciation, pacing, and balance before posting.

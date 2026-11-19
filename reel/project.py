"""Read a reel storyboard and identify its voice takes."""

import hashlib
import json
import re

LAYOUTS = {"hook", "speaker", "story", "close"}
THEMES = {"ember", "teal", "indigo", "gold"}
RATE = re.compile(r"[+-]\d+%")


def load_story(path):
    story = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(story, dict) or not isinstance(story.get("scenes"), list):
        raise ValueError("The storyboard must contain a scenes list.")
    scenes = story["scenes"]
    if not scenes or any(not isinstance(scene, dict) for scene in scenes):
        raise ValueError("Provide at least one scene object.")
    if scenes[0].get("layout") != "hook":
        raise ValueError("The first scene must use the hook layout.")
    for key, default in (
        ("brand", "Ancient Anatomy"),
        ("voice", "hi-IN-MadhurNeural"),
        ("rate", "+0%"),
        ("hook_rate", "+18%"),
    ):
        if (
            not isinstance(story.setdefault(key, default), str)
            or not story[key].strip()
        ):
            raise ValueError(f"{key} must be a nonempty string.")
    for key in ("rate", "hook_rate"):
        if not RATE.fullmatch(story[key]):
            raise ValueError(f"{key} must be a signed percentage like +0%.")
    ids = set()
    for scene in scenes:
        name = scene.get("id")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
            raise ValueError(
                "Scene IDs must use lowercase letters, numbers, underscores or hyphens."
            )
        if name in ids:
            raise ValueError(f"Duplicate scene ID {name}.")
        ids.add(name)
        if (
            scene.get("layout") not in LAYOUTS
            or scene.setdefault("theme", "ember") not in THEMES
        ):
            raise ValueError(f"Unknown layout or theme in {name}.")
        if not isinstance(scene.setdefault("title", ""), str):
            raise ValueError(f"The title in {name} must be text.")
        lines = scene.get("lines")
        if (
            not isinstance(lines, list)
            or not lines
            or not all(isinstance(line, str) and line.strip() for line in lines)
        ):
            raise ValueError(f"{name} must have nonempty narration lines.")
    return story


def scene_takes(story, scene, build):
    for index, line in enumerate(scene["lines"]):
        rate = (
            story["hook_rate"]
            if scene is story["scenes"][0] and index == 0
            else story["rate"]
        )
        identity = json.dumps([line, story["voice"], rate], ensure_ascii=False)
        key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        yield line, rate, build / "voice" / key

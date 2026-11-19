"""Cairo drawing helpers and shaped Hindi text."""

from functools import lru_cache
from io import BytesIO
import math
import os
from pathlib import Path

import cairocffi as cairo
from PIL import Image, ImageDraw, ImageFont, features

ART = Path(__file__).with_name("art")
MAC_DEVANAGARI = "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"


def smooth(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)


def rgb(value):
    return tuple(int(value[index : index + 2], 16) / 255 for index in (1, 3, 5))


def color(ctx, value, alpha=1):
    ctx.set_source_rgba(*rgb(value), alpha)


def path(ctx, points, fill=None, stroke=None, width=2, alpha=1, closed=False):
    ctx.new_path()
    ctx.move_to(*points[0])
    for point in points[1:]:
        if len(point) == 2:
            ctx.line_to(*point)
        else:
            ctx.curve_to(*point)
    if closed:
        ctx.close_path()
    if fill:
        color(ctx, fill, alpha)
        if stroke:
            ctx.fill_preserve()
        else:
            ctx.fill()
    if stroke:
        color(ctx, stroke, alpha)
        ctx.set_line_width(width)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def diamond(ctx, x, y, rx, ry, fill, alpha=1):
    path(
        ctx,
        [(x, y - ry), (x + rx, y), (x, y + ry), (x - rx, y)],
        fill=fill,
        alpha=alpha,
        closed=True,
    )


def ellipse(ctx, x, y, rx, ry, fill, alpha=1, stroke=0):
    ctx.new_sub_path()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, math.tau)
    ctx.restore()
    color(ctx, fill, alpha)
    if stroke:
        ctx.set_line_width(stroke)
        ctx.stroke()
    else:
        ctx.fill()


def panel(ctx, x, y, width, height, radius, fill, alpha=1):
    ctx.new_sub_path()
    for ix, iy, start in (
        (x + width - radius, y + radius, -0.5),
        (x + width - radius, y + height - radius, 0),
        (x + radius, y + height - radius, 0.5),
        (x + radius, y + radius, 1),
    ):
        ctx.arc(ix, iy, radius, start * math.pi, (start + 0.5) * math.pi)
    ctx.close_path()
    color(ctx, fill, alpha)
    ctx.fill()


def soft_glow(ctx, x, y, radius, tint, alpha):
    gradient = cairo.RadialGradient(x, y, 0, x, y, radius)
    gradient.add_color_stop_rgba(0, *rgb(tint), alpha)
    gradient.add_color_stop_rgba(1, *rgb(tint), 0)
    ctx.set_source(gradient)
    ctx.rectangle(x - radius, y - radius, radius * 2, radius * 2)
    ctx.fill()


@lru_cache
def asset(name):
    return cairo.ImageSurface.create_from_png(str(ART / f"{name}.png"))


def draw_surface(ctx, surface, x, y, width, height, alpha=1):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(width / surface.get_width(), height / surface.get_height())
    ctx.set_source_surface(surface)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def sprite(ctx, name, x, y, scale=1, angle=0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)
    ctx.rotate(math.radians(angle))
    draw_surface(ctx, asset(name), -153, -153, 306, 306)
    ctx.restore()


@lru_cache(maxsize=64)
def font(size):
    if not features.check_feature("raqm"):
        raise RuntimeError("Install Pillow with RAQM support for Devanagari shaping.")
    custom = os.environ.get("REEL_DEVANAGARI_FONT")
    path = custom or MAC_DEVANAGARI
    index = int(os.environ.get("REEL_FONT_INDEX", 0 if custom else 1))
    try:
        return ImageFont.truetype(
            path, size, index=index, layout_engine=ImageFont.Layout.RAQM
        )
    except OSError as exc:
        raise RuntimeError(
            f"Could not open {path}. Set REEL_DEVANAGARI_FONT to a local font."
        ) from exc


@lru_cache(maxsize=256)
def label_surface(words, size, fill):
    face = font(size * 2)
    left, top, right, bottom = face.getbbox(words)
    canvas = Image.new("RGBA", (right - left + 16, bottom - top + 16))
    ImageDraw.Draw(canvas).text((8 - left, 8 - top), words, fill=fill, font=face)
    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)
    return cairo.ImageSurface.create_from_png(buffer)


def label(ctx, words, x, y, size, fill="#fff0d5", limit=630):
    if not words.strip():
        return
    layer = label_surface(words, size, fill)
    width = min(limit, layer.get_width() / 2)
    height = layer.get_height() * width / layer.get_width()
    draw_surface(ctx, layer, x - width / 2, y - height / 2, width, height)

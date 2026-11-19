"""Articulated Hanuman presenter shared by the animated scene layouts."""

import math

from .drawing import (
    path,
    smooth,
    soft_glow,
    sprite,
    ellipse,
    diamond,
    draw_surface,
    asset,
)

GOLD = "#efc783"
INK = "#392737"
SKIN = "#dd916a"


def curve(c, points, color, width):
    path(c, points, stroke=color, width=width)


def limb(c, points, thickness, fill=SKIN):
    curve(c, points, INK, thickness + 4)
    curve(c, points, fill, thickness)


def presenter(c, x, y, scale, t, lips=0, finger=0, tilt=0):
    c.save()
    c.translate(x, y + 1.6 * math.sin(t * 2))
    c.scale(scale, scale)
    soft_glow(c, 0, -45, 195, "#ffcf78", 0.32)
    sprite(c, "halo", 0, -34, 1.04, 0.9 * t)
    limb(
        c,
        [
            (-36, 154),
            (-109, 178, -136, 104, -152, 40),
            (-169, -27, -164, -61, -189, -69),
            (-213, -76, -224, -46, -202, -41),
        ],
        10,
    )
    path(
        c,
        [
            (-70, 125),
            (8, 106, 62, 119, 80, 145),
            (96, 185, 101, 231, 105, 286),
            (48, 303, 8, 281, -5, 294),
            (-46, 301, -75, 281, -92, 272),
            (-85, 215, -82, 163, -70, 125),
        ],
        "#983e47",
        INK,
        3,
        closed=True,
    )
    for i in (-58, -31, 0, 28, 55):
        curve(c, [(i, 147), (i - 22, 202, i + 5, 236, i + 10, 277)], "#c46450", 3)
    path(
        c,
        [
            (-38, 26),
            (-56, 29, -92, 50, -95, 74),
            (-84, 119, -62, 123, -64, 148),
            (-31, 162, 44, 164, 74, 144),
            (71, 113, 90, 90, 95, 68),
            (90, 44, 53, 27, 37, 26),
        ],
        "#d88560",
        INK,
        3,
        closed=True,
    )
    path(
        c,
        [
            (-52, 32),
            (-39, 69, -4, 94, 73, 139),
            (66, 151, 59, 154, 48, 155),
            (-21, 111, -48, 84, -70, 46),
        ],
        "#b14646",
        INK,
        2,
        closed=True,
    )
    curve(c, [(-54, 39), (-38, 79, -2, 102, 62, 147)], GOLD, 3)
    curve(c, [(-42, 40), (-30, 95, 23, 110, 46, 43)], "#925543", 3)
    for i in range(12):
        u = i / 11
        ellipse(c, -42 + 88 * u, 42 + 47 * math.sin(math.pi * u), 3.6, 5, GOLD)
    curve(c, [(-65, 146), (-33, 156, 45, 164, 74, 143)], "#704437", 13)
    curve(c, [(-65, 145), (-33, 156, 45, 164, 74, 142)], GOLD, 8)
    diamond(c, 6, 154, 10, 8, "#fff0af")
    limb(
        c,
        [(-79, 63), (-104, 74, -133, 116, -123, 131), (-104, 137, -88, 137, -68, 122)],
        18,
    )
    ellipse(c, -65, 122, 14, 10, "#efa47b")
    curve(c, [(-86, 130), (-82, 137)], GOLD, 5)
    if finger > 0.001:
        bend = smooth(finger)
    else:
        bend = 0
    hx = 80 + 78 * bend
    hy = 119 - 157 * bend
    limb(c, [(79, 63), (108, 77, 113, 107, 126, 106), (133, 107, 143, 66, hx, hy)], 17)
    c.save()
    c.translate(hx, hy)
    c.rotate(-0.45 * (1 - bend))
    path(
        c,
        [
            (-11, 13),
            (-19, 4, -22, -10, -15, -17),
            (-12, -20, -8, -17, -5, -16),
            (-5, -39, -5, -50, 0, -52),
            (7, -53, 8, -49, 8, -42),
            (8, -30, 8, -19, 9, -14),
            (18, -15, 25, -9, 24, -2),
            (26, 9, 19, 22, 10, 22),
            (-1, 24, -9, 19, -11, 13),
        ],
        "#efaa7e",
        INK,
        2.3,
        closed=True,
    )
    for dx in (6, 13, 20):
        curve(c, [(dx, -9), (dx + 2, -3, dx + 1, 2, dx - 1, 5)], "#ac6860", 1.2)
    curve(c, [(-6, 20), (10, 24, 15, 19, 19, 15)], GOLD, 5)
    c.restore()
    c.save()
    c.translate(1, 0)
    c.rotate(math.radians(tilt + 2.5 * math.sin(t * 1.5)))
    draw_surface(c, asset("presenter-head"), -111, -202, 226, 278)
    a = min(1, lips)
    w = 24 + 4 * (1 - a)
    m = 2 + 16 * a
    path(
        c,
        [
            (-w, 23),
            (-w * 0.6, 28 - a * 4, w * 0.4, 31 - a * 9, w, 21),
            (w * 0.65, 29 + m, -w * 0.64, 32 + m, -w, 23),
        ],
        "#703d42",
        "#9a6258",
        1.3,
        closed=True,
    )
    if a > 0.22:
        curve(c, [(-w * 0.58, 26), (0, 28, w * 0.4, 27, w * 0.6, 25)], "#fff1c9", 2.2)
    if a > 0.5:
        curve(
            c,
            [
                (-6, 30 + m * 0.52),
                (0, 30 + m * 0.58, 5, 30 + m * 0.53, 10, 29 + m * 0.48),
            ],
            "#d5887d",
            2,
        )
    blink = max(0, 1 - abs((t + 1.5) % 3.71 - 0.14) / 0.12)
    if blink > 0.2:
        for ex in (-33, 32):
            ellipse(c, ex, -23, 15, 5.8 * blink, "#e09a75")
            curve(
                c, [(ex - 13, -23), (ex - 5, -17, ex + 6, -16, ex + 15, -23)], INK, 1.7
            )
    c.restore()
    c.restore()

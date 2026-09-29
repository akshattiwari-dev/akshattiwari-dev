"""
Builds dark_mode.svg and light_mode.svg:
ASCII portrait (left) + neofetch-style card (right).

Usage:  python tools/build_svg.py [photo.png]
Best input: a PNG with a TRANSPARENT background (transparent = empty space).
Run it again whenever you change your photo or any text below.
"""
import sys
from html import escape
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
PHOTO = sys.argv[1] if len(sys.argv) > 1 else ROOT / "tools" / "photo_cutout.png"

# ---------------- EDIT YOUR INFO HERE ----------------
NAME, HOST = "akshat", "tiwari"
INFO = [  # (label, value)
    ("OS", "Linux"),
    ("Uptime", "Always shipping, always learning"),
    ("Location", "Noida, India"),
    ("Role", "Full-Stack Developer & AI Enthusiast"),
    ("Building", "SyncRank · OAuth Service · MainStage"),
    ("Learning", "AI Agents (LangChain)"),
]
STACK = [
    ("Languages", "JavaScript, TypeScript, Python, C++"),
    ("Frontend", "React, Next.js, Tailwind, HTML, CSS"),
    ("Backend", "Node.js, Express, BullMQ, Prisma"),
    ("Data", "PostgreSQL, MongoDB, Redis"),
    ("Tools", "Git, Linux, Postman, Figma, Jest"),
    ("AI Tools", "Claude, Grok"),
]
CONTACT = [
    ("Email", "akshattiwari2141@gmail.com"),
    ("LinkedIn", "builtby-akshattiwari"),
    ("LeetCode", "akshat-tiwari"),
    ("GitHub", "akshattiwari-dev"),
]
# -----------------------------------------------------

COLS = 120                   # portrait width in characters (more = more detail)
FONT = 5.6                   # portrait font size in px
CELL_W, CELL_H = 3.3, 6.0    # px per character; textLength pins the width so every browser matches
PORTRAIT_X, INFO_X = 14, 432
LOCAL_MIX, GAMMA, FLOOR = 0.55, 1.15, 0.16  # local-contrast strength (0-1), midtone darkening (>1 = darker), minimum ink for dark areas
WIDTH_CH = 60                # width of the right-hand text column in characters
LINE_H, WIDTH_PX = 19, 985
RAMP = " .:-=+*#%@"          # clean 10-step density ramp: shapes read better than noisy letters

THEMES = {
    "dark_mode":  dict(bg="#161b22", border="#30363d", text="#c9d1d9", key="#ffa657", val="#a5d6ff", cc="#616e7f"),
    "light_mode": dict(bg="#f6f8fa", border="#d0d7de", text="#24292f", key="#953800", val="#0a3069", cc="#a0acba"),
}


def ascii_portrait(dark):
    im = Image.open(PHOTO).convert("RGBA")
    box = im.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    im = im.crop(box)
    rows = round(COLS * im.height / im.width * CELL_W / CELL_H)
    im = im.filter(ImageFilter.GaussianBlur(1.0)).resize((COLS, rows), Image.LANCZOS)
    alpha = im.getchannel("A")
    inside = alpha.point(lambda a: 255 if a > 100 else 0)
    gray = ImageOps.autocontrast(im.convert("L"), cutoff=1, mask=inside)
    # Local contrast: keep the broad shading, then boost the difference from the blurred
    # neighbourhood so eyes, brows, nose and beard edges pop while flat areas stay calm.
    local = ImageChops.subtract(gray, gray.filter(ImageFilter.GaussianBlur(7)), scale=1, offset=128)
    local = ImageEnhance.Contrast(local).enhance(2.6)
    gray = Image.blend(gray, local, LOCAL_MIX)
    gray = ImageOps.autocontrast(gray, cutoff=1, mask=inside)
    gray = gray.point(lambda v: int(255 * (FLOOR + (1 - FLOOR) * (v / 255) ** GAMMA)))  # FLOOR keeps hair/suit visible
    lines = []
    for y in range(rows):
        row = ""
        for x in range(COLS):
            if alpha.getpixel((x, y)) < 100:
                row += " "
                continue
            v = gray.getpixel((x, y))
            v = v if dark else 255 - v
            row += RAMP[min(int(v / 256 * len(RAMP)), len(RAMP) - 1)]
        lines.append(row.rstrip())
    return lines


def span(cls, text):
    return f'<tspan class="{cls}">{escape(text)}</tspan>'


def row(label, value, vid=None):
    dots = "." * max(2, WIDTH_CH - len(label) - len(value) - 4)
    v = f'<tspan class="val" id="{vid}">{escape(value)}</tspan>' if vid else span("val", value)
    return span("cc", ". ") + span("key", label) + span("cc", f": {dots} ") + v


def header(title):
    return span("text", f"- {title} ") + span("cc", "-" * (WIDTH_CH - len(title) - 3))


def stat_row(l1, id1, l2, id2):
    d1 = "." * (14 - len(l1))
    return (span("cc", ". ") + span("key", l1) + span("cc", f": {d1} ")
            + f'<tspan class="val" id="{id1}">0</tspan>' + span("cc", "  |  ")
            + span("key", l2) + span("cc", ": ") + f'<tspan class="val" id="{id2}">0</tspan>')


def right_column():
    top = (span("key", NAME) + span("text", "@") + span("key", HOST) + " "
           + span("cc", "-" * (WIDTH_CH - len(NAME) - len(HOST) - 2)))
    L = [top] + [row(k, v) for k, v in INFO]
    L += [header("Tech Stack")] + [row(k, v) for k, v in STACK]
    L += [header("Contact")] + [row(k, v) for k, v in CONTACT]
    L += [header("GitHub Stats"), stat_row("Repos", "repo_data", "Stars", "star_data"),
          stat_row("Commits", "commit_data", "Followers", "follower_data")]
    return L


def build(name, c):
    art = ascii_portrait(name == "dark_mode")
    lines = right_column()
    height = max(len(lines) * LINE_H, len(art) * CELL_H) + 60
    art_y0 = (height - len(art) * CELL_H) / 2 + CELL_H
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH_PX}" height="{height}" viewBox="0 0 {WIDTH_PX} {height}">',
        "<style>",
        ".ascii{font-family:'DejaVu Sans Mono',Consolas,'Courier New',monospace;font-size:5.6px;white-space:pre}",
        ".info{font-family:Consolas,'DejaVu Sans Mono','Courier New',monospace;font-size:14px;white-space:pre}",
        f".text{{fill:{c['text']}}} .key{{fill:{c['key']};font-weight:bold}} .val{{fill:{c['val']}}} .cc{{fill:{c['cc']}}}",
        "</style>",
        f'<rect width="{WIDTH_PX - 2}" height="{height - 2}" x="1" y="1" rx="15" fill="{c["bg"]}" stroke="{c["border"]}"/>',
        f'<text class="ascii" fill="{c["text"]}" xml:space="preserve">',
    ]
    for i, line in enumerate(art):
        lead = len(line) - len(line.lstrip())
        txt = line.strip()
        if txt:
            out.append(f'<tspan x="{PORTRAIT_X + lead * CELL_W:.1f}" y="{art_y0 + i * CELL_H:.1f}" '
                       f'textLength="{len(txt) * CELL_W:.1f}" lengthAdjust="spacing">{escape(txt)}</tspan>')
    out.append("</text>")
    out.append(f'<text class="info" x="{INFO_X}" y="38" xml:space="preserve">')
    for i, line in enumerate(lines):
        out.append(f'<tspan x="{INFO_X}" y="{38 + i * LINE_H}">{line}</tspan>')
    out.append("</text></svg>")
    (ROOT / f"{name}.svg").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {name}.svg  ({len(art)} ascii rows, height {height})")


for n, colors in THEMES.items():
    build(n, colors)

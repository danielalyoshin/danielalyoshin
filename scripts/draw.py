"""Draws the profile README's hardware as SVG, in the Midnight Studio vocabulary of
~/Projects/personal-site (tokens.css, studio/materials.ts, DESIGN.md).

The sqlalchemy-d1 logo tiles (assets/sqlalchemy-d1*.svg) and the knobs app icon
(assets/knobs-app-icon.svg, the master from danielalyoshin/knobs, assets/) are the owner's
files, committed as provided; this script never writes them.

Fonts are the site's own: Archivo (width pinned at 110%, weight kept variable) for the
hardware's prints, and VT323 for the links, which are set as the tube's on-screen links.
Each SVG embeds a small subset, because GitHub renders README images without access to
web fonts. Needs fontTools and brotli:

    pip install fonttools brotli
    python3 scripts/draw.py
"""
import base64
import io
import os

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
SITE = os.path.expanduser("~/Projects/personal-site/node_modules/@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2")
OSD_FONT = os.path.expanduser("~/Projects/personal-site/node_modules/@fontsource/vt323/files/vt323-latin-400-normal.woff2")

# personal-site/src/styles/tokens.css and src/components/studio/materials.ts
SILK_HI, SILK, SILK_DIM = "#e9ebf1", "#b7bbc6", "#868b99"
SHELL, FACE, EDGE, RECESS, RUBBER = "#35404b", "#46515d", "#596675", "#151d27", "#141d27"
TABLETOP, UNDER, MOLDING, WINDOW = "#59636f", "#2a323b", "#1a1f25", "#0f141a"
REC_RED = "#ff3b30"
# cassette label data (studio/Tape.tsx; content/projects/*.ts)
PAPER, LABEL_INK, STUDIO_LABEL, STUDIO_INK = "#deded5", "#192026", "#232931", "#dfe6e1"
KNOBS, SUPERSET, ABOUT = "#e5484d", "#ff7a1a", "#61e8c6"
# the site's tapes as (number, spine, label variant, accent): content/projects/*.ts, content/about.ts.
# A tape's number is its slot on the site's rack.
KNOBS_TAPE = ("01", "KNOBS", "rental", KNOBS)
SUPERSET_D1 = ("02", "SUPERSET D1", "classic", SUPERSET)
ABOUT_TAPE = ("06", "ABOUT", "studio", ABOUT)
# GitHub's own grounds, for prints that sit straight on the page
GH = {"light": {"muted": "#57606a"}, "dark": {"muted": SILK_DIM}}
# The tube's link ink is --osd-white. Off the tube a link sits on GitHub's page, so in light
# it takes GitHub's own text ink, where white would vanish.
OSD_INK = {"light": "#1f2328", "dark": "#ffffff"}

CHARS = "".join(chr(c) for c in range(0x20, 0x7F)) + "–·"


def _embed(font, features=()):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = list(features)
    sub = subset.Subsetter(opts)
    sub.populate(text=CHARS)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


# (the @font-face, the family stack) for each face a print can be set in
ARCHIVO = ("@font-face{font-family:'Archivo';font-weight:100 900;src:url(data:font/woff2;base64,%s) format('woff2')}"
           % _embed(instancer.instantiateVariableFont(TTFont(SITE), {"wdth": 110}), ["kern"]),
           "'Archivo',Arial,sans-serif")
VT323 = ("@font-face{font-family:'VT323';src:url(data:font/woff2;base64,%s) format('woff2')}" % _embed(TTFont(OSD_FONT)),
         "'VT323',ui-monospace,'Courier New',monospace")
_METRICS = {w: instancer.instantiateVariableFont(TTFont(SITE), {"wdth": 110, "wght": w}) for w in (600, 800)}
_METRICS["osd"] = TTFont(OSD_FONT)


def text_width(s, size, weight=600, tracking=0.0):
    """Advance width of a line as Chrome sets it: glyph advances plus tracking after every glyph.
    Weight "osd" measures VT323 instead of Archivo."""
    font = _METRICS[weight]
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in s) * size / upm + tracking * len(s)


def svg(w, h, body, title, extra_css="", face=ARCHIVO):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
            f"<title>{title}</title><style>{face[0]}"
            f"text{{font-family:{face[1]}}}.w400{{font-weight:400}}.w600{{font-weight:600}}.w800{{font-weight:800}}"
            f"{extra_css}</style>{body}</svg>")


# Drawn marks (The Drawn Mark Rule): nothing here is ever a typed glyph.
def mark_arrow(x, y, s, color):
    """The site's outward-link mark (Icons.tsx, ExternalIcon): 1.5-unit strokes on a 16-unit box."""
    return (f'<g transform="translate({x} {y}) scale({s / 16})" fill="none" stroke="{color}" stroke-width="1.5">'
            '<path d="M4.25 11.75 11.5 4.5M6 4.5h5.5V10"/></g>')


def mark_eject(x, y, s, color):
    return (f'<path d="M{x} {y + s * 0.6} L{x + s / 2} {y} L{x + s} {y + s * 0.6} Z" fill="{color}"/>'
            f'<rect x="{x}" y="{y + s * 0.76}" width="{s}" height="{s * 0.22}" fill="{color}"/>')


def mark_speaker_muted(x, y, s, color):
    """The deck's sound mark with sound off: a filled speaker, and the red slash that is the deck's one colour print."""
    k = s / 20
    return (f'<g transform="translate({x} {y}) scale({k})"><path d="M3 7.5 H7 L12 3.5 V16.5 L7 12.5 H3 Z" fill="{color}"/>'
            f'<path d="M2.5 17.5 L17.5 2.5" stroke="{REC_RED}" stroke-width="1.8" stroke-linecap="round"/></g>')


def keycap(x, y, w, h, radius=3):
    """A beveled cap in its recess: lit top edge, darker bottom edge (DESIGN.md: Playback buttons)."""
    return (f'<rect x="{x - 3}" y="{y - 3}" width="{w + 6}" height="{h + 6}" rx="{radius + 2}" fill="{RECESS}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{FACE}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="3" rx="1.5" fill="{EDGE}"/>'
            f'<rect x="{x}" y="{y + h - 4}" width="{w}" height="4" fill="{UNDER}"/>')


def deck(compact=False):
    """The AV-01 deck, head-on, on the studio table. The owner's name is the maker's mark.
    No tape is loaded: the slot's flap hangs closed and the readout stands at STANDBY,
    as the site's deck shows between tapes (studio/Player.tsx)."""
    if compact:
        W, H = 600, 508
        x0, x1, top, bot = 24, 576, 24, 460
        name_xy, name_size, role_y, role_size = (58, 94), 40, 126, 19.5
        bay = (56, 544, 154, 266)
        win = (56, 544, 288, 336)
        key = (318, 362, 226, 46)
        sound = (56, 362, 226, 46)
        type_size, model_y, model_size = 20, 438, 17
    else:
        W, H = 1000, 284
        x0, x1, top, bot = 52, 948, 36, 236
        name_xy, name_size, role_y, role_size = (88, 104), 32, 132, 15.5
        bay = (440, 750, 70, 176)
        win = (770, 924, 70, 110)
        key = (774, 132, 146, 40)
        sound = (89, 162, 116, 40)
        type_size, model_y, model_size = 15.5, 212, 14.5
    b = []
    # the table the equipment stands on: top plane, front face, recessed pedestal
    ty = bot + 6
    b.append(f'<defs><filter id="s" x="-10%" y="-300%" width="120%" height="700%"><feGaussianBlur stdDeviation="6"/></filter></defs>')
    b.append(f'<ellipse cx="{W / 2}" cy="{H - 8}" rx="{W * 0.44}" ry="5" fill="#000" opacity="0.22" filter="url(#s)"/>')
    b.append(f'<rect x="{x0 - 36}" y="{ty}" width="{x1 - x0 + 72}" height="8" fill="{TABLETOP}"/>')
    b.append(f'<rect x="{x0 - 36}" y="{ty + 8}" width="{x1 - x0 + 72}" height="16" fill="#46505b"/>')
    b.append(f'<rect x="{x0 + 4}" y="{ty + 24}" width="{x1 - x0 - 8}" height="10" fill="#1b222a"/>')
    # chassis: lit cover edge, one-tone fascia, parting line, darker underside, four pads
    b.append(f'<rect x="{x0}" y="{top}" width="{x1 - x0}" height="12" rx="3" fill="{EDGE}"/>')
    b.append(f'<rect x="{x0}" y="{top + 10}" width="{x1 - x0}" height="{bot - top - 10}" fill="{SHELL}"/>')
    b.append(f'<rect x="{x0}" y="{top + 16}" width="{x1 - x0}" height="1.5" fill="{RECESS}"/>')
    b.append(f'<rect x="{x0}" y="{bot - 6}" width="{x1 - x0}" height="6" fill="{UNDER}"/>')
    pad = 40 if compact else 46
    for px in (x0 + 22, x0 + 22 + pad * 1.9, x1 - 22 - pad * 2.9, x1 - 22 - pad):
        b.append(f'<rect x="{px}" y="{bot}" width="{pad}" height="6" rx="1.5" fill="{RUBBER}"/>')
    # maker's mark
    assert name_xy[0] + text_width("DANIEL ALYOSHIN", name_size, 800, -name_size * 0.018) < bay[0] - 16 or compact, "the name runs into the bay"
    b.append(f'<text class="w800" x="{name_xy[0]}" y="{name_xy[1]}" font-size="{name_size}" letter-spacing="{-name_size * 0.018}" fill="{SILK_HI}">DANIEL ALYOSHIN</text>')
    b.append(f'<text class="w600" x="{name_xy[0] + 1}" y="{role_y}" font-size="{role_size}" letter-spacing="{role_size * 0.12}" fill="{SILK}">FORWARD DEPLOYED ENGINEER</text>')
    # the slot, empty: its flap hangs closed in the opening, shaded where it hinges under the
    # fascia, with the lit lip a tape pushes on near its foot (Player.tsx: player-flap)
    bx0, bx1, by0, by1 = bay
    fx0, fy0, fw, fh = bx0 + 5, by0 + 5, bx1 - bx0 - 10, by1 - by0 - 10
    b.append(f'<rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" rx="3" fill="{RECESS}"/>')
    b.append(f'<rect x="{fx0}" y="{fy0}" width="{fw}" height="{fh}" rx="2" fill="{UNDER}"/>')
    b.append(f'<rect x="{fx0}" y="{fy0 + 3}" width="{fw}" height="{fh - 3}" rx="2" fill="{SHELL}"/>')
    b.append(f'<rect x="{fx0 + fw * 0.065:.2f}" y="{fy0 + fh * 0.88 - 1:.2f}" width="{fw * 0.87:.2f}" height="2" fill="{EDGE}"/>')
    b.append(f'<text class="w600" x="{(bx0 + bx1) / 2}" y="{model_y}" text-anchor="middle" font-size="{model_size}" letter-spacing="{model_size * 0.12}" fill="{SILK_DIM}">AV–01 / VHS</text>')
    # status window: transport state left, sound mark right
    wx0, wx1, wy0, wy1 = win
    mid = (wy0 + wy1) / 2
    speaker = type_size * 1.15
    assert wx0 + 12 + text_width("STANDBY", type_size, 600, type_size * 0.1) < wx1 - 12 - speaker, "STANDBY runs into the sound mark"
    b.append(f'<rect x="{wx0}" y="{wy0}" width="{wx1 - wx0}" height="{wy1 - wy0}" rx="2" fill="{WINDOW}"/>')
    b.append(f'<text class="w600" x="{wx0 + 12}" y="{mid + type_size * 0.36}" font-size="{type_size}" letter-spacing="{type_size * 0.1}" fill="{SILK_HI}">STANDBY</text>')
    b.append(mark_speaker_muted(wx1 - 12 - speaker, mid - type_size * 0.58, speaker, SILK_HI))
    # the sound key: one printed label; sound state is the window's mark, not the key's
    sx, sy, sw, sh = sound
    b.append(keycap(sx, sy, sw, sh))
    b.append(f'<text class="w600" x="{sx + sw / 2}" y="{sy + sh / 2 + type_size * 0.3}" text-anchor="middle" font-size="{type_size}" letter-spacing="{type_size * 0.1}" fill="{SILK_HI}">SOUND</text>')
    # the eject key, wide, beneath the window
    kx, ky, kw, kh = key
    b.append(keycap(kx, ky, kw, kh))
    label = text_width("EJECT", type_size, 600, type_size * 0.1)
    lead = type_size * 0.72 + type_size * 0.5
    start = kx + (kw - label - lead) / 2
    b.append(mark_eject(start, ky + kh / 2 - type_size * 0.42, type_size * 0.72, SILK_HI))
    b.append(f'<text class="w600" x="{start + lead}" y="{ky + kh / 2 + type_size * 0.3}" font-size="{type_size}" letter-spacing="{type_size * 0.1}" fill="{SILK_HI}">EJECT</text>')
    return svg(W, H, "".join(b), "Daniel Alyoshin, forward deployed engineer")


def osd_link(label, title, theme, left=0, right=0):
    """A link as the site's tube sets them at the foot of each tape (CRT.module.css, .links a):
    uppercase VT323 at 20 in a 1px outline with 2px corners, 6/14 padding, 44 tall, ending in the
    outward arrow at 0.7em after a 0.4em gap. Off the tube it takes the page's ink for the theme.
    left/right are clear space drawn in, standing in for the site's 16px gap between links."""
    size, h, pad = 20, 44, 14
    ink = OSD_INK[theme]
    tw = text_width(label, size, "osd")
    bw = 1 + pad + tw + size * 0.4 + size * 0.7 + pad + 1
    arrow = size * 0.7
    body = (f'<rect x="{left + 0.5}" y="0.5" width="{bw - 1}" height="{h - 1}" rx="2" fill="none" stroke="{ink}"/>'
            # VT323's capitals stand 0.56em, centred on the box
            f'<text x="{left + 1 + pad}" y="{h / 2 + size * 0.28}" font-size="{size}" fill="{ink}">{label}</text>' +
            mark_arrow(left + 1 + pad + tw + size * 0.4, (h - arrow) / 2, arrow, ink))
    return svg(round(left + bw + right), h, body, title, face=VT323)


def section_label(text, theme):
    """A silkscreen label printed on the page: uppercase Archivo 600, 0.12em tracking, dim ink."""
    size, h = 15, 24
    ink = GH[theme]["muted"]
    w = round(text_width(text, size, 600, size * 0.12) + 2)
    body = f'<text class="w600" x="0" y="{h / 2 + size * 0.36}" font-size="{size}" letter-spacing="{size * 0.12}" fill="{ink}">{text}</text>'
    return svg(w, h, body, text.title()), w


def shelf():
    """The archive holder with the site's six slots, in the site's order: tapes 01 and 02,
    three blank tapes, and the About tape."""
    W, H, crop = 560, 292, 44
    tw, th, x_start, gap, base = 54, 236, 62, 20.4, 286
    b = [f'<defs><filter id="s" x="-10%" y="-300%" width="120%" height="700%"><feGaussianBlur stdDeviation="5"/></filter></defs>',
         f'<ellipse cx="{W / 2}" cy="{H + crop - 10}" rx="{W * 0.42}" ry="4" fill="#000" opacity="0.22" filter="url(#s)"/>',
         # sloped cheeks, rear stop and floor
         f'<path d="M22 {base + 20} V112 L50 96 V{base + 20} Z" fill="{SHELL}"/>',
         f'<path d="M538 {base + 20} V112 L510 96 V{base + 20} Z" fill="{SHELL}"/>',
         f'<path d="M50 96 L22 112" stroke="{EDGE}" stroke-width="2"/><path d="M510 96 L538 112" stroke="{EDGE}" stroke-width="2"/>',
         f'<rect x="50" y="118" width="460" height="{base - 118}" fill="#1b222a"/>']
    tapes = [KNOBS_TAPE, SUPERSET_D1, None, None, None, ABOUT_TAPE]
    for i, tape in enumerate(tapes):
        x = x_start + i * (tw + gap)
        y = base - th
        b.append(f'<rect x="{x - 3}" y="{y + 10}" width="{tw + 6}" height="{th - 10}" fill="{RECESS}"/>')  # guide channel
        b.append(f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="3" fill="{MOLDING}"/>')
        b.append(f'<rect x="{x + tw - 6}" y="{y + 2}" width="4" height="{th - 2}" fill="#12161b"/>')  # the shell's side, turned slightly
        b.append(f'<rect x="{x + 3}" y="{y}" width="{tw - 6}" height="1" fill="#2b323b"/>')
        if tape is None:  # a blank tape: molded ribs, no label
            for r in range(2):
                b.append(f'<rect x="{x + 10}" y="{y + 26 + r * 8}" width="{tw - 20}" height="2" fill="#11151a"/>')
            continue
        number, name, variant, accent = tape
        studio = variant == "studio"
        lx, ly, lw, lh = x + 6, y + 8, tw - 12, th - 16
        # a rental label is printed on the accent itself, in label ink (studio/Tape.tsx)
        ground, ink = {"studio": (STUDIO_LABEL, accent), "classic": (PAPER, LABEL_INK), "rental": (accent, LABEL_INK)}[variant]
        b.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{ground}"/>')
        b.append(f'<rect x="{lx + 4}" y="{ly + 5}" width="{lw - 8}" height="1.6" fill="{ink}"/>')
        b.append(f'<text class="w800" x="{lx + 5}" y="{ly + 23}" font-size="15" fill="{ink}">{number}</text>')
        name_size = min(17, (lh - 90) / (text_width(name, 1, 800)))
        b.append(f'<text class="w800" transform="translate({lx + lw / 2 + name_size * 0.36} {ly + 34}) rotate(90)" font-size="{name_size:.2f}" fill="{ink}">{name}</text>')
        bly = ly + lh - 44
        b.append(f'<rect x="{lx}" y="{bly}" width="{lw}" height="22" fill="{accent}"/>')
        if studio:
            b.append(f'<rect x="{lx + 5}" y="{bly + 6}" width="{lw - 10}" height="1.6" fill="{STUDIO_LABEL}"/>')
            b.append(f'<rect x="{lx + 5}" y="{bly + 11}" width="{(lw - 10) * 0.7}" height="1.6" fill="{STUDIO_LABEL}"/>')
        else:
            for s in range(5):
                b.append(f'<rect x="{lx}" y="{bly + 1.5 + s * 4.1:.2f}" width="{lw}" height="1.3" fill="{LABEL_INK}"/>')
        b.append(f'<text class="w600" x="{lx + 5}" y="{ly + lh - 7}" font-size="10" fill="{STUDIO_INK if studio else LABEL_INK}">VHS</text>')
    # the low retaining lip in front, standing on pads
    b.append(f'<rect x="22" y="{base}" width="516" height="20" fill="{FACE}"/>')
    b.append(f'<rect x="22" y="{base}" width="516" height="3" fill="{EDGE}"/>')
    b.append(f'<rect x="22" y="{base + 16}" width="516" height="4" fill="{UNDER}"/>')
    for px in (30, 150, 370, 490):
        b.append(f'<rect x="{px}" y="{base + 20}" width="40" height="6" rx="1.5" fill="{RUBBER}"/>')
    b[0] = b[0] + f'<g transform="translate(0 {-crop})">'
    b.append("</g>")
    return svg(W, H, "".join(b), "The tape shelf: KNOBS, SUPERSET D1, three blank tapes, and About")


def main():
    os.makedirs(ASSETS, exist_ok=True)
    out = {}
    out["deck.svg"] = deck()
    out["deck-compact.svg"] = deck(compact=True)
    out["shelf.svg"] = shelf()
    # the contact row is centred under the deck, so its clear space splits either side;
    # a project's row starts flush with its text, so its clear space all falls after
    contact = (("linkedin", "LINKEDIN", "LinkedIn"), ("email", "EMAIL", "Email"), ("site", "ALYOSHIN.DEV", "alyoshin.dev"))
    knobs = (("getknobs", "GETKNOBS.APP", "getknobs.app"), ("knobs-source", "SOURCE", "Source"))
    superset = (("pypi", "PYPI", "PyPI"), ("dialect-pr", "DIALECT PR", "Dialect PR"),
                ("superset-pr", "SUPERSET PR", "Superset PR"), ("packages", "PACKAGES", "Packages"))
    for row, left, right in ((contact, 6, 6), (knobs, 0, 12), (superset, 0, 12)):
        for slug, label, title in row:
            for theme in ("light", "dark"):
                out[f"link-{slug}-{theme}.svg"] = osd_link(label, title, theme, left, right)
    for slug, text in (("about", "ABOUT"), ("projects", "PROJECTS"), ("stack", "STACK")):
        for theme in ("light", "dark"):
            out[f"label-{slug}-{theme}.svg"], _ = section_label(text, theme)
    for name, content in out.items():
        with open(os.path.join(ASSETS, name), "w") as f:
            f.write(content)
    for name in sorted(os.listdir(ASSETS)):
        print(f"{os.path.getsize(os.path.join(ASSETS, name)):>7}  assets/{name}")


if __name__ == "__main__":
    main()

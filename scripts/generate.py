#!/usr/bin/env python3
"""Generate one Ziran module per MingCute SVG, and the package's [exports].

Each module holds a single constant, Shape: the icon reduced to drawing
operations, so an application that imports an icon carries only that icon.

    Shape :: "<op>|<op>|..."      op = <kind> ":" <path data>
    kind  F        fill, nonzero
          E        fill, even-odd
          S<w><c><j>  stroke of width w (a number), cap c and join j, each one of
                   b butt / r round / s square (cap) and m miter / r round /
                   v bevel (join)

Shapes are in the icon's own 24 x 24 view box. Colors are dropped: an icon is a
mask that the caller tints. Icons built on gradients, clip paths or dashes are
skipped and listed in SKIPPED.txt.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"
KAPPA = 0.5522847498307936
CAPS = {"butt": "b", "round": "r", "square": "s"}
JOINS = {"miter": "m", "round": "r", "bevel": "v"}
SOURCE_LINE_LIMIT = 4095


def num(value):
    text = f"{float(value):.4f}".rstrip("0").rstrip(".")
    return text or "0"


def ellipse_path(cx, cy, rx, ry):
    ox, oy = rx * KAPPA, ry * KAPPA
    return (f"M{num(cx + rx)} {num(cy)}"
            f"C{num(cx + rx)} {num(cy + oy)} {num(cx + ox)} {num(cy + ry)} {num(cx)} {num(cy + ry)}"
            f"C{num(cx - ox)} {num(cy + ry)} {num(cx - rx)} {num(cy + oy)} {num(cx - rx)} {num(cy)}"
            f"C{num(cx - rx)} {num(cy - oy)} {num(cx - ox)} {num(cy - ry)} {num(cx)} {num(cy - ry)}"
            f"C{num(cx + ox)} {num(cy - ry)} {num(cx + rx)} {num(cy - oy)} {num(cx + rx)} {num(cy)}Z")


def rect_path(x, y, w, h, r):
    if r <= 0:
        return f"M{num(x)} {num(y)}H{num(x + w)}V{num(y + h)}H{num(x)}Z"
    k = r * KAPPA
    return (f"M{num(x + r)} {num(y)}H{num(x + w - r)}"
            f"C{num(x + w - r + k)} {num(y)} {num(x + w)} {num(y + r - k)} {num(x + w)} {num(y + r)}"
            f"V{num(y + h - r)}"
            f"C{num(x + w)} {num(y + h - r + k)} {num(x + w - r + k)} {num(y + h)} {num(x + w - r)} {num(y + h)}"
            f"H{num(x + r)}"
            f"C{num(x + r - k)} {num(y + h)} {num(x)} {num(y + h - r + k)} {num(x)} {num(y + h - r)}"
            f"V{num(y + r)}"
            f"C{num(x)} {num(y + r - k)} {num(x + r - k)} {num(y)} {num(x + r)} {num(y)}Z")


def shape_of(path):
    root = ET.parse(path).getroot()
    if root.get("viewBox") != "0 0 24 24":
        raise ValueError("view box")
    ops = []
    for element in root.iter():
        tag = element.tag.replace(SVG, "")
        if tag in ("svg", "defs"):
            continue
        if tag not in ("path", "circle", "rect", "ellipse"):
            raise ValueError(tag)
        a = element.attrib
        if "stroke-dasharray" in a or "data-figma-gradient-fill" in a or "opacity" in a:
            raise ValueError("dash, gradient or opacity")
        if tag == "path":
            d = a["d"]
        elif tag == "circle":
            d = ellipse_path(float(a["cx"]), float(a["cy"]), float(a["r"]), float(a["r"]))
        elif tag == "ellipse":
            d = ellipse_path(float(a["cx"]), float(a["cy"]), float(a["rx"]), float(a["ry"]))
        else:
            d = rect_path(float(a.get("x", 0)), float(a.get("y", 0)),
                          float(a["width"]), float(a["height"]), float(a.get("rx", 0)))
        if not re.fullmatch(r"[MLHVCZ0-9eE.,\s-]+", d):
            raise ValueError("path command")
        d = re.sub(r"\s+", " ", d.strip())
        filled = a.get("fill") not in (None, "none") or (a.get("stroke") is None and tag != "svg")
        if a.get("fill") == "none":
            filled = False
        if filled:
            ops.append(("E:" if a.get("fill-rule") == "evenodd" else "F:") + d)
        if a.get("stroke") not in (None, "none"):
            ops.append(f"S{num(a.get('stroke-width', 1))}"
                       f"{CAPS[a.get('stroke-linecap', 'butt')]}"
                       f"{JOINS[a.get('stroke-linejoin', 'miter')]}:{d}")
    if not ops:
        raise ValueError("empty")
    return "|".join(ops)


def shape_declaration(shape):
    declaration = f'Shape :: "{shape}";'
    if len(declaration) <= SOURCE_LINE_LIMIT:
        return declaration + "\n"

    # SVG paths accept newlines wherever they accept spaces between operands.
    lines = []
    while len(shape) > SOURCE_LINE_LIMIT:
        split_at = shape.rfind(" ", 0, SOURCE_LINE_LIMIT + 1)
        if split_at <= 0:
            raise ValueError("icon path has no separator within the source line limit")
        lines.append(shape[:split_at])
        shape = shape[split_at + 1:]
    lines.append(shape)
    return "Shape :: #string END_SHAPE\n" + "\n".join(lines) + "\nEND_SHAPE;\n"


def main():
    revision = sys.argv[1] if len(sys.argv) > 1 else "unversioned"
    modules = ROOT / "src"
    exports = []
    skipped = []
    seen = {}
    for style in ("filled", "regular", "extra"):
        base = ROOT / "svg" / style
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.svg")):
            name = path.stem
            key = (style, name)
            if key in seen:
                raise SystemExit(f"duplicate icon {style}/{name}: {path} and {seen[key]}")
            seen[key] = path
            try:
                shape = shape_of(path)
            except ValueError as reason:
                skipped.append(f"{style}/{path.relative_to(base).as_posix()}: {reason}")
                continue
            module = f"mingcute_{style}_{name}"
            out = modules / f"{module}.zi"
            out.write_text(
                (f"// MingCute {style} icon \"{name}\" (Apache-2.0, see LICENSE).\n"
                 if style != "extra" else
                 f"// Icon \"{name}\", drawn to match MingCute regular (Apache-2.0, see LICENSE).\n") +
                f"// Generated by scripts/generate.py from svg/{style}/{path.relative_to(base).as_posix()}.\n"
                + shape_declaration(shape))
            exports.append(f'{module} = "src/{module}.zi"')
    (ROOT / "SKIPPED.txt").write_text("\n".join(skipped) + "\n")
    (ROOT / "ziran.toml").write_text(
        '[package]\nname = "mingcute"\nmodule_roots = ["src"]\n\n'
        '[toolchain]\ngit = "https://git.waozi.xyz/ziranlang/ziran.git"\nref = "5db3d3c39425d5dfe4bfe4a84e6f6e2e5a810ad0"\n\n'
        "[exports]\n" + "\n".join(exports) + "\n")
    print(f"{len(exports)} icons, {len(skipped)} skipped (MingCute {revision})")


main()

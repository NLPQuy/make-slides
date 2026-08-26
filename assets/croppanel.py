#!/usr/bin/env python3
"""
croppanel.py -- cut one panel out of a multi-panel paper figure.

Paper figures are composed for a two-column page: three panels side by side,
7pt labels, meant to be read at 30 cm. Projected, that becomes three competing
images none of which is legible, and the speaker ends up saying "look at the
middle one", which is the audience's cue to stop looking.

One panel per slide. Crop, do not shrink.

Python port of croppanel.sh for machines without ghostscript (TeX Live on
Windows ships none). Uses PyMuPDF. Auto-trims dead margin after
the crop, which is the step everyone skips: hand-picked crop coordinates leave
whitespace, and two panels can waste half their area on it.

Usage:
    python croppanel.py fig.pdf                        # print the bbox
    python croppanel.py fig.pdf --grid 1x3             # preview a split
    python croppanel.py fig.pdf out.pdf x0 y0 x1 y1    # crop one panel
    python croppanel.py fig.pdf --split 1x3 --out figures/panel
                                                               # cut every panel

Coordinates are PDF points, origin BOTTOM-LEFT, same convention the bbox
printout uses. Fractions of the width also work: 0.34 means 34% across.

ALWAYS open the .preview.png it writes. Every crop this skill has got wrong
was one nobody looked at: 20 points of error swallows an axis label.
"""
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("croppanel.py needs PyMuPDF:  pip install pymupdf")

PREVIEW_DPI = 120
TRIM_PAD = 2.0  # points of padding kept after the auto-trim, like pdfcrop --margins 2


def _open(path):
    if not os.path.exists(path):
        sys.exit(f"not found: {path}")
    doc = fitz.open(path)
    if doc.page_count != 1:
        print(f"  note: {doc.page_count} pages, only page 1 is cropped")
    return doc


def _resolve(v, span, lo):
    """A value <= 1.0 is read as a fraction of the span, anything larger as points."""
    v = float(v)
    return lo + v * span if 0.0 <= v <= 1.0 else v


def _ink_bbox(page, clip=None):
    """Tightest box around actual drawn content, so dead margin can be trimmed."""
    pix = page.get_pixmap(dpi=72, clip=clip)
    if pix.width < 2 or pix.height < 2:
        return None
    # Walk the pixmap for the extent of everything that is not the corner colour.
    bg = pix.pixel(0, 0)
    x0, y0, x1, y1 = pix.width, pix.height, 0, 0
    for y in range(pix.height):
        for x in range(pix.width):
            if pix.pixel(x, y) != bg:
                if x < x0: x0 = x
                if y < y0: y0 = y
                if x > x1: x1 = x
                if y > y1: y1 = y
    if x1 <= x0 or y1 <= y0:
        return None
    origin = clip if clip is not None else page.rect
    # The +1 covers the pixel's own width; clamp to the origin box, or a
    # full-bleed page reports an ink box larger than the page it came from.
    return fitz.Rect(origin.x0 + x0, origin.y0 + y0,
                     origin.x0 + x1 + 1, origin.y0 + y1 + 1) & origin


def _write(doc, page, rect, out, trim=True):
    if trim:
        ink = _ink_bbox(page, clip=rect)
        if ink is not None:
            rect = fitz.Rect(max(rect.x0, ink.x0 - TRIM_PAD),
                             max(rect.y0, ink.y0 - TRIM_PAD),
                             min(rect.x1, ink.x1 + TRIM_PAD),
                             min(rect.y1, ink.y1 + TRIM_PAD))
    page.set_cropbox(rect)
    d = os.path.dirname(os.path.abspath(out))
    os.makedirs(d, exist_ok=True)
    doc.save(out, garbage=4, deflate=True)

    png = os.path.splitext(out)[0] + ".preview.png"
    with fitz.open(out) as o:
        o[0].get_pixmap(dpi=PREVIEW_DPI).save(png)
    print(f"  wrote {out}")
    print(f"  preview {png}   <- open it. Check no axis label or legend got cut.")


def cmd_bbox(path):
    doc = _open(path)
    page = doc[0]
    r = page.rect
    print(f"bounding box of {path}:")
    print(f"  media  {r.x0:.1f} {r.y0:.1f} {r.x1:.1f} {r.y1:.1f}"
          f"   ({r.width:.1f} x {r.height:.1f} pt)")
    ink = _ink_bbox(page)
    if ink is not None:
        print(f"  ink    {ink.x0:.1f} {ink.y0:.1f} {ink.x1:.1f} {ink.y1:.1f}"
              f"   ({ink.width:.1f} x {ink.height:.1f} pt)")
        waste = max(0.0, 100 * (1 - (ink.width * ink.height) / (r.width * r.height)))
        print(f"  {waste:.0f}% of the page area is dead margin")
    print()
    print(f"crop one panel:  python {sys.argv[0]} {path} out.pdf x0 y0 x1 y1")
    print(f"cut every panel: python {sys.argv[0]} {path} --split 1x3 --out figures/panel")
    doc.close()


def _grid(spec):
    try:
        rows, cols = (int(v) for v in spec.lower().split("x"))
    except ValueError:
        sys.exit(f"--split/--grid wants ROWSxCOLS, e.g. 1x3, got {spec!r}")
    return rows, cols


def cmd_split(path, spec, out_stem):
    rows, cols = _grid(spec)
    src = _open(path)
    r = src[0].rect
    w, h = r.width / cols, r.height / rows
    n = 0
    for i in range(rows):
        for j in range(cols):
            n += 1
            cell = fitz.Rect(r.x0 + j * w, r.y0 + i * h,
                             r.x0 + (j + 1) * w, r.y0 + (i + 1) * h)
            doc = _open(path)
            _write(doc, doc[0], cell, f"{out_stem}{n}.pdf")
            doc.close()
    src.close()
    print(f"\n{n} panels. An even grid is a GUESS: open every preview, and fall")
    print("back to explicit coordinates for any panel whose axis label got cut.")


def cmd_crop(path, out, coords):
    doc = _open(path)
    page = doc[0]
    r = page.rect
    x0 = _resolve(coords[0], r.width, r.x0)
    y0 = _resolve(coords[1], r.height, r.y0)
    x1 = _resolve(coords[2], r.width, r.x0)
    y1 = _resolve(coords[3], r.height, r.y0)
    rect = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    if rect.is_empty or not rect.intersects(r):
        sys.exit(f"crop box {rect} lies outside the page {r}")
    _write(doc, page, rect & r, out)
    doc.close()


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    path = a[0]
    rest = a[1:]

    if not rest or rest[0] in ("--bbox",):
        cmd_bbox(path)
    elif rest[0] in ("--grid", "--split"):
        if len(rest) < 2:
            sys.exit("--split wants a grid, e.g. --split 1x3")
        out = "panel"
        if "--out" in rest:
            out = rest[rest.index("--out") + 1]
        cmd_split(path, rest[1], out)
    elif len(rest) == 5:
        cmd_crop(path, rest[0], rest[1:])
    else:
        sys.exit("usage: croppanel.py fig.pdf [out.pdf x0 y0 x1 y1 | --split RxC --out stem]")


if __name__ == "__main__":
    main()

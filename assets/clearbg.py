#!/usr/bin/env python3
"""
clearbg.py -- make a paper figure's background transparent.

Matplotlib writes an opaque white rectangle covering the whole page unless you
passed transparent=True, which you did not, and you no longer have the plotting
script. On a slide whose ground is anything but pure white that rectangle shows
up as a bright panel with hard edges, and the figure reads as pasted on rather
than placed.

This finds the leading full-page fill at the start of the content stream and
turns its paint operator into a no-op (f -> n), so the rectangle is still there
and still the right size but paints nothing. Everything drawn after it is
untouched.

    ./clearbg.py figures/*.pdf          # in place, keeps a .orig backup
    ./clearbg.py --check figures/*.pdf  # report only, change nothing
    ./clearbg.py --all figures/plot.pdf # also clear WHITE fills further in

--all additionally neutralises white fills that are not the first paint, which
is what a matplotlib axes patch is: the panel behind the plotting area, drawn
after the figure background. Only pure-white fills are touched, and the bbox
check still guards against structural damage, but a figure that deliberately
paints something white will lose it. Use it per file, look at the result.

Every edit is verified: the ink bounding box must be identical afterwards. If
it is not, the original is put back and the file is reported as skipped. An
earlier version of this script did not verify, and silently blanked three of
eight figures -- the damage was only visible on a rendered slide.
"""
import re, sys, zlib, shutil, subprocess, os, tempfile

LEAD = re.compile(
    rb"\A(\s*q[^\n]*\n)"
    rb"((?:1|1\.0+)\s+g\s*\n"
    rb"|(?:1|1\.0+)\s+(?:1|1\.0+)\s+(?:1|1\.0+)\s+rg\s*\n)"
    rb"(\s*[\d.\-]+\s+[\d.\-]+\s+[\d.\-]+\s+[\d.\-]+\s+re\s*\n)"
    rb"(f\s*\n)", re.S)


def ink(path):
    """Bounding box of everything actually drawn, rounded to whole points."""
    r = subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dUseCropBox", "-sDEVICE=bbox", path],
        capture_output=True, text=True)
    m = re.search(r"%%HiResBoundingBox: ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)", r.stderr)
    if not m:
        return None
    x0, y0, x1, y1 = map(float, m.groups())
    return round(x1 - x0), round(y1 - y0)


def repack(blob, patched):
    """Recompress `patched` to exactly len(blob) bytes, or return None.

    The patch is f -> n, one byte for one byte, so the DECOMPRESSED length is
    unchanged; only the compressed length moves. Compress at whatever level
    lands under the original size and pad the remainder with newlines: a
    deflate reader stops at the end of the stream and ignores the tail, so
    /Length stays correct and the xref never moves.

    This exists because patching /Length is a minefield. It can be a direct
    number or an indirect reference, and a generated PDF can carry the same
    object number twice, so the reference resolves to the wrong object. Not
    changing any length at all sidesteps the lot.
    """
    for level in (9, 8, 6, 4, 2, 1):
        c = zlib.compress(patched, level)
        if len(c) <= len(blob):
            return c + b"\n" * (len(blob) - len(c))
    return None


def flatten(path):
    """Rewrite through ghostscript so the page is one plain content stream.

    pdfcrop wraps the original page in a Form XObject, which buries the
    background fill one level down and makes the /Length arithmetic fragile.
    Ghostscript's pdfwrite flattens that away. Figures that came straight from
    gs are already flat and this is a no-op for them.
    """
    tmp = tempfile.mktemp(suffix=".pdf")
    r = subprocess.run(["gs", "-q", "-o", tmp, "-sDEVICE=pdfwrite", "-dQUIET", path],
                       capture_output=True)
    if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
        shutil.move(tmp, path)
        return True
    if os.path.exists(tmp):
        os.remove(tmp)
    return False


ANYWHITE = re.compile(
    rb"((?:1|1\.0+)\s+g\s*\n|(?:1|1\.0+)\s+(?:1|1\.0+)\s+(?:1|1\.0+)\s+rg\s*\n)"
    rb"(\s*[\d.\-]+\s+[\d.\-]+\s+[\d.\-]+\s+[\d.\-]+\s+re\s*\n)(f)(\s*\n)")


def clear(path, check=False, allwhite=False):
    raw = open(path, "rb").read()
    if not check and b"/Subtype /Form" in raw and b"PTEX" in raw:
        before = ink(path)
        shutil.copyfile(path, path + ".flat")
        if flatten(path) and ink(path) == before:
            os.remove(path + ".flat")
            raw = open(path, "rb").read()
        else:
            shutil.move(path + ".flat", path)
    for m in re.finditer(rb"stream\r?\n", raw):
        s, e = m.end(), raw.find(b"endstream", m.end())
        if e < 0:
            continue
        try:
            content = zlib.decompress(raw[s:e])
        except zlib.error:
            continue
        hit = LEAD.match(content)
        # --all does not need the leading fill: a figure whose page background
        # was already cleared still has its axes patch to deal with.
        if not hit and not (allwhite and ANYWHITE.search(content)):
            continue
        if check:
            return "would clear"

        before = ink(path)
        if allwhite:
            # f -> n keeps the byte count, so the stream length never moves
            patched = ANYWHITE.sub(rb"\1\2n\4", content)
        else:
            patched = content[:hit.start(4)] + b"n\n" + content[hit.end(4):]
        if patched == content:
            return "nothing left to clear"
        new = repack(raw[s:e], patched)
        if new is None:
            return "will not fit without moving /Length, skipped"
        out = raw[:s] + new + raw[e:]

        shutil.copyfile(path, path + ".orig")
        tmp = tempfile.mktemp(suffix=".pdf")
        open(tmp, "wb").write(out)
        r = subprocess.run(["gs", "-q", "-o", path, "-sDEVICE=pdfwrite", "-dQUIET", tmp],
                           capture_output=True)
        os.remove(tmp)

        after = ink(path) if r.returncode == 0 else None
        if after is None or before is None or \
           abs(after[0] - before[0]) > 2 or abs(after[1] - before[1]) > 2:
            shutil.copyfile(path + ".orig", path)
            os.remove(path + ".orig")
            return f"VERIFY FAILED {before} -> {after}, restored"
        return "cleared"
    return "no white background found"


if __name__ == "__main__":
    args = sys.argv[1:]
    check = "--check" in args
    allwhite = "--all" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print(__doc__)
        sys.exit(1)
    for f in files:
        print(f"  {os.path.basename(f):28s} {clear(f, check, allwhite)}")
    if not check:
        print("\nEdits are bbox-verified, but LOOK at one on a coloured slide anyway:")
        print("a figure can keep its bbox and still lose an interior fill.")

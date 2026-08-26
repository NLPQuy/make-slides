#!/usr/bin/env python3
"""
checkslides.py -- build a beamer deck and refuse to call it done if any frame
overflows. Same gate as checkslides.sh, for machines without a POSIX shell.

Overfull \\vbox in a beamer frame means content ran off the bottom of the
slide. LaTeX reports it as a warning and still produces a PDF, which is
exactly why decks ship with text sliding under the page edge. This turns that
warning into a failure with the offending frame titles named.

Two things it does that the shell version does not, because both were needed
on Windows and neither costs anything elsewhere:

  * follows \\input{...} when auditing, so a deck split across files gets
    counted whole rather than reporting "0 em dashes" for a two-line main.tex;
  * calls lualatex directly instead of latexmk, which is not always on PATH
    in a TeX Live install driven from a GUI editor.

Usage:
    python checkslides.py slides.tex
"""
import os
import re
import subprocess
import sys

EXT_AUX = (".aux", ".log", ".nav", ".out", ".snm", ".toc", ".vrb")


def read_with_inputs(path, base_dir, seen=None):
    """Concatenate a .tex with everything it \\input's, one level of recursion
    per file. Used for the style audit only, never for the build."""
    seen = seen if seen is not None else set()
    real = os.path.abspath(path)
    if real in seen or not os.path.exists(real):
        return ""
    seen.add(real)
    out = []
    with open(real, encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = re.match(r"^\s*\\input\{([^}]+)\}", line)
            if m:
                sub = m.group(1)
                if not sub.endswith(".tex"):
                    sub += ".tex"
                out.append(read_with_inputs(os.path.join(base_dir, sub), base_dir, seen))
            else:
                out.append(line)
    return "".join(out)


def strip_comments(text):
    """Drop LaTeX comments. A comment ruler of dashes is not an em dash the
    audience reads, and a rule that cries wolf gets switched off."""
    return "\n".join(re.sub(r"(^|[^\\])%.*", r"\1", ln) for ln in text.splitlines())


def strip_environments(text):
    """Also drop tabular and tikzpicture bodies. Inside those the habits mean
    something different and the rules do not apply: marking the losing row of a
    table is data encoding, not the everything-is-bold failure, and
    font=\\footnotesize on a diagram node is a label size, the same call
    slidekit itself makes in \\figcap."""
    depth, keep = 0, []
    opener = re.compile(r"\\begin\{(tabular|tabularx|array|tikzpicture)\}")
    closer = re.compile(r"\\end\{(tabular|tabularx|array|tikzpicture)\}")
    for ln in text.splitlines():
        if opener.search(ln):
            depth += 1
        if depth == 0:
            keep.append(ln)
        if closer.search(ln):
            depth = max(0, depth - 1)
    return "\n".join(keep)


def build(tex, work_dir):
    base = os.path.splitext(os.path.basename(tex))[0]
    log = os.path.join(work_dir, base + ".log")
    pdf = os.path.join(work_dir, base + ".pdf")
    print("==> building %s" % os.path.basename(tex))
    for _ in (1, 2):
        subprocess.run(
            ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
             os.path.basename(tex)],
            cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if not os.path.exists(pdf):
        print("BUILD FAILED. Errors:")
        if os.path.exists(log):
            with open(log, encoding="utf-8", errors="ignore") as f:
                errs = [ln for ln in f if ln.startswith("! ")]
            print("".join(errs[:10]))
        sys.exit(1)
    return base, log


def frame_title_above(tex_lines, line_no):
    """LaTeX reports the overflow at the \\end{frame} line, so the frame title
    is the nearest \\begin{frame} above it. Name the frame, not the line
    number: nobody fixes an overflow by looking at a line number."""
    for i in range(min(line_no - 1, len(tex_lines) - 1), -1, -1):
        if r"\begin{frame}" in tex_lines[i]:
            m = re.search(r"\\begin\{frame\}(?:\[[^\]]*\])?\{(.*)", tex_lines[i].strip())
            if m:
                return m.group(1).rstrip("}")[:64] or "<untitled>"
            return "<untitled>"
    return "<untitled>"


def main():
    tex = sys.argv[1] if len(sys.argv) > 1 else "slides.tex"
    if not os.path.exists(tex):
        sys.exit("not found: %s" % tex)
    work_dir = os.path.dirname(os.path.abspath(tex)) or "."
    base, log_path = build(tex, work_dir)

    with open(log_path, encoding="utf-8", errors="ignore") as f:
        log = f.read()

    m = re.search(r"Output written on .*?\((\d+) pages?", log)
    print("==> built %s.pdf, %s slides" % (base, m.group(1) if m else "?"))

    # ------------------------------------------------------------ overflow --
    print("==> checking for overflow")
    over = re.findall(r"Overfull \\vbox \(([\d.]+)pt too high\) detected at line (\d+)", log)
    hbox = len(re.findall(r"Overfull \\hbox", log))
    fail = False

    if over:
        print()
        print("  !! %d frame(s) ran off the BOTTOM of the slide:" % len(over))
        with open(tex, encoding="utf-8", errors="ignore") as f:
            tex_lines = f.readlines()
        for pt, ln in over:
            print("     %8s over   line %-5s  %s"
                  % (pt + "pt", ln, frame_title_above(tex_lines, int(ln))))
        fail = True

    if hbox:
        print()
        print("  !  %d Overfull \\hbox -- content ran off the SIDE (often a long" % hbox)
        print("     unbreakable token: a URL, a \\texttt, or an unhyphenated term).")
        for ln in re.findall(r"Overfull \\hbox[^\n]*", log)[:10]:
            print("     " + ln.strip())

    # ------------------------------------------------------ style tripwires --
    print()
    print("==> style audit of %s" % os.path.basename(tex))
    body = strip_comments(read_with_inputs(tex, work_dir))
    prose = strip_environments(body)

    n_frame = len(re.findall(r"\\begin\{frame\}", body))
    counts = [
        ("frames", n_frame, None),
        ("font-shrink commands",
         len(re.findall(r"\\(small|footnotesize|scriptsize|tiny)\b", prose)),
         lambda v: v > 0 and "<- cut text instead of shrinking it"),
        ("em dashes", len(re.findall(r"(---|\u2014)", body)),
         lambda v: v > n_frame // 3 and "<- use full stops"),
        ("bold/colour marks", len(re.findall(r"\\(textbf|K|F)\{", prose)),
         lambda v: v > n_frame * 2 and "<- >2 per frame reads as no emphasis"),
        ("boxes",
         len(re.findall(r"\\begin\{(alert|example)?block\}|\\begin\{takeaway\}", body)),
         lambda v: v > n_frame and "<- more than one per frame"),
        (r"manual \vspace", len(re.findall(r"\\vspace", body)),
         lambda v: v > n_frame // 2 and "<- each one patches a layout bug"),
        (r"extra \definecolor", len(re.findall(r"\\definecolor", body)),
         lambda v: v > 0 and "<- palette is fixed in slidekit.sty"),
    ]
    for name, value, verdict in counts:
        note = "" if verdict is None else (verdict(value) or "ok")
        print("  %-34s %4d   %s" % (name, value, note))

    for ext in EXT_AUX:
        p = os.path.join(work_dir, base + ext)
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

    print()
    if fail:
        print("RESULT: FAIL (overflow). Fix before showing this to anyone.")
        sys.exit(1)
    print("RESULT: no vertical overflow.")


if __name__ == "__main__":
    main()

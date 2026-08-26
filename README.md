# make-slides

A Claude Code skill for building LaTeX beamer decks that do not overflow, do
not read as machine-written, and do not bury the audience in text.

It was distilled from an audit of two real progress-report decks. Counted on
prose, with comments, tables and diagrams excluded:

| | frames | font-shrink | em dashes | bold/colour | boxes | manual `\vspace` |
|---|---:|---:|---:|---:|---:|---:|
| Deck A | 28 | 89 | 38 | 144 | 40 | 28 |
| Deck B | 40 | 70 | 97 | 205 | 86 | 66 |
| Rebuilt with this skill | 21 | **0** | **0** | 25 | **0** | 8 |

Deck B also wrapped thirteen tables in `\resizebox`, which makes font size a
function of table width, so consecutive slides landed at different arbitrary
sizes.

This README is for humans. `SKILL.md` is what Claude loads.

## Install

```bash
git clone https://github.com/NLPQuy/make-slides ~/.claude/skills/make-slides
chmod +x ~/.claude/skills/make-slides/assets/*.sh \
         ~/.claude/skills/make-slides/assets/*.py
```

Then in any project: `/make-slides`, or just ask for slides and it triggers.

Updating later is `git pull` in that directory.

## Use it by hand

```bash
mkdir talk && cd talk
cp ~/.claude/skills/make-slides/assets/{slidekit.sty,checkslides.sh,croppanel.sh,clearbg.py} .
cp ~/.claude/skills/make-slides/assets/template.tex slides.tex
mkdir figures
chmod +x *.sh *.py
./checkslides.sh slides.tex
```

`checkslides.sh` is the gate. It exits non-zero while any frame overflows, and
names the frame rather than a line number. Do not ship a deck it has not passed.

### On Windows

The two `.sh` scripts need a POSIX shell, and both shell out to ghostscript,
which TeX Live does not ship. Two Python ports cover that. Same gate, same
output, same exit codes:

```powershell
copy assets\slidekit.sty,assets\checkslides.py,assets\croppanel.py,assets\clearbg.py .
copy assets\template.tex slides.tex
python checkslides.py slides.tex
```

`croppanel.py` uses PyMuPDF instead of ghostscript, so it needs no external
binary, and it auto-trims dead margin itself rather than leaving that to a
separate `pdfcrop` call. `clearbg.py` still needs ghostscript, because it
rewrites the content stream; it now finds `gswin64c` too.

## What is in here

| | |
|---|---|
| `SKILL.md` | Workflow and rules. Loaded into Claude's context. |
| `assets/slidekit.sty` | The style package. Fixed palette, one measured takeaway box, height- and width-budgeted figures. |
| `assets/checkslides.sh` | Build, fail on overflow, audit prose style. |
| `assets/checkslides.py` | Same gate, without a POSIX shell or latexmk. Also follows `\input{}`, so a deck split across files is audited whole. |
| `assets/croppanel.sh` | Cut one panel out of a multi-panel paper figure. |
| `assets/croppanel.py` | Same, via PyMuPDF instead of ghostscript. Auto-trims, and `--split RxC` cuts a whole grid in one call. |
| `assets/clearbg.py` | Strip the opaque white background out of an imported figure so it sits on any slide ground. |
| `assets/template.tex` | Starting deck. One frame shape, used for every frame. |
| `references/failure-catalog.md` | Every mistake this exists to prevent, with the measurement that caught it. Read when a deck looks wrong and you cannot say why. |

## Requirements

- **lualatex** or xelatex (the package uses `fontspec`)
- **metropolis** beamer theme
- **ghostscript** for `croppanel.sh`, `clearbg.py`, and for rasterising pages
- **pdfcrop** (TeX Live) to trim dead margin after cropping a panel
- **PyMuPDF** only if you use `croppanel.py` in place of `croppanel.sh`
- Fira Sans if you want the intended typeface; it falls back silently if absent

BasicTeX on macOS covers all of this. On Windows, where there is no shell and
no ghostscript, use `checkslides.py` and `croppanel.py` instead of the two
`.sh` scripts. `babel` is deliberately not required:
the package sets ragged-right with hyphenation off, so a deck in any language
builds on a minimal TeX Live.

## Licence

MIT. See `LICENSE`.

---
name: make-slides
description: Build LaTeX beamer decks for technical talks (paper presentations, progress reports, lab seminars, conference talks) that do not overflow, do not read as AI-generated, and do not drown the audience in text. Use whenever asked to make, fix, or review slides, a deck, a presentation, or a .tex beamer file. Ships a style package, a build-time overflow checker, and a figure-cropping tool.
---

# Making slides that people can actually read

A slide deck is not a shortened paper. It is a **visual script for a speaker**.
Almost every ugly deck comes from forgetting that and pouring the report onto
the slides.

## Workflow

1. **Read the source material fully** before writing any LaTeX. For a paper:
   every section file, not the abstract. You cannot write a one-line finding
   for a slide whose figure you have not looked at.
2. **Look at every figure.** Rasterise and open them:
   `gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r110 -sOutputFile=f.png fig.pdf`
   You are deciding what each figure proves. That decision is the slide.
3. **Ask the user three things before writing**: occasion and length (this sets
   the slide count: roughly 1.5 to 2 min per slide), language, and whether frame
   titles should be short labels or full assertion sentences. Do not guess;
   these change every slide.
4. **Copy `assets/` into the deck folder**: `slidekit.sty`, `checkslides.sh`,
   `croppanel.sh`, and `template.tex` as the starting `slides.tex`.
5. **Split multi-panel paper figures** with `croppanel.sh`, one panel per
   slide, and **open the preview PNG it writes**. Every bad crop is one nobody
   looked at.
6. **Write frames.** One shape only. See `assets/template.tex`.
7. **Run `./checkslides.sh slides.tex` and do not stop until it says
   `RESULT: no vertical overflow`.** Then rasterise the pages and *look at
   them*. The checker catches overflow; only your eyes catch a figure shrunk
   to a postage stamp or a hole in the middle of the layout.
8. **Show the user rendered pages and ask for feedback**, repeatedly, while
   there is still time to change the design. Do not present a finished deck
   for the first time at the end.

## The frame shape

Exactly one, used for every frame:

```latex
\begin{frame}{Label}                 % 2-4 words
  \takeaway{The finding, one line.}  % written FIRST
  \fig{evidence}                     % ONE piece of evidence
  \showtakeaway                      % emitted here, under the evidence
  \note{Everything else.}            % setup, caveats, what you will say
\end{frame}
```

`\takeaway` is declared at the top and emitted at the bottom on purpose. It
forces the conclusion to be written before the evidence, and it lets the
package **measure** the box and compute the figure's height budget from the
space actually left. That measurement is why frames stop overflowing.

## Rules

**Text**
- One base font size, set once in `\documentclass`. **Never** `\small`,
  `\scriptsize`, `\tiny` in the body. Text that does not fit gets cut.
- **Never `\resizebox` a table.** It is not a font size, it is "whatever size
  makes this fit", so consecutive tables land at different arbitrary sizes.
  Cut a column instead: usually the one holding a sentence, which belongs in
  the takeaway or `\note`.
- **Do not invent a translation for a term the audience already says in
  English.** Coining "mẻ dữ liệu" for *batch* or "độ trải" for *entropy* costs
  the listener a decode step and reads as translationese. Keep the term, gloss
  it once. This is the same failure as the old deck's "khả-năng-hồi".
- **Say a thing once per slide.** A notation table and an `\ann{}` label that
  both explain the same symbol in the same words is one of them wasted; make
  the label do work the table did not.
- Write **keywords, not sentences**. Drop copulas and connectives, keep the
  technical noun phrases, use `$\to$` and `:` to carry the logic. `Cầu gradient
  chứ không phải cầu Euclid. Gradient tự cân hướng theo ảnh hưởng lên output.`
  not `Việc chọn hình cầu gradient thay vì hình cầu Euclid là có chủ ý, bởi vì…`
- **No em dashes.** They are the loudest AI tell in prose. A full stop or a
  colon is almost always what you meant. `checkslides.sh` counts them.
- At most **two** bold/coloured marks per frame. Everything emphasised means
  nothing emphasised.
- No ALL-CAPS for emphasis. Shouting is what you do when the layout failed.
- Provenance, sample sizes, protocol, caveats → `\note{}`. If a figure needs a
  paragraph explaining how to read it, either the figure is wrong or that
  paragraph is the takeaway and belongs in the box.

**Maths**
- **Never display a formula whose symbols have not been introduced.** Give the
  notation its own frame first: one short table, symbol on the left, plain
  meaning on the right. Then show the formula.
- **Annotate every operator** with `\ann{}` under an `\underbrace`. A nested
  `min-max-sup` is three separate ideas; unlabelled it is one wall. Say what
  each one ranges over and why.
- **Introduce a symbol before the frame that needs it, not after.** Sweep the
  deck in order and list where each symbol first appears on a slide; anything
  used before its notation frame is a bug. The outline is the one exception:
  previewing notation there is its job.
- **Anchor an abstract sum with a count.** "n=3 binary labels, so 8 possible
  labellings, and Z adds all 8" does more than another sentence of prose.
- "They can read it" is false at 4 metres, at the speaker's pace. Either
  annotate the formula or do not show it.

**Colour**

Three decisions, each noticed only when wrong. All are already made in
`slidekit.sty`; change them together or not at all.

- **The neutral must be a tint of the accent, never an unrelated beige.** This
  is the highest-leverage colour decision in a deck. A neutral that relates to
  nothing else on the slide reads as dirt, not restraint. The takeaway box,
  the table header band, and the progress-bar track all use the same tint.
- **Ground is ivory, not white.** Pure white glares under a projector and makes
  everything on it look clinical. `#FAF9F6` fixes it invisibly. Cost: figures
  lifted from a paper carry an opaque white background that then shows as a
  bright rectangle, so `\fig` puts them on an evenly padded white **card**.
  If you control the figures, render them `transparent=True` and `\figcardfalse`.
- **Sample `key` from the figures the deck actually shows**, then darken until
  it clears 4.5:1 as body text. An accent merely *near* the figure's colour
  makes the slide and the chart look like two designs stapled together.
  Sampling recipe and contrast check: `references/failure-catalog.md`.
- Six colours total. Adding a seventh is the first step back to the
  fifteen-colour deck nobody could read.

**Figures**
- One figure per slide. Never a figure and a table encoding the same numbers.
- Figures that must be compared go **side by side**, never stacked. A stacked
  pair wastes the width of a 16:9 frame and defeats the comparison.
- Crop paper panels apart rather than showing three and saying "look at the
  middle one".
- Crop off a panel's internal title when the frame title already says it.
- **Always `pdfcrop --margins 2` after cropping a panel.** Hand-picked crop
  coordinates leave dead margin: two panels here wasted 50% of their area on
  white before this step, 6% after.
- **Run `clearbg.py` on every imported figure.** Paper figures carry an opaque
  white rectangle that shows as a bright panel on any ground but pure white.
  `--all` also removes the axes patch. Then `\figcardfalse`, since the white
  card only existed to hide that rectangle.
- **Balance two side-by-side figures by visual weight, not by one dimension.**
  Matching heights when the aspect ratios differ five-fold makes one of them
  postage-stamp sized. Reshape the content instead: a 5x2 grid of thumbnails
  balances a square plot, a 5x1 strip does not.
- **Sweep every composite, not just the obvious one.** The rule to split panels
  was already written down and still got applied to only one of two figures.
- A pipeline or a mechanism is a **diagram**, not a bullet list. Keep TikZ node
  text to three or four words; a node holding a sentence will demand
  `\scriptsize` and you will give in.

**The outline slide**
- Never `\tableofcontents`. It is four nouns down the left of an empty slide.
- Make the outline **the argument**, and keep it minimal: one row per section,
  three short columns, nothing else. Number, section name, and the single
  symbol or figure that section delivers. The audience meets the notation once
  before it matters.
- No gloss column, no small-caps markers, no second row per section. A richer
  version was built and rejected as cluttered: it is slide two and every extra
  element is one the audience has to skip.
- Numbered circles on a connector line, cards in a row, anything that looks
  like a strategy deck: a technical audience reads notation, not iconography.
- Check the section markers against the real `\section` commands.

**Layout**
- The frame body is one solid block that beamer centres, so a frame **grows
  from the middle outwards** as content is added. Do not try to pin the
  takeaway to the bottom with `\vfill`: beamer has already placed its own fills
  around the body, and the extra ones split the slack 2:1:1, stranding the
  content high with a hole beneath it.
- `\begin{columns}[c]`, not `[T]`, whenever text is paired with a **figure**.
  They will never be the same height, and `[T]` leaves the short column hanging
  at the top. Keep `[T]` only for text against text.
- Never re-typeset metropolis' `frametitle` template. Beamer reserves the body
  height against the theme's own title box; a taller hand-rolled one pushes
  *every* frame down and the deck overflows for reasons that look like content.
  Recolour, never re-typeset.
- `{\centering ...\par}`, never `\begin{center}`. The environment adds ~20pt
  of vertical space no height budget accounts for.
- Every manual `\vspace` is a patch over a layout bug. A handful is fine; one
  per frame means the structure is wrong.
- `\graphicspath` points inside the deck folder. Never at another project's
  results directory.

**Hygiene**
- No commented-out `\iffalse` frames, no `\today` on a dated report, no dead
  colour definitions.
- The last slide is the one people stare at longest during Q&A. Put the
  takeaway and your contact on it, not the word "Thanks".

## Tools

| Tool | Use |
|---|---|
| `checkslides.sh slides.tex` | Build, fail on any overflowing frame **naming the frame**, print a style audit. The gate. |
| `croppanel.sh fig.pdf` | Print a figure's bounding box. |
| `croppanel.sh fig.pdf out.pdf x0 y0 x1 y1` | Crop one panel and write a preview PNG. Open it. |

`checkslides.sh` turns LaTeX's `Overfull \vbox` warning, which otherwise
produces a PDF anyway and is exactly why decks ship with text under the page
edge, into a hard failure with the frame title named.

## Before saying it is done

- `checkslides.sh` reports no overflow and a clean style audit.
- You have rasterised the pages and looked at every one.
- No frame has a hole in the middle, a stamp-sized figure, or a half-drawn rule.
- Every number on a slide traces back to the source, in the same rounding.

`references/failure-catalog.md` lists the concrete failures this skill was
built from, including the ones made while building it. Read it when a deck
looks wrong and you cannot say why.

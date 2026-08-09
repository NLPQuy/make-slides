# Failure catalogue

Two sources: an audit of a real 28-frame progress-report deck (`Template_1.tex`),
and the mistakes made while building the reference deck in this repo. The second
list matters more: those are the ones that get made *while following the rules*.

---

## Part 1. Measured on the 28-frame deck

| Symptom | Count | What it actually means |
|---|---:|---|
| `\small` / `\scriptsize` / `\tiny` | 91 | Base was already 8pt. Text was being **compressed to fit** instead of cut. |
| `\textbf` + colour macros | 205 | ~7 per frame. Emphasising everything emphasises nothing. |
| `---` em dash | 50 | ~2 per frame, used as glue where a full stop belonged. Loudest AI tell. |
| `\definecolor` | 15 | The eye cannot hold 15 colours. Four is the ceiling. |
| block / alertblock / exampleblock | 40 | 1.4 boxes per frame, **boxes nested inside boxes**, no consistent meaning. |
| manual `\vspace` | 28 | One per frame. Each one patches an overflow rather than fixing it. |
| "How to read this" boxes | 17 | Present on 60% of frames. |

**Structural failures, worse than the counts:**

1. **One layout repeated 14 times.** Columns 0.56/0.44, figure left, table
   right, explanation box below. The audience recognises the mould by slide 3
   and stops looking.
2. **Figure and table encoding the same data.** The curve shows the trajectory;
   the table beside it repeats the endpoints. Two encodings, double reading cost.
3. **The "how to read this" box is proof the design failed.** If a figure needs
   a paragraph of prose to be legible, either the figure is wrong or that
   paragraph is the finding and belongs in the frame title.
4. **Titles that compress three ideas.** *"Trapped weights: gradient starvation
   & recoverability, Permuted-MNIST"* is topic + two metrics + dataset tag.
5. **Hard-coded `height=0.6\textheight`** plus a legend plus a 3-line box, on a
   frame whose title bar already took 15%. It fit by luck, until it did not.
6. **ALL-CAPS for emphasis.** Shouting is what happens when the layout cannot
   create hierarchy.
7. **Shipped rubbish**: `\graphicspath` pointing at another project's results
   directory, a dead frame inside `\iffalse`, `\today` on a dated report, and a
   final `[standout]` slide reading only "Thanks", wasting the slide people
   stare at longest during Q&A.

---

## Part 2. Mistakes made while building the replacement

These reproduced *while consciously trying to avoid part 1*. Expect them.

### Making it fit by shrinking

**`\resizebox{0.99\linewidth}{!}{...}` around a table** is the worst version of
shrinking text to fit, and the hardest to see in the source. It is not a font
size, it is "whatever size makes this table fit", so two tables on consecutive
slides end up at two different arbitrary sizes and neither matches the body.
The audited deck used it thirteen times. → Cut columns until the table fits at
the deck's one font size. The column most often worth cutting is the one
holding a sentence; that sentence is the takeaway or a `\note`.

### Overflow that is not about content

**Re-typesetting `frametitle`.** A hand-rolled `\setbeamertemplate{frametitle}`
was ~15pt taller than metropolis' own. Beamer reserves the body's `\textheight`
against the *theme's* title box, so **every frame in the deck** overflowed by
that constant. It looked like a content problem on seven different frames.
→ Recolour the theme, never re-typeset it.

**`\begin{center}`.** The environment adds `\topsep + \partopsep` above and
below, about 20pt that no height budget accounts for, and invisible in the
source. → `{\centering ...\par}`.

**Metropolis' own title page** overflows a `[plain]` frame by 15.64pt on an
empty four-line deck. Verified minimal. → absorbed once in `\titleframe`; do
not leave it in the report, or you learn to ignore the report.

**Discarded glue.** `\vfill`, and even `\vspace*{\fill}`, at the very top of
a frame body is silently dropped, because glue at the head of a vertical list is
discardable. The intended vertical centring did nothing and the hole stayed.
→ `\hrule height 0pt\vspace*{\fill}`; a zero-height rule is not discardable.

**Em-only slack.** A budget slack of `4em` was enough at 11pt and 0.7pt short at
8pt, because frame padding does not scale with the base size. → part em, part
absolute.

**Fighting beamer's own centring.** Beamer frames default to `c`, which already
puts a `\vfill` above and below the body. Adding two more to pin the takeaway
to the bottom gives four competing fils: the slack splits 2:1:1 and the content
ends up stranded high with a hole under it. Switching the class to `t` is worse:
the body then has natural height, so `\vfill` has nothing to stretch against
and the takeaway floats mid-slide. → Leave the body a solid block and let
beamer centre it. The frame grows from the middle outwards, which is also what
people mean when they say a slide looks tidy.

**`[T]` columns pairing text with a figure.** The figure column runs half again
as tall; `[T]` pins the text to the top of a column that extends well below it,
and the text reads as stranded. → `[c]` whenever one column is a figure.

### Figures

**Cropping without looking.** A hero-panel crop sliced the panel's title in
half; the sliced glyphs shipped onto a slide. `croppanel.sh` prints
`preview at ... <- open it` for exactly this reason, and it was ignored.
→ Open the preview. Every time.

**`trim={0.02\width}` does not work** inside `\includegraphics`; `\width` is
undefined there and `adjustbox`'s `export` option does not rescue it.
→ Crop to a separate PDF with ghostscript, where you can see the result.

**Stacked panels.** A paper's vertically-stacked two-panel figure, dropped
straight onto a 16:9 slide, leaves both panels small, both squeezed, and the
comparison impossible. → Split and place side by side.

### Layout and reading

**A takeaway box long enough to eat the slide.** A three or four line box left the figure
at a third of its useful size. → One line. If it will not fit in one line, the
frame has more than one point and needs splitting.

**An empty-titled `alertblock`** still typesets its title row, leaving a dead
band of colour across the top of the box. → Build the box by hand: text,
padding, and a coloured rule down the left edge.

**A progress bar with an invisible track** reads, at slide 9 of 18, as a rule
someone forgot to finish. → Give the track a visible grey and thicken both.

**Sentences instead of keywords.** The first draft was grammatical Vietnamese
prose. Correct, and still too much to read while listening. → Drop copulas and
connectives, keep the technical noun phrases, let `$\to$` and `:` carry the
logic.

### The outline slide

**`\tableofcontents` is four nouns down the left of an empty slide.** It fills a
third of the width, says nothing the section titles will not say again, and is
the most skippable slide in the deck.

**Consulting vocabulary is not research vocabulary.** Numbered circles joined by
a connector line, four coloured cards in a row: these read as a strategy deck
and were rejected on sight by a researcher with "chua du vibe research". A
technical audience reads notation, not iconography.

**And then over-building the replacement.** The first fix put six rows, three
columns, a prose gloss on every row and small-caps section markers on slide
two. Rejected in one word: cluttered. An outline earns attention by being
scannable in three seconds, not by being informative.

→ Make the outline the ARGUMENT, in four rows and three short columns. One row per step: symbol or claim on the left,
plain-language gloss on the right, section marker in the margin. Every symbol
the audience will meet later appears there first, which is the only job that
slide can usefully do. Check the section markers against the real `\section`
commands; an outline promising a §5 that does not exist is a factual error on
slide two.

### Two habits worth stealing

Both from the audited progress deck, which got these right while getting the
layout wrong.

**A provenance macro.** `\src{359 khung / lan chay sang loc}` under every table,
so a number on a slide can always be traced to the run that produced it. The
skill's `\takeaway[...]` optional argument is the same idea; use it on every
frame that shows a number. The original applied it to five tables out of
thirteen, which is the part to not copy.

**Diagrams instead of bullet lists.** Twelve hand-built TikZ pipelines rather
than twelve `itemize` blocks. A five-box pipeline says in one glance what five
bullets say in fifteen seconds. Keep node text to three or four words: the
original packed a full sentence into several nodes and each one then needed
`\scriptsize`.

### Maths nobody can read

**Jumping straight to the formula.** A theory frame opened with

    R**(Theta) = min_Q max_{x,y} sup_theta log P_theta(y|x) / Q(y|x)

where `Q`, `x^n`, `y^n` and `Theta` had never appeared on a slide, and where
none of the three nested operators was explained. It passed every layout check
and taught nothing: the audience spends the frame decoding notation instead of
listening. The reviewer's words: "nhay thang vao cong thuc va nhin chang hieu
may cai term ca".

→ Three frames, not one:
1. **Notation.** A short table, symbol on the left, plain meaning on the right,
   plus one sentence saying what the problem even is.
2. **The formula, every operator annotated** with `\ann{}` under an
   `\underbrace`. `min_Q` is "the best predictor we can pick", `max_{x,y}` is
   "on the worst data", `sup_theta` is "graded against the model that fits it
   best". Three ideas, three labels.
3. **The closed form, anchored with a count.** "n=3 binary labels gives 8
   possible labellings, and Z adds all 8" lands where another paragraph of
   prose does not.

The cost is two extra frames. The alternative is one frame that does nothing.

**And then only fixing the frame that was pointed at.** The same defect sat in
three more frames: `theta_0`, `eta`, `epsilon` and the loss in Definition 3.1;
`\hat\theta_{y^n}`, `H(.)` and the expectation in Theorem 3.2. `\hat\theta_{y^n}`
was the worst, since the whole proof turns on it and it was never defined.
→ When one frame is caught, sweep the whole deck: list every symbol and the
frame it first appears on, and check each against its notation frame. Five
minutes of scripting, and it finds the ones nobody complained about yet.

**Translationese.** Rendering *batch* as "mẻ dữ liệu" and *entropy* as "độ
trải" is the same failure as the audited deck's "khả-năng-hồi": a coined phrase
the audience must decode, where they already know the English word. Keep the
term, gloss it once.

**Saying it twice.** A notation table row and an `\ann{}` label under the same
symbol, in the same words. One of the two is wasted; make the label carry what
the table did not.

### Imported figures carry their own background

**An opaque white rectangle.** Matplotlib draws one over the whole page unless
you passed `transparent=True`, which you did not, and you no longer have the
plotting script. On an ivory ground it reads as a bright panel with hard edges
and the figure looks pasted on. `assets/clearbg.py` finds that fill and turns
its paint operator into a no-op. Three things made it harder than it looks:

- `pdfcrop` wraps the page in a Form XObject, burying the fill a level down.
  Flatten through `gs -sDEVICE=pdfwrite` first.
- Patching `/Length` after recompressing is a minefield: it may be a direct
  number or an indirect reference, and a generated PDF can carry the same
  object number twice so the reference resolves to an xref object. Sidestep it
  entirely: `f` -> `n` leaves the DECOMPRESSED length unchanged, so recompress
  and pad with newlines to exactly the original byte count. Nothing moves.
- The axes patch is a second white fill drawn later. `--all` clears those too.

**A tool that edits binary assets must verify itself.** The first version of
`clearbg.py` had none, and silently blanked three of eight figures. Nothing in
the build failed: the deck compiled, the gate passed, and the damage was only
visible as an empty rectangle on a rendered slide. It now compares the ink
bounding box before and after and restores the original on any mismatch.

**Dead margin inside the figure.** Panels cropped by hand-picked coordinates
wasted half their area on white: `hero_a` measured 49.8%. `pdfcrop --margins 2`
after every crop takes that to about 6%, which is the margin you asked for.

**Balancing a pair.** Two figures side by side should match in visual weight,
which is not the same as matching one dimension. Setting equal heights on a 5:1
strip and a 1.4:1 plot made the plot tiny. The fix was to reshape the content:
back to a 5x2 thumbnail grid, which is roughly square and sits comfortably
beside a square plot.

### Colour

**A neutral that relates to nothing.** The first palette used beige `#E9E7E1`
for the takeaway box against a white ground and a teal-blue accent. Every
individual colour was defensible and the result looked dirty, because the box
belonged to no family. → Make the neutral a pale tint of the accent. Single
biggest visual improvement in the whole exercise, and it costs one hex value.

**An accent that is nearly the figure's colour.** `#1C6E8C` against bars drawn
in `#2484A8`: close enough that nobody names the problem, far enough that the
text and the chart look like two designs stapled together. → Sample, then
darken only for contrast.

**Ivory ground versus imported figures.** Dropping the ground to `#FAF9F6`
removes projector glare, and immediately turns every paper figure's opaque
white background into a bright rectangle with ragged margins. The proper fix is
`savefig(transparent=True)`, which needs plotting scripts you usually do not
have. → Put figures on an evenly padded white card, so the white is a decision
rather than a mismatch. Remember the card's padding comes out of the height
budget, or every figure frame overflows by exactly twice the padding.

**A dark deck with borrowed figures is not an option.** Same problem, an order
of magnitude worse: every white figure background becomes a glare panel. Only
choose a dark ground if you are generating every figure yourself.

---

## Sampling accents from your own figures

Matplotlib defaults will not match whatever palette you invent, and the mismatch
quietly costs the audience the link between a coloured word and a coloured line.

```bash
gs -dNOPAUSE -dBATCH -dUseCropBox -sDEVICE=png16m -r120 \
   -sOutputFile=/tmp/f.png figures/hero.pdf
```

Then count saturated pixels (`max-min > 40`) bucketed to the nearest 12, and
take the top two. Darken each until it clears 4.5:1 against white:

```python
def lum(h):
    c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [x/12.92 if x <= .03928 else ((x+.055)/1.055)**2.4 for x in c]
    return .2126*c[0] + .7152*c[1] + .0722*c[2]

contrast = (lum(hex_colour) + .05) / (lum("FFFFFF") + .05)   # want >= 4.5
```

A figure's own blue is often fine as a 3pt line and too weak as 8pt text: the
worked example measured 4.25:1 at `#2484A8` and shipped `#1C6E8C` at 5.7:1.

---

## Slide budget

Roughly 1.5–2 minutes per content slide, section pages excluded.

| Occasion | Content slides |
|---|---|
| Conference talk, 12 min | 8–10 |
| Reading group, 20 min | 12–15 |
| Lab seminar, 40 min | 18–22 |

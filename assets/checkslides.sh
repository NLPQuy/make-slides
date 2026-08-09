#!/usr/bin/env bash
# ============================================================================
#  checkslides.sh -- build a beamer deck and refuse to call it done if any
#  frame overflows.
#
#  Overfull \vbox in a beamer frame means content ran off the bottom of the
#  slide. LaTeX reports it as a warning and still produces a PDF, which is
#  exactly why decks ship with text sliding under the page edge. This turns
#  that warning into a failure with the offending frame titles named.
#
#  Usage: ./checkslides.sh slides.tex
# ============================================================================
set -uo pipefail

TEX="${1:-slides.tex}"
BASE="${TEX%.tex}"

echo "==> building $TEX"
latexmk -lualatex -interaction=nonstopmode -halt-on-error "$TEX" >/dev/null 2>&1
STATUS=$?

if [[ ! -f "$BASE.pdf" ]]; then
  echo "BUILD FAILED. Errors:"
  grep -A4 -E '^! ' "$BASE.log" | head -40
  exit 1
fi

PAGES=$(grep -oE '^Output written on .* \(([0-9]+) pages' "$BASE.log" | grep -oE '[0-9]+ pages' | grep -oE '[0-9]+')
echo "==> built $BASE.pdf, $PAGES slides"

# ---------------------------------------------------------------- overflow --
# Beamer emits the frame title just before typesetting it, so the most recent
# "Overfull \vbox ... has occurred while \output is active" maps to the frame
# whose page number precedes it. Simplest reliable signal: page numbers.
echo "==> checking for overflow"
OVER=$(grep -n 'Overfull \\vbox' "$BASE.log" | grep -v 'has occurred while \\output is active' || true)
OVERBOX=$(grep -c 'Overfull \\vbox' "$BASE.log" || true)
UNDER=$(grep -c 'Overfull \\hbox' "$BASE.log" || true)

FAIL=0
if [[ "$OVERBOX" -gt 0 ]]; then
  echo
  echo "  !! $OVERBOX frame(s) ran off the BOTTOM of the slide:"
  # LaTeX reports "detected at line N" -- N is the \end{frame} line, so the
  # frame title is the nearest \begin{frame} above it. Name the frame, not
  # the line number: nobody fixes an overflow by looking at a line number.
  grep -oE 'Overfull \\vbox \([0-9.]+pt too high\) detected at line [0-9]+' "$BASE.log" \
  | while read -r line; do
      PT=$(echo "$line"  | grep -oE '\([0-9.]+pt' | tr -d '(')
      LN=$(echo "$line"  | grep -oE '[0-9]+$')
      TITLE=$(awk -v n="$LN" 'NR<=n && /\\begin\{frame\}/{t=$0} END{print t}' "$TEX" \
              | sed -E 's/.*\\begin\{frame\}\{?//; s/\}[[:space:]]*$//' | cut -c1-64)
      printf '     %8s over   line %-5s  %s\n' "$PT" "$LN" "${TITLE:-<untitled>}"
    done
  FAIL=1
fi
if [[ "$UNDER" -gt 0 ]]; then
  echo
  echo "  !  $UNDER Overfull \\hbox -- content ran off the SIDE (often a long"
  echo "     unbreakable token: a URL, a \\texttt, or an unhyphenated term)."
  grep 'Overfull \\hbox' "$BASE.log" | head -10
fi

# --------------------------------------------------------- style tripwires --
# The habits that made the old deck unreadable. Counted, not judged.
echo
echo "==> style audit of $TEX"
audit () { printf '  %-34s %4s   %s\n' "$1" "$2" "$3"; }

# Two passes, because the rules are about PROSE.
#
# BODY   drops LaTeX comments. A comment ruler of dashes is not an em dash the
#        audience reads, and a rule that cries wolf gets switched off.
# PROSE  additionally drops tabular and tikzpicture bodies. Inside those, the
#        habits mean something different and the rules do not apply:
#          - marking the losing row of a table is data encoding, not the
#            "everything is bold so nothing is" failure;
#          - `font=\footnotesize` on a diagram node is a label size, the same
#            call slidekit itself makes in \figcap, not prose shrunk to fit.
#        Counting these as violations trains you to ignore the audit, which
#        costs more than the false positives save.
BODY=$(sed -E 's/(^|[^\\])%.*/\1/' "$TEX")
PROSE=$(printf '%s' "$BODY" | awk '
  /\\begin\{(tabular|tabularx|array|tikzpicture)\}/ { d++ }
  d == 0 { print }
  /\\end\{(tabular|tabularx|array|tikzpicture)\}/   { if (d > 0) d-- }')

count  () { printf '%s' "$BODY"  | grep -oE "$1" | wc -l | tr -d ' '; }
countp () { printf '%s' "$PROSE" | grep -oE "$1" | wc -l | tr -d ' '; }

N_SHRINK=$(countp '\\(small|footnotesize|scriptsize|tiny)\b')
N_BOLD=$(countp '\\(textbf|K|F)\{')
N_DASH=$(count '(---|—)')
N_BLOCK=$(count '\\begin\{(alert|example)?block\}|\\begin\{takeaway\}')
N_FRAME=$(count '\\begin\{frame\}')
N_VSPACE=$(count '\\vspace')
N_COLOR=$(count '\\definecolor')

audit "frames"                "$N_FRAME"  ""
audit "font-shrink commands"  "$N_SHRINK" "$([[ $N_SHRINK -gt 0 ]] && echo '<- cut text instead of shrinking it' || echo ok)"
audit "em dashes"             "$N_DASH"   "$([[ $N_DASH -gt $((N_FRAME/3)) ]] && echo '<- use full stops' || echo ok)"
audit "bold/colour marks"     "$N_BOLD"   "$([[ $N_BOLD -gt $((N_FRAME*2)) ]] && echo '<- >2 per frame reads as no emphasis' || echo ok)"
audit "boxes"                 "$N_BLOCK"  "$([[ $N_BLOCK -gt $N_FRAME ]] && echo '<- more than one per frame' || echo ok)"
audit "manual \\vspace"        "$N_VSPACE" "$([[ $N_VSPACE -gt $((N_FRAME/2)) ]] && echo '<- each one patches a layout bug' || echo ok)"
audit "extra \\definecolor"    "$N_COLOR"  "$([[ $N_COLOR -gt 0 ]] && echo '<- palette is fixed in slidekit.sty' || echo ok)"

echo
if [[ $FAIL -eq 1 ]]; then
  echo "RESULT: FAIL (overflow). Fix before showing this to anyone."
  exit 1
fi
echo "RESULT: no vertical overflow."

#!/usr/bin/env bash
# ============================================================================
#  croppanel.sh -- cut one panel out of a multi-panel paper figure.
#
#  Paper figures are composed for a two-column page: three panels side by
#  side, 7pt labels, meant to be read at 30 cm. Projected, that becomes three
#  competing images none of which is legible, and the speaker ends up saying
#  "look at the middle one" -- which is the audience's cue to stop looking.
#
#  One panel per slide. Crop, don't shrink.
#
#  Usage:
#    ./croppanel.sh figures/hero_figure.pdf          # print the bounding box
#    ./croppanel.sh figures/hero_figure.pdf out.pdf x0 y0 x1 y1
#
#  Workflow: run with one argument to get the bbox, guess panel boundaries as
#  fractions of the width, crop, then rasterise and LOOK at the result before
#  putting it on a slide. Getting it wrong by 20bp swallows an axis label.
# ============================================================================
set -euo pipefail

IN="$1"

if [[ $# -eq 1 ]]; then
  echo "bounding box of $IN:"
  gs -q -dNOPAUSE -dBATCH -sDEVICE=bbox "$IN" 2>&1 | head -2
  echo
  echo "crop with:  $0 $IN out.pdf x0 y0 x1 y1"
  exit 0
fi

OUT="$2"; X0="$3"; Y0="$4"; X1="$5"; Y1="$6"

gs -q -o "$OUT" -sDEVICE=pdfwrite -dQUIET \
   -c "[/CropBox [$X0 $Y0 $X1 $Y1] /PAGES pdfmark" -f "$IN"

PNG="${OUT%.pdf}.preview.png"
gs -dNOPAUSE -dBATCH -dUseCropBox -sDEVICE=png16m -r120 \
   -sOutputFile="$PNG" "$OUT" >/dev/null 2>&1

echo "wrote $OUT"
echo "preview at $PNG  <- open it. Check no axis label or legend got cut."

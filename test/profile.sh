#!/usr/bin/env bash
#
# Create a profile trace and output PDF

set -e

cd "$(dirname "$0")/.." || exit 1

if ! command -v gprof2dot; then
  echo "Install gprof2dot via pip!"
  exit 1
fi

rm -f test/output*.cprof test/output*.pdf

echo "Profiling"
poetry run \
  python3 \
  -m cProfile \
      -s cumtime \
      -o output.cprof \
  siti_tools/__main__.py \
      videos/foreman_cif.y4m

gprof2dot -f pstats -s output.cprof -n 1 | \
    dot -Tpdf -o output.pdf

echo "Done"

#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.." || exit 1

outDir=test/ground_truth

for f in test/videos/[A-Z]*.y4m; do
  if [[ "$f" == *"10bit"* ]]; then
    extraArgs="--bit-depth 10"
  fi
  bn="$(basename "$f")"
  outFile="${bn%%.y4m}.json"
  python3 -m siti_tools "$f" --color-range full $extraArgs > "$outDir/$outFile"
done

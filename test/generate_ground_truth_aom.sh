#!/usr/bin/env bash

set -e
set -x

cd "$(dirname "$0")/.." || exit 1

outDir=test/ground_truth

# AOM content starts with an uppercase letter
for f in test/videos/[A-Z]*.y4m; do
  if [[ "$f" == *"10bit"* ]]; then
    extraArgs="--bit-depth 10"
  fi
  bn="$(basename "$f")"
  outFile="${bn%%.y4m}.json"
  python3 -m siti_tools "$f" --color-range full $extraArgs > "$outDir/$outFile"
done

# all others
for f in test/videos/[a-z]*.y4m; do
  extraArgs=""
  if [[ "$f" == *"10bpp"* ]]; then
    extraArgs="$extraArgs --bit-depth 10"
  fi
  if [[ "$f" != *"limited"* ]]; then
    extraArgs="$extraArgs --color-range full"
  fi
  bn="$(basename "$f")"
  outFile="${bn%%.y4m}.json"
  python3 -m siti_tools "$f" $extraArgs > "$outDir/$outFile"
done

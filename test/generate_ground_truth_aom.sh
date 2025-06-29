#!/usr/bin/env bash

set -e
set -x

cd "$(dirname "$0")/.." || exit 1

outDir=test/ground_truth

# Define AOM content files explicitly
aom_files=(
  "FourPeople_480x270_60.y4m"
  "ParkJoy_480x270_50.y4m"
  "SparksElevator_480x270p_5994_10bit.y4m"
  "SparksTruck_2048x1080_5994_hdr10.y4m"
)

# Process AOM content
for bn in "${aom_files[@]}"; do
  f="test/videos/$bn"
  if [[ -f "$f" ]]; then
    extraArgs=""
    if [[ "$f" == *"10bit"* ]] || [[ "$f" == *"hdr10"* ]]; then
      extraArgs="--bit-depth 10"
    fi
    if [[ "$f" == *"hdr10"* ]]; then
      extraArgs="$extraArgs --hdr-mode hdr10"
    fi
    outFile="${bn%%.y4m}.json"
    python3 -m siti_tools "$f" --color-range full $extraArgs > "$outDir/$outFile"
  fi
done

# Process all other y4m files
for f in test/videos/*.y4m; do
  bn="$(basename "$f")"
  # Skip if it's an AOM file
  if [[ " ${aom_files[@]} " =~ " ${bn} " ]]; then
    continue
  fi
  
  extraArgs=""
  if [[ "$f" == *"10bpp"* ]]; then
    extraArgs="$extraArgs --bit-depth 10"
  fi
  if [[ "$f" != *"limited"* ]]; then
    extraArgs="$extraArgs --color-range full"
  fi
  outFile="${bn%%.y4m}.json"
  python3 -m siti_tools "$f" $extraArgs > "$outDir/$outFile"
done

# Process legacy files
legacy_files=(
  "foreman_cif.y4m"
  "full-range.y4m"
  "limited-range.y4m"
)

for bn in "${legacy_files[@]}"; do
  f="test/videos/$bn"
  if [[ -f "$f" ]]; then
    extraArgs="--legacy"
    if [[ "$f" != *"limited"* ]]; then
      extraArgs="$extraArgs --color-range full"
    fi
    outFile="${bn%%.y4m}-legacy.json"
    python3 -m siti_tools "$f" $extraArgs > "$outDir/$outFile"
  fi
done

#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

numFrames="3"
metadataPrint="signalstats,metadata=print"

# a pure black frame
ffmpeg -y -f lavfi -i color=black:size=320x240 -frames:v "$numFrames" -pix_fmt yuv420p videos/black.y4m

# a pure white frame
ffmpeg -y -f lavfi -i color=white:size=320x240 -frames:v "$numFrames" -pix_fmt yuv420p videos/white.y4m

# generate random noise
ffmpeg -y -f lavfi -i nullsrc=size=320x240 -filter:v "geq=random(1)*255:128:128,$metadataPrint" -frames:v "$numFrames" -pix_fmt yuv420p videos/noise.y4m

# generate full range output ("pc" in ffmpeg)
ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=full,$metadataPrint" -frames:v "$numFrames" -pix_fmt yuv420p videos/full-range.y4m

# generate limited range output ("tv" in ffmpeg)
ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=limited,$metadataPrint" -frames:v "$numFrames" -pix_fmt yuv420p videos/limited-range.y4m

# checkerboard pattern, 1x1px
ffmpeg -y -f lavfi -i color=white:size=320x240 -f lavfi -i color=black:size=320x240 -filter_complex "[0:v][1:v]blend=all_expr='if(eq(mod(X,2),mod(Y,2)),A,B)'" -frames:v "$numFrames" -pix_fmt yuv420p videos/checkerboard-1x1.y4m

# checkerboard pattern, 8x8px
ffmpeg -y -f lavfi -i color=white:size=320x240 -f lavfi -i color=black:size=320x240 -filter_complex "[0:v][1:v]blend=all_expr='if(eq(mod(floor(X/32),2),mod(floor(Y/32),2)),A,B)'" -frames:v "$numFrames" -pix_fmt yuv420p videos/checkerboard-8x8.y4m

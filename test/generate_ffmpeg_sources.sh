#!/usr/bin/env bash

set -e

cd "$(dirname "$0")" || exit 1

# a pure black frame
ffmpeg -y -f lavfi -i color=black:size=320x240 -frames:v 3 -pix_fmt yuv420p videos/black.y4m

# a pure white frame
ffmpeg -y -f lavfi -i color=white:size=320x240 -frames:v 3 -pix_fmt yuv420p videos/white.y4m

# generate random noise
# disabled since it cannot be done reproducibly
# ffmpeg -y -f lavfi -i nullsrc=size=320x240 -filter:v "geq=random(1)*255:128:128,signalstats,metadata=print" -frames:v 3 -pix_fmt yuv420p videos/noise.y4m

# generate full range output ("pc" in ffmpeg)
ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=full,signalstats,metadata=print" -frames:v 3 -pix_fmt yuv420p videos/full-range.y4m

# generate limited range output ("tv" in ffmpeg)
ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=limited,signalstats,metadata=print" -frames:v 3 -pix_fmt yuv420p videos/limited-range.y4m

# checkerboard pattern, 1x1px
ffmpeg -y -f lavfi -i color=white:size=320x240 -f lavfi -i color=black:size=320x240 -filter_complex "[0:v][1:v]blend=all_expr='if(eq(mod(X,2),mod(Y,2)),A,B)',signalstats,metadata=print" -frames:v 3 -pix_fmt yuv420p videos/checkerboard-1x1.y4m

# checkerboard pattern, 8x8px
ffmpeg -y -f lavfi -i color=white:size=320x240 -f lavfi -i color=black:size=320x240 -filter_complex "[0:v][1:v]blend=all_expr='if(eq(mod(floor(X/32),2),mod(floor(Y/32),2)),A,B)',signalstats,metadata=print" -frames:v 3 -pix_fmt yuv420p videos/checkerboard-8x8.y4m

# checkerboard pattern, 8x8px, 10-bit limited range
ffmpeg -y -f lavfi -i color=white:size=320x240 -f lavfi -i color=black:size=320x240 -filter_complex "[0:v][1:v]blend=all_expr='if(eq(mod(floor(X/32),2),mod(floor(Y/32),2)),A,B)',signalstats,metadata=print" -frames:v 3 -pix_fmt yuv420p10le -strict -1 videos/checkerboard-8x8-10bpp-limited.y4m

# checkerboard pattern, 8x8px, 10-bit
ffmpeg -y -f lavfi -i color=white:size=320x240 -f lavfi -i color=black:size=320x240 -filter_complex "[0:v][1:v]blend=all_expr='if(eq(mod(floor(X/32),2),mod(floor(Y/32),2)),A,B)',scale=in_range=limited:out_range=full,signalstats,metadata=print" -frames:v 3 -pix_fmt yuv420p10le -strict -1 videos/checkerboard-8x8-10bpp.y4m

# various width/height combinations
ffmpeg -y -f lavfi -i testsrc=size=1920x1080 -filter:v "scale=in_range=limited:out_range=full,signalstats,metadata=mode=print" -frames:v 1 -pix_fmt yuv420p videos/test-1080p.y4m
ffmpeg -y -f lavfi -i testsrc=size=1280x720 -filter:v "scale=in_range=limited:out_range=full,signalstats,metadata=mode=print" -frames:v 1 -pix_fmt yuv420p videos/test-720p.y4m
ffmpeg -y -f lavfi -i testsrc=size=854x480 -filter:v "scale=in_range=limited:out_range=full,signalstats,metadata=mode=print" -frames:v 1 -pix_fmt yuv420p videos/test-480p.y4m
ffmpeg -y -f lavfi -i testsrc=size=640x360 -filter:v "scale=in_range=limited:out_range=full,signalstats,metadata=mode=print" -frames:v 1 -pix_fmt yuv420p videos/test-360p.y4m
ffmpeg -y -f lavfi -i testsrc=size=426x240 -filter:v "scale=in_range=limited:out_range=full,signalstats,metadata=mode=print" -frames:v 1 -pix_fmt yuv420p videos/test-240p.y4m
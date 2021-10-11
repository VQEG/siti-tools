#!/usr/bin/env python3
#
# Verify output of PyAV with limited/full range content
import av
import numpy as np

# generate with:
# ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=limited,$metadataPrint" -frames:v 3 -pix_fmt yuv420p videos/limited-range.y4m
# ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=full,$metadataPrint" -frames:v 3 -pix_fmt yuv420p videos/full-range.y4m


def decode_and_print(input_file):
    print(input_file)
    container = av.open(input_file)

    for frame in container.decode(video=0):
        frame_data = (
            frame.to_ndarray(format="gray")
            .reshape(frame.height, frame.width)
            .astype("int")
        )
        print(f"min: {np.min(frame_data)}, max: {np.max(frame_data)}")


decode_and_print("videos/full-range.y4m")
decode_and_print("videos/limited-range.y4m")

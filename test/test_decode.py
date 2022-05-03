#!/usr/bin/env python3
#
# Verify output of PyAV with limited/full range content
import av
import numpy as np

# generate with:
# ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=limited,signalstats,metadata=mode=print" -frames:v 3 -pix_fmt yuv420p videos/limited-range.y4m
# ffmpeg -y -f lavfi -i testsrc=size=320x240 -filter:v "scale=in_range=limited:out_range=full,signalstats,metadata=mode=print" -frames:v 3 -pix_fmt yuv420p videos/full-range.y4m
def useful_array(plane, bytes_per_pixel=1):
    total_line_size = abs(plane.line_size)
    useful_line_size = plane.width * bytes_per_pixel
    arr = np.frombuffer(plane, np.uint8)
    if total_line_size != useful_line_size:
        arr = arr.reshape(-1, total_line_size)[:, 0:useful_line_size].reshape(-1)
    return arr


def decode_and_print(input_file, bitdepth=8):
    print(input_file)
    container = av.open(input_file)
    breakpoint()

    if bitdepth == 8:
        datatype = np.uint8
    elif bitdepth > 8:
        datatype = np.uint16
    else:
        raise RuntimeError

    for idx, frame in enumerate(container.decode(video=0)):
        frame_data = (
            np.frombuffer(frame.planes[0], datatype)
            # useful_array(frame.planes[0])
            .reshape(frame.height, frame.width).astype("int")
        )
        print(f"frame {idx} -- min: {np.min(frame_data)}, max: {np.max(frame_data)}")
    print()


# decode_and_print("videos/limited-range.y4m")

# decode_and_print("videos/full-range.y4m")

# decode_and_print("videos/checkerboard-8x8.y4m")

# decode_and_print("videos/checkerboard-8x8-10bpp-limited.y4m", bitdepth=10)

decode_and_print("videos/checkerboard-8x8-10bpp.y4m", bitdepth=10)

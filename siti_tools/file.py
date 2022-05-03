# This file is part of siti_tools
#
# MIT License
#
# siti_tools, Copyright (c) 2021 Werner Robitza
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Generator
import numpy as np
import av
import logging

logger = logging.getLogger("siti")


def read_container(input_file: str) -> Generator[np.ndarray, None, None]:
    """
    Read a multiplexed file via ffmpeg and yield the per-frame Y data.

    This method tries to be clever determining the bit depth and decoding the
    data correctly such that content with >8bpp is returned with the full range
    of values, and not 0-255.

    Args:
        input_file (str): Input file path

    Raises:
        RuntimeError: If no video streams were found or decoding was not possible

    Yields:
        np.ndarray: The frame data, integer
    """
    container = av.open(input_file)

    if not len(container.streams.video):
        raise RuntimeError("No video streams found!")

    for frame in container.decode(video=0):
        # FIXME: this has been determined experimentally, not sure if it is the
        # correct way to do that -- the return values seem correct for a white/black
        # checkerboard pattern
        if "p10" in str(frame.format):
            datatype = np.uint16
        elif "p12" in str(frame.format):
            datatype = np.uint16
        else:
            datatype = np.uint8

        try:
            yield (
                # The code commented out below does the "standard" conversion of YUV
                # to grey, using weighting, but it does not actually use the correct
                # luminance-only Y values.
                # frame.to_ndarray(format="gray")

                # choose the Y plane (the first one)
                np.frombuffer(frame.planes[0], datatype)
                .reshape(frame.height, frame.width).astype("int")
            )
        except ValueError as e:
            raise RuntimeError(
                f"Cannot decode frame. Have you specified the bit depth correctly? Original error: {e}"
            )

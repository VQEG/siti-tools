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

import os
from typing import Generator
import numpy as np
import av


def read_container(input_file: str) -> Generator[np.ndarray, None, None]:
    """Read a multiplexed file via ffmpeg and yield the per-frame Y data

    Args:
        input_file (str): Input file path

    Raises:
        RuntimeError: If no video streams were found

    Yields:
        np.ndarray: The frame data, integer
    """
    container = av.open(input_file)

    if not len(container.streams.video):
        raise RuntimeError("No video streams found!")

    for frame in container.decode(video=0):
        frame_data = (
            frame.to_ndarray(format="gray")
            .reshape(frame.height, frame.width)
            .astype("int")
        )

        if not full_range:
            # check if we don't actually exceed minimum range
            frame_data = _convert_range(frame_data)
        yield frame_data

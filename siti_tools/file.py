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
from enum import Enum
import av


class FileFormat(Enum):
    YUV420P = 1


def read_yuv(
    input_file: str,
    width: int,
    height: int,
    file_format=FileFormat.YUV420P,
    full_range=False,
) -> Generator[np.ndarray, None, None]:
    """Read a YUV420p file and yield the per-frame Y data

    Args:
        input_file (str): Input file path
        width (int): Width in pixels
        height (int): Height in pixels
        file_format (str, optional): The input file format. Defaults to FileFormat.YUV420P.
        full_range (bool, optional): Whether to assume full range input. Defaults to False.

    Raises:
        NotImplementedError: If a wrong file format is chosen

    Yields:
        np.ndarray: The frame data
    """
    # TODO: add support for other YUV types
    if file_format != FileFormat.YUV420P:
        raise NotImplementedError("Other file formats are not yet implemented!")

    # get the number of frames
    file_size = os.path.getsize(input_file)

    num_frames = file_size // (width * height * 3 // 2)

    with open(input_file, "rb") as in_f:
        for _ in range(num_frames):
            y_data = (
                np.frombuffer(in_f.read((width * height)), dtype=np.uint8)
                .reshape((height, width))
                .astype("float32")
            )

            # read U and V components, but skip
            in_f.read((width // 2) * (height // 2) * 2)

            # in case we need the data later, you can uncomment this:
            # u_data = (
            #     np.frombuffer(in_f.read(((width // 2) * (height // 2))), dtype=np.uint8)
            #     .reshape((height // 2, width // 2))
            #     .astype("float32")
            # )
            # v_data = (
            #     np.frombuffer(in_f.read(((width // 2) * (height // 2))), dtype=np.uint8)
            #     .reshape((height // 2, width // 2))
            #     .astype("float32")
            # )

            if not full_range:
                # check if we don't actually exceed minimum range
                if np.min(y_data) < 16 or np.max(y_data) > 235:
                    raise RuntimeError("Input YUV appears to be full range, specify full_range=True!")
                # convert to grey by assumng limited range input
                y_data = np.around((y_data - 16) / ((235 - 16) / 255))

            yield y_data


def read_container(input_file: str) -> Generator[np.ndarray, None, None]:
    container = av.open(input_file)

    if not len(container.streams.video):
        raise RuntimeError("No video streams found!")

    for frame in container.decode(video=0):
        frame_data = (
            frame.to_ndarray(format="gray")
            .reshape(frame.height, frame.width)
            .astype("float32")
        )
        yield frame_data

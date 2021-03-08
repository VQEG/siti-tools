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

from typing import Optional
from scipy import ndimage
import numpy as np

from .file import FileFormat, read_container, read_yuv


def si(frame_data: np.ndarray) -> float:
    """Calculate SI of a frame

    Args:
        frame_data (ndarray): 2D array of input frame data

    Returns:
        float: SI
    """
    # TODO: check array dimensions

    # calculate horizontal/vertical operators
    sob_x = ndimage.sobel(frame_data, axis=0)
    sob_y = ndimage.sobel(frame_data, axis=1)

    # crop output to valid window, calculate gradient magnitude
    si = np.hypot(sob_x, sob_y)[1:-1, 1:-1].std()
    return si


def ti(
    frame_data: np.ndarray, previous_frame_data: Optional[np.ndarray]
) -> Optional[float]:
    """
    Calculate TI between two frames.

    Args:
        frame_data (ndarray): 2D array of current frame data
        previous_frame_data (ndarray): 2D array of previous frame data, must be of same size as current frame

    Returns:
        float: TI, or None if previous frame data is not given
    """
    # TODO: check array dimensions
    # TODO: check array dimensions equal between both args

    if previous_frame_data is None:
        return None
    else:
        return (frame_data - previous_frame_data).std()


def calculate_si_ti(
    input_file: str,
    width=0,
    height=0,
    file_format=FileFormat.YUV420P,
    num_frames=0,
    full_range=False,
):
    """Calculate SI and TI from a raw input file.
    Returns two arrays and one integer, the first array being the SI values, the
    second array being the TI values. The first element of the TI value array will
    always be 0. The integer will be equal to the number of frames read.

    Args:
        input_file (str): path to input file
        width (int): frame width in pixels. Defaults to 0.
        height (int): frame height in pixels. Defaults to 0.
        file_format (FileFormat): file format for raw files. Defaults to YUV420P.
        num_frames (int, optional): number of frames to calculate. Defaults to 0 (calculate all).
        full_range (bool, optional): whether to assume full range for input file. Defaults to False.

    Returns:
        [[float], [float], int]: [si_values], [ti_values], frame count
    """
    si_values = []
    ti_values = [0.0]
    previous_frame_data = None

    # use raw input read function
    if input_file.endswith(".yuv"):
        kwargs = {"width": width, "height": height, "full_range": full_range, "file_format": file_format}
        iterator_fun = read_yuv
    else:
        # read via PyAV
        kwargs = {}
        iterator_fun = read_container

    current_frame = 0
    for frame_data in iterator_fun(input_file, **kwargs):
        si_value = si(frame_data)
        si_values.append(si_value)

        ti_value = ti(frame_data, previous_frame_data)
        if ti_value is not None:
            ti_values.append(ti_value)

        previous_frame_data = frame_data

        current_frame += 1

        if num_frames is not None and current_frame >= num_frames:
            return si_values, ti_values, current_frame

    return si_values, ti_values, current_frame

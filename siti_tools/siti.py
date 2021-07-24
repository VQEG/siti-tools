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
from enum import Enum
import numpy as np

from .file import read_container


class EnumArg(Enum):
    def __str__(self):
        return self.value


class HdrMode(EnumArg):
    """
    Mode of HDR calculation, should be SDR by default
    """

    SDR = "sdr"
    HDR10 = "hdr10"
    HLG = "hlg"


class SdrRange(EnumArg):
    """
    Limited or full range, where limited is from 16-235, and full is from 0-255.
    """

    LIMITED = "limited"
    FULL = "full"


class EotfFunction(EnumArg):
    """
    EOTF for converting SDR
    """

    BT1886 = "bt1886"
    INV_SRGB = "inv_srgb"


DEFAULT_HDR_MODE = HdrMode.SDR
DEFAULT_SDR_RANGE = SdrRange.LIMITED
DEFAULT_EOTF_FUNCTION = EotfFunction.BT1886
DEFAULT_GAMMA = 2.4  # for BT.1886
DEFAULT_L_MIN = 0.1
DEFAULT_L_MAX = 300
DEFAULT_L_MIN_HDR = 0.01
DEFAULT_L_MAX_HDR = 1000.0


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


def eotf_1886(
    frame_data: np.ndarray,
    gamma: float = DEFAULT_GAMMA,
    l_min: float = 0.0,
    l_max: float = 1.0,
) -> np.ndarray:
    """
    Electro-optical transfer function defined in ITU-T Rec. BT.1886

    Args:
        frame_data: pixel values expected in the range [0, 1]
        gamma: exponent
        l_min: minimum luminance
        l_max: maximum luminance
    Note:
        As the mapping to display luminance happens outside of this function, l_min and l_max are set to 0.0 and 1.0,
        respectively. If you change these values while using this function in the context of SI/TI calculation, your
        output will be wrong. You can however change the values when using this function in a standalone fashion.

    Returns:
        frame_data: pixel values in the range [0, 1]

    """
    frame_data = np.maximum(frame_data, 0.0)
    frame_data = np.minimum(frame_data, 1.0)

    a = np.power(np.power(l_max, 1.0 / gamma) - np.power(l_min, 1.0 / gamma), gamma)
    b = np.power(l_min, 1.0 / gamma) / (
        np.power(l_max, 1.0 / gamma) - np.power(l_min, 1.0 / gamma)
    )

    frame_data = a * np.power(np.maximum(frame_data + b, 0), gamma)

    return frame_data


def eotf_inv_srgb(frame_data: np.ndarray) -> np.ndarray:
    """
    Inverse sRGB electro-optical transfer function

    Args:
        frame_data: pixel values expected in the range [0, 1]

    Returns:
        frame_data: pixel values in the range [0, 1]

    """
    frame_data = np.maximum(frame_data, 0.0)
    frame_data = np.minimum(frame_data, 1.0)

    frame_data = (frame_data <= 0.04045) * frame_data / 12.92 + (
        frame_data > 0.04045
    ) * np.power((frame_data + 0.055) / 1.055, 2.4)

    return frame_data


def apply_display_model(
    frame_data: np.ndarray,
    eotf_function: EotfFunction = EotfFunction.BT1886,
    l_max=DEFAULT_L_MAX,
    l_min=DEFAULT_L_MIN,
    gamma=DEFAULT_GAMMA,
) -> np.ndarray:
    """
    Apply the SDR EOTF

    Args:
        frame_data (np.ndarray): Raw frame data in full range
        Other arguments: see calculate_si_ti()
    """
    if eotf_function == EotfFunction.BT1886:
        fn = eotf_1886
        kwargs = {"gamma": gamma}
    elif eotf_function == EotfFunction.INV_SRGB:
        fn = eotf_inv_srgb
        kwargs = {}
    else:
        raise RuntimeError("Unknown EOTF function!")

    return (l_max - l_min) * fn(frame_data, **kwargs) - l_min


def oetf_pq(frame_data: np.ndarray) -> np.ndarray:
    """
    Perceptual quantizer opto-electrical transfer function defined in ITU-T Rec. BT.2100

    Args:
        frame_data: pixel values expected to be in the physical luminance between 0 and 10,000 cd/m^2

    Returns:
        frame_data: pixel values in the range [0, 1]

    """

    m = 78.84375
    n = 0.1593017578125
    c1 = 0.8359375
    c2 = 18.8515625
    c3 = 18.6875
    lm1 = np.power(10000.0, n)
    lm2 = np.power(frame_data, n)

    frame_data = np.power((c1 * lm1 + c2 * lm2) / (lm1 + c3 * lm2), m)

    return frame_data


def eotf_hlg(
    frame_data: np.ndarray,
    l_min: float = DEFAULT_L_MIN_HDR,
    l_max: float = DEFAULT_L_MAX_HDR,
) -> np.ndarray:
    """
    Hybrid log-gamma opto-electrical transfer function defined in ITU-T Rec. BT.2100

    Args:
        frame_data: pixel values expected to be in the range [0, 1]

    Returns:
        frame_data: pixel values in the physical luminance up to 10,000 cd/m^2

    """
    frame_data = np.maximum(frame_data, 0.0)
    frame_data = np.minimum(frame_data, 1.0)

    a = 0.17883277
    b = 0.02372241
    c = 1.00429347
    gamma = 1.2

    frame_data = (frame_data <= 0.5) * (np.power(frame_data, 2.0) / 3.0) + (
        frame_data > 0.5
    ) * (np.exp((frame_data - c) / a) - b)

    frame_data = (l_max - l_min) * np.power(frame_data, gamma - 1.0) + l_min

    return frame_data


def calculate_si_ti(
    input_file: str,
    hdr_mode=DEFAULT_HDR_MODE,
    sdr_range=DEFAULT_SDR_RANGE,
    eotf_function=DEFAULT_EOTF_FUNCTION,
    l_max=DEFAULT_L_MAX,
    l_min=DEFAULT_L_MIN,
    gamma=DEFAULT_GAMMA,
    num_frames=0,
):
    """Calculate SI and TI from an input file.
    Returns two arrays and one integer, the first array being the SI values, the
    second array being the TI values. The first element of the TI value array will
    always be 0. The integer will be equal to the number of frames read.

    TODO: document arguments

    Returns:
        [[float], [float], int]: [si_values], [ti_values], frame count
    """
    si_values = []
    ti_values = [0.0]
    previous_frame_data = None

    current_frame = 0
    for frame_data in read_container(input_file):

        if hdr_mode == HdrMode.SDR:
            # TODO: check what to do in case of > 8 bpc
            # convert limited to full range
            if sdr_range == SdrRange.LIMITED:
                # check if we don't actually exceed minimum range
                if np.min(frame_data) < 16 or np.max(frame_data) > 235:
                    raise RuntimeError(
                        "Input appears to be full range, but treated as limited range SDR!"
                    )
                frame_data = np.around((frame_data - 16) / ((235 - 16) / 255))

            frame_data = apply_display_model(
                frame_data,
                eotf_function=eotf_function,
                l_max=l_max,
                l_min=l_min,
                gamma=gamma,
            )

            frame_data = oetf_pq(frame_data)
        elif hdr_mode == HdrMode.HDR10:
            # nothing to do
            pass
        elif hdr_mode == HdrMode.HLG:
            frame_data = eotf_hlg(frame_data)
            frame_data = oetf_pq(frame_data)
        else:
            raise RuntimeError("Invalid HDR mode")

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

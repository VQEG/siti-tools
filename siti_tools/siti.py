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
from typing import Dict, List, Optional, Tuple, Union
from scipy import ndimage
from enum import Enum
import numpy as np

from .file import read_container
from . import __version__ as version


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


class ColorRange(EnumArg):
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


class SiTiCalculator:
    DEFAULT_HDR_MODE = HdrMode.SDR
    DEFAULT_BIT_DEPTH = 8  # or 10, 12
    DEFAULT_COLOR_RANGE = ColorRange.LIMITED
    DEFAULT_EOTF_FUNCTION = EotfFunction.BT1886
    DEFAULT_GAMMA = 2.4  # for BT.1886
    DEFAULT_L_MIN = 0.1
    DEFAULT_L_MAX = 300
    DEFAULT_L_MIN_HDR = 0.01
    DEFAULT_L_MAX_HDR = 1000.0

    LIMITED_RANGE_MIN = 16 / 255
    LIMITED_RANGE_MAX = 235 / 255

    def __init__(
        self,
        hdr_mode: HdrMode = DEFAULT_HDR_MODE,
        bit_depth: int = DEFAULT_BIT_DEPTH,
        color_range: ColorRange = DEFAULT_COLOR_RANGE,
        eotf_function: EotfFunction = DEFAULT_EOTF_FUNCTION,
        l_max: float = DEFAULT_L_MAX,
        l_min: float = DEFAULT_L_MIN,
        gamma: float = DEFAULT_GAMMA,
    ):
        """
        Create a new SI/TI calculator

        Args:
            hdr_mode (HdrMode, optional): Select SDR, HDR10 or HLG. Defaults to SDR.
            bit_depth (int, optional): 8, 10 or 12. Defaults to 8.
            color_range (ColorRange, optional): Set the color range (limited or full). Defaults to limited.
            eotf_function (EotfFunction, optional): EOTF function for converting SDR to HDR. Defaults to BT.1886.
            l_max (float, optional): Set the peak display luminance in cd/m2. Defaults to 300 (SDR) or 1000 (HDR).
            l_min (float, optional): Set the black display luminance in cd/m2. Defaults to 0.1 (SDR) or 0.01 (HDR).
            gamma (float, optional): Set the BT.1886 gamma. Defaults to 2.4.
        """
        self.hdr_mode = hdr_mode

        if bit_depth not in [8, 10, 12]:
            raise RuntimeError("Bit depth must be one of 8, 10, 12")

        self.bit_depth = bit_depth

        self.color_range = color_range
        self.eotf_function = eotf_function

        # overwrite the default depending on HDR type
        if l_max is None:
            self.l_max = (
                SiTiCalculator.DEFAULT_L_MAX
                if self.hdr_mode == HdrMode.SDR
                else SiTiCalculator.DEFAULT_L_MAX_HDR
            )
        else:
            self.l_max = l_max
        if l_min is None:
            self.l_min = (
                SiTiCalculator.DEFAULT_L_MIN
                if self.hdr_mode == HdrMode.SDR
                else SiTiCalculator.DEFAULT_L_MIN_HDR
            )
        else:
            self.l_min = l_min

        self.gamma = gamma

        self.si_values: List[float] = []
        self.ti_values: List[Union[float, None]] = []

        self.last_input_file: Union[None, str] = None

    def get_general_settings(self) -> Dict:
        """
        A dictionary of settings used for the calculation
        """
        return {
            "hdr_mode": str(self.hdr_mode),
            "bit_depth": self.bit_depth,
            "color_range": str(self.color_range),
            "eotf_function": str(self.eotf_function),
            "l_max": self.l_max,
            "l_min": self.l_min,
            "gamma": self.gamma,
            "version": version,
        }

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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
        if np.min(frame_data) < 0:
            print("Warning: Input for eotf_1886() was < 0, truncating")
        if np.max(frame_data) > 1:
            print("Warning: Input for eotf_1886() was > 1, truncating")

        frame_data = np.maximum(frame_data, 0.0)
        frame_data = np.minimum(frame_data, 1.0)

        a = np.power(np.power(l_max, 1.0 / gamma) - np.power(l_min, 1.0 / gamma), gamma)
        b = np.power(l_min, 1.0 / gamma) / (
            np.power(l_max, 1.0 / gamma) - np.power(l_min, 1.0 / gamma)
        )

        frame_data = a * np.power(np.maximum(frame_data + b, 0), gamma)

        return frame_data

    @staticmethod
    def eotf_inv_srgb(frame_data: np.ndarray) -> np.ndarray:
        """
        Inverse sRGB electro-optical transfer function

        Args:
            frame_data: pixel values expected in the range [0, 1]

        Returns:
            frame_data: pixel values in the range [0, 1]

        """
        if np.min(frame_data) < 0:
            print("Warning: Input for eotf_inv_srgb() was < 0, truncating")
        if np.max(frame_data) > 1:
            print("Warning: Input for eotf_inv_srgb() was > 1, truncating")

        frame_data = np.maximum(frame_data, 0.0)
        frame_data = np.minimum(frame_data, 1.0)

        frame_data = (frame_data <= 0.04045) * frame_data / 12.92 + (
            frame_data > 0.04045
        ) * np.power((frame_data + 0.055) / 1.055, 2.4)

        return frame_data

    @staticmethod
    def apply_display_model(
        frame_data: np.ndarray,
        eotf_function: EotfFunction = EotfFunction.BT1886,
        l_max: float = DEFAULT_L_MAX,
        l_min: float = DEFAULT_L_MIN,
        gamma: float = DEFAULT_GAMMA,
    ) -> np.ndarray:
        """
        Apply the SDR EOTF

        Args:
            frame_data (np.ndarray): Raw frame data in full range, values in the range [0, 1]
            Other arguments: see calculate()

        Returns:
            frame_data: pixel values in the range [0, 1]
        """
        if np.min(frame_data) < 0:
            raise RuntimeError("Input for apply_display_model() was < 0")
        if np.max(frame_data) > 1:
            raise RuntimeError("Input for apply_display_model() was > 1")

        if eotf_function == EotfFunction.BT1886:
            fn = SiTiCalculator.eotf_1886
            kwargs = {"gamma": gamma}
        elif eotf_function == EotfFunction.INV_SRGB:
            fn = SiTiCalculator.eotf_inv_srgb
            kwargs = {}
        else:
            raise RuntimeError("Unknown EOTF function!")

        return (l_max - l_min) * fn(frame_data, **kwargs) - l_min

    @staticmethod
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

    @staticmethod
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

    def normalize_to_original_range(self, frame_data: Union[np.ndarray, float]):
        """
        Normalize frame data in the range [0, 1] to their original range, based on
        bit depth, e.g. from [0, 1] to [0, 255].
        """
        return frame_data * (2 ** self.bit_depth - 1)

    def normalize_to_original_si_range(self, frame_data: Union[np.ndarray, float]):
        """
        Normalize frame data in the range [0, 1] to [0, 255], which was the original
        range for SI/TI.
        """
        return frame_data * (2 ** 8 - 1)

    def normalize_between_0_1(self, frame_data: Union[np.ndarray, float]):
        """
        Normalize frame data in the range [0, x] to [0, 1], based on bit depth.
        """
        return frame_data / (2 ** self.bit_depth - 1)

    def calculate(
        self,
        input_file: str,
        num_frames=0,
    ) -> Tuple[List[float], List[Union[float, None]], int]:
        """Calculate SI and TI from an input file.

        Returns two arrays and one integer, the first array being the SI values, the
        second array being the TI values. The first element of the TI value array will
        always be 0. The integer will be equal to the number of frames read.

        You can also get the results later via .get_results()

        Args:
            input_file (str): input file path
            num_frames (int): number of frames to calculate. Defaults to 0 (unlimited).

        Returns:
            [[float], [float|None], int]: [si_values], [ti_values], frame count
        """
        self.si_values = []
        self.ti_values = []
        self.last_input_file = input_file
        previous_frame_data = None

        current_frame = 0
        for frame_data in read_container(input_file):
            # Normalize frame data according to bit depth between 0 and 1.
            # This will transform [0, 255] to [0, 1], and [0, 1023] to [0, 1] etc.
            frame_data = self.normalize_between_0_1(frame_data)

            # convert limited to full range
            if self.color_range == ColorRange.LIMITED:
                # check if we don't actually exceed minimum range
                input_min = np.min(frame_data)
                input_max = np.max(frame_data)
                if (
                    input_min < self.LIMITED_RANGE_MIN
                    or input_max > self.LIMITED_RANGE_MAX
                ):
                    # inform the user about the original range
                    raise RuntimeError(
                        "Input appears to be full range, but treated as limited range SDR! "
                        f"Input range is [{int(self.normalize_to_original_range(input_min))}-{int(self.normalize_to_original_range(input_max))}]. "
                        "Specify the range as full instead."
                    )
                frame_data = (frame_data - self.LIMITED_RANGE_MIN) / (
                    self.LIMITED_RANGE_MAX - self.LIMITED_RANGE_MIN
                )

            if self.hdr_mode == HdrMode.SDR:
                frame_data = SiTiCalculator.apply_display_model(
                    frame_data,
                    eotf_function=self.eotf_function,
                    l_max=self.l_max,
                    l_min=self.l_min,
                    gamma=self.gamma,
                )

                frame_data = SiTiCalculator.oetf_pq(frame_data)
            elif self.hdr_mode == HdrMode.HDR10:
                # nothing to do
                # TODO: does this mean we also shouldn't normalize between [0-1] here?
                pass
            elif self.hdr_mode == HdrMode.HLG:
                frame_data = SiTiCalculator.eotf_hlg(frame_data)
                frame_data = SiTiCalculator.oetf_pq(frame_data)
            else:
                raise RuntimeError("Invalid HDR mode")

            si_value = SiTiCalculator.si(frame_data)
            self.si_values.append(self.normalize_to_original_si_range(si_value))

            ti_value = SiTiCalculator.ti(frame_data, previous_frame_data)
            if ti_value is not None:
                self.ti_values.append(self.normalize_to_original_si_range(ti_value))

            previous_frame_data = frame_data

            current_frame += 1

            if num_frames is not None and current_frame >= num_frames:
                return self.si_values, self.ti_values, current_frame

        return self.si_values, self.ti_values, current_frame

    def get_results(self) -> Dict:
        """
        Get a JSON-serializable result dictionary with SI, TI values, as well as used settings.

        Returns:
            dict: A dictionary containing "si", "ti" arrays, "settings" as a dict, and the "input_file" name.
        """
        return {
            "si": self.si_values,
            "ti": self.ti_values,
            "settings": self.get_general_settings(),
            "input_file": os.path.basename(self.last_input_file)
            if self.last_input_file is not None
            else "",
        }

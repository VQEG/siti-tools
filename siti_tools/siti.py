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

import csv
import io
import logging
import os
import plotille
from typing import Dict, List, Optional, Tuple, Union, Callable, cast
from scipy import ndimage
from enum import Enum
import numpy as np

from .file import read_container
from . import __version__ as version

logger = logging.getLogger("siti")


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


class CalculationDomain(EnumArg):
    """
    Domain in which to calculate SI/TI
    """

    PQ = "pq"
    PU21 = "pu21"


class Pu21Mode(EnumArg):
    BANDING = "banding"
    BANDING_GLARE = "banding_glare"
    PEAKS = "peaks"
    PEAKS_GLARE = "peaks_glare"


class SiTiCalculator:
    DEFAULT_HDR_MODE = HdrMode.SDR
    DEFAULT_BIT_DEPTH = 8  # or 10, 12
    DEFAULT_COLOR_RANGE = ColorRange.LIMITED
    DEFAULT_EOTF_FUNCTION = EotfFunction.BT1886
    DEFAULT_CALCULATION_DOMAIN = CalculationDomain.PQ
    DEFAULT_PU21_MODE = Pu21Mode.BANDING
    DEFAULT_GAMMA = 2.4  # for BT.1886
    DEFAULT_L_MIN = 0.1
    DEFAULT_L_MAX = 300
    DEFAULT_L_MIN_HDR = 0.01
    DEFAULT_L_MAX_HDR = 1000.0

    LIMITED_RANGE_MIN = 16 / 255
    LIMITED_RANGE_MAX = 235 / 255

    @staticmethod
    def from_settings(settings: Dict):
        return SiTiCalculator(**settings)

    def __init__(
        self,
        hdr_mode: HdrMode = DEFAULT_HDR_MODE,
        bit_depth: int = DEFAULT_BIT_DEPTH,
        color_range: ColorRange = DEFAULT_COLOR_RANGE,
        eotf_function: EotfFunction = DEFAULT_EOTF_FUNCTION,
        calculation_domain: CalculationDomain = DEFAULT_CALCULATION_DOMAIN,
        l_max: Union[float, None] = None,
        l_min: Union[float, None] = None,
        gamma: float = DEFAULT_GAMMA,
        pu21_mode: Pu21Mode = DEFAULT_PU21_MODE,
        verbose=False,
        show_histogram=False,
        legacy=False,
    ):
        """
        Create a new SI/TI calculator

        Args:
            hdr_mode (HdrMode, optional): Select SDR, HDR10 or HLG. Defaults to SDR.
            bit_depth (int, optional): 8, 10 or 12. Defaults to 8.
            color_range (ColorRange, optional): Set the color range (limited or full). Defaults to limited.
            eotf_function (EotfFunction, optional): EOTF function for converting SDR to HDR. Defaults to BT.1886.
            calculation_domain (CalculationDomain, optional): Domain to calculate SI/TI in. Defaults to PQ.
            l_max (float, optional): Set the peak display luminance in cd/m2. Defaults to 300 (SDR) or 1000 (HDR).
            l_min (float, optional): Set the black display luminance in cd/m2. Defaults to 0.1 (SDR) or 0.01 (HDR).
            gamma (float, optional): Set the BT.1886 gamma. Defaults to 2.4.
            pu21_mode (Pu21Mode, optional): Set the default PU21 mode. Defaults to BANDING.
            verbose (bool, optional): Show verbose logging for the first frame.
            show_histogram (bool, optional): Show a histogram for the first frame (computation-intensive, implies verbose=True).
            legacy (bool, optional): Use legacy SI/TI calculation. Defaults to False.
        """
        self.verbose = verbose
        self.show_histogram = show_histogram
        self.legacy = legacy

        if self.show_histogram:
            self.verbose = True

        self.callbacks: List[Callable] = []

        self.hdr_mode = hdr_mode

        if bit_depth not in [8, 10, 12]:
            raise RuntimeError("Bit depth must be one of 8, 10, 12")

        self.bit_depth = bit_depth

        self.color_range = color_range
        self.eotf_function = eotf_function
        self.calculation_domain = calculation_domain

        self.pu21_mode = pu21_mode
        self.oetf_function_kwargs = {}
        if self.calculation_domain == CalculationDomain.PQ:
            self.oetf_function = SiTiCalculator.oetf_pq
        else:
            self.oetf_function = SiTiCalculator.oetf_pu21
            self.oetf_function_kwargs["mode"] = self.pu21_mode

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
        A dictionary of settings used for the calculation
        """
        return {
            "calculation_domain": str(self.calculation_domain),
            "hdr_mode": str(self.hdr_mode),
            "bit_depth": self.bit_depth,
            "color_range": str(self.color_range),
            "eotf_function": str(self.eotf_function),
            "l_max": self.l_max,
            "l_min": self.l_min,
            "gamma": self.gamma,
            "pu21_mode": str(self.pu21_mode),
            "legacy": self.legacy,
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
            return cast(np.ndarray, frame_data - previous_frame_data).std()

    @staticmethod
    def eotf_1886(
        frame_data: np.ndarray,
        gamma: float = DEFAULT_GAMMA,
        l_min: float = 0.0,
        l_max: float = 1.0,
    ) -> np.ndarray:
        """
        Electro-optical transfer function defined in ITU-R Rec. BT.1886

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
            logger.warn("Input for eotf_1886() was < 0, truncating")
        if np.max(frame_data) > 1:
            logger.warn("Input for eotf_1886() was > 1, truncating")

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
            logger.warn("Input for eotf_inv_srgb() was < 0, truncating")
        if np.max(frame_data) > 1:
            logger.warn("Input for eotf_inv_srgb() was > 1, truncating")

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
            frame_data: pixel values in the physical domain.
        """
        if np.min(frame_data) < 0:
            raise RuntimeError("Input for apply_display_model() was < 0")
        if np.max(frame_data) > 1:
            raise RuntimeError("Input for apply_display_model() was > 1")

        if eotf_function == EotfFunction.BT1886:
            fn = SiTiCalculator.eotf_1886
            # note that l_min/l_max are not passed here on purpose, as they are set to 0.0 and 1.0,
            # and mapped outside of the eotf_1886 function
            kwargs = {"gamma": gamma}
        elif eotf_function == EotfFunction.INV_SRGB:
            fn = SiTiCalculator.eotf_inv_srgb
            kwargs = {}
        else:
            raise RuntimeError("Unknown EOTF function!")

        return (l_max - l_min) * fn(frame_data, **kwargs) + l_min

    @staticmethod
    def oetf_pq(frame_data: np.ndarray) -> np.ndarray:
        """
        Perceptual quantizer opto-electrical transfer function defined in ITU-R Rec. BT.2100

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
        # FIXME: this might return an error if input is negative, see https://stackoverflow.com/q/45384602/
        lm2 = np.power(frame_data, n)

        frame_data = np.power((c1 * lm1 + c2 * lm2) / (lm1 + c3 * lm2), m)

        return frame_data

    @staticmethod
    def oetf_pu21(
        frame_data: np.ndarray,
        mode: Pu21Mode = Pu21Mode.BANDING,
    ) -> np.ndarray:
        """
        PU21 OETF, see https://github.com/gfxdisp/pu21

        Args:
            frame_data (np.ndarray): Raw frame data in full range, values in the range [0, 1]
            mode (Pu21Mode), defaults to Pu21Mode.BANDING

        Returns:
            frame_data: pixel values in the range [0, 1]
        """

        if mode == "banding":
            p = [
                1.070275272,
                0.4088273932,
                0.153224308,
                0.2520326168,
                1.063512885,
                1.14115047,
                521.4527484,
            ]
            p_min = -1.5580e-07
            p_max = 520.4673
        elif mode == "banding_glare":
            p = [
                0.353487901,
                0.3734658629,
                8.277049286e-05,
                0.9062562627,
                0.09150303166,
                0.9099517204,
                596.3148142,
            ]
            p_min = 5.4705e-10
            p_max = 595.3939
        elif mode == "peaks":
            p = [
                1.043882782,
                0.6459495343,
                0.3194584211,
                0.374025247,
                1.114783422,
                1.095360363,
                384.9217577,
            ]
            p_min = 1.3674e-07
            p_max = 380.9853
        elif mode == "peaks_glare":
            p = [
                816.885024,
                1479.463946,
                0.001253215609,
                0.9329636822,
                0.06746643971,
                1.573435413,
                419.6006374,
            ]
            p_min = -9.7360e-08
            p_max = 407.5066
        else:
            raise RuntimeError("Invalid mode specified for PU21")

        # scale frame_data to the range 0.005 - 10,000
        # disabled since the input is already in physical luminance
        # frame_data = frame_data * 10000.0
        # frame_data = np.maximum(frame_data, 0.05)

        frame_data = p[6] * (
            np.power(
                (
                    (p[0] + p[1] * np.power(frame_data, p[3]))
                    / (1.0 + p[2] * np.power(frame_data, p[3]))
                ),
                p[4],
            )
            - p[5]
        )

        # get the output into the range [0, 1]
        frame_data = (frame_data - p_min) / (p_max - p_min)

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
        return frame_data * (2**self.bit_depth - 1)

    def normalize_to_original_si_range(self, frame_data: Union[np.ndarray, float]):
        """
        Normalize frame data in the range [0, 1] to [0, 255], which was the original
        range for SI/TI.
        """
        return frame_data * (2**8 - 1)

    def normalize_between_0_1(self, frame_data: Union[np.ndarray, float]):
        """
        Normalize frame data in the range [0, x] to [0, 1], based on bit depth.
        """
        return frame_data / (2**self.bit_depth - 1)

    def add_frame_callback(
        self, callback_fn: Callable[[float, Union[float, None], int], None]
    ):
        """Add a function that gets called whenever a frame's values are available

        Args:
            callback_fn (Callable[[float, Union[float, None], int], None]): The function that should get called. It will receive SI, TI and the frame number.
        """
        self.callbacks.append(callback_fn)

    def handle_limited_range(self, frame_data) -> np.ndarray:
        """
        Transforms data from limited range to full range. We expect the input to be in [16/255, 235/255] already.
        Apply this to limited range content only! If we exceed the limited range, an error will be raised.

        Args:
            frame_data (np.ndarray): The frame data in limited range.

        Returns:
            frame_data: The frame data in full range between [0, 1].
        """
        input_min = np.min(frame_data)
        input_max = np.max(frame_data)
        if (input_min + 0.001 < self.LIMITED_RANGE_MIN) or (
            input_max - 0.001 > self.LIMITED_RANGE_MAX
        ):
            # inform the user about the original range
            raise RuntimeError(
                "Input appears to be full range, but it is treated as limited range SDR! "
                f"Input range is [{int(self.normalize_to_original_range(input_min))}-{int(self.normalize_to_original_range(input_max))}]. "
                f"Expected range for limited content [{int(self.normalize_to_original_range(self.LIMITED_RANGE_MIN))}-{int(self.normalize_to_original_range(self.LIMITED_RANGE_MAX))}]. "
                "Specify the range as full instead."
            )
        # scale up to full range
        frame_data = np.clip(
            (frame_data - self.LIMITED_RANGE_MIN)
            / (self.LIMITED_RANGE_MAX - self.LIMITED_RANGE_MIN),
            0,
            1,
        )

        return frame_data

    @staticmethod
    def plot_histogram(frame_data: np.ndarray) -> str:
        return plotille.histogram(
            frame_data.flatten(), bins=40, width=78, height=25, x_min=0
        )

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
            self.verbose and logger.debug(f"Frame {current_frame+1}")

            if current_frame == 0:
                logger.debug("Original frame data")
                self._log_frame_data(frame_data)

            # Normalize frame data according to bit depth between 0 and 1.
            # This will transform [0, 255] to [0, 1], and [0, 1023] to [0, 1] etc.
            if not self.legacy:
                frame_data = self.normalize_between_0_1(frame_data)

                if current_frame == 0:
                    logger.debug("Frame data after normalization between 0 and 1")
                    self._log_frame_data(frame_data)

                # convert limited to full range
                if self.color_range == ColorRange.LIMITED:
                    frame_data = self.handle_limited_range(frame_data)
                    if current_frame == 0:
                        logger.debug("Frame data after limited-range normalization")
                        self._log_frame_data(frame_data)
                else:
                    # in full range, we do not have to further process the data
                    pass
            else:
                if self.color_range == ColorRange.LIMITED:
                    # legacy mode, apply the old way of normalizing data between 16-235
                    input_min = np.min(frame_data)
                    input_max = np.max(frame_data)
                    if input_min < 16 or input_max > 235:
                        raise RuntimeError(
                            f"Input appears to be full range ([{input_min}, {input_max}]), specify --color-range=full!"
                        )
                    # convert to grey by assumng limited range input
                    frame_data = np.around((frame_data - 16) / ((235 - 16) / 255))
                else:
                    # in full range, we do not have to further process the data
                    pass

            if not self.legacy:
                if self.hdr_mode == HdrMode.SDR:
                    frame_data = SiTiCalculator.apply_display_model(
                        frame_data,
                        eotf_function=self.eotf_function,
                        l_max=self.l_max,
                        l_min=self.l_min,
                        gamma=self.gamma,
                    )
                    if current_frame == 0:
                        logger.debug(
                            f"Frame data after apply_display_model for SDR ({self.l_min}, {self.l_max})"
                        )
                        self._log_frame_data(frame_data)
                    frame_data = self.oetf_function(
                        frame_data, **self.oetf_function_kwargs
                    )
                    if current_frame == 0:
                        logger.debug(
                            f"Frame data after OETF function {self.oetf_function} with args {self.oetf_function_kwargs}"
                        )
                        self._log_frame_data(frame_data)
                elif self.hdr_mode == HdrMode.HDR10:
                    # nothing to do, we are already in PQ domain
                    # TODO allow using Pu21 here?
                    pass
                elif self.hdr_mode == HdrMode.HLG:
                    frame_data = SiTiCalculator.eotf_hlg(
                        frame_data, self.l_min, self.l_max
                    )
                    if current_frame == 0:
                        logger.debug(
                            f"Frame data after eotf_hlg for HLG with l_min/l_max settings {self.l_min, self.l_max}"
                        )
                        self._log_frame_data(frame_data)
                    frame_data = self.oetf_function(
                        frame_data, **self.oetf_function_kwargs
                    )
                    if current_frame == 0:
                        logger.debug(
                            f"Frame data after OETF function {self.oetf_function} with args {self.oetf_function_kwargs}"
                        )
                        self._log_frame_data(frame_data)
                else:
                    raise RuntimeError(f"Invalid HDR mode '{self.hdr_mode}'")

            if not self.legacy:
                si_value = self.normalize_to_original_si_range(
                    SiTiCalculator.si(frame_data)
                )
            else:
                si_value = SiTiCalculator.si(frame_data)
            if current_frame != 0:
                if not self.legacy:
                    ti_value = self.normalize_to_original_si_range(
                        cast(float, SiTiCalculator.ti(frame_data, previous_frame_data))
                    )
                else:
                    ti_value = SiTiCalculator.ti(frame_data, previous_frame_data)
            else:
                ti_value = None

            logger.debug(
                f"SI value {np.around(SiTiCalculator.si(frame_data), 3)}, normalized: {np.around(self.normalize_to_original_si_range(SiTiCalculator.si(frame_data)), 3)}"
            )
            if ti_value is not None:
                logger.debug(
                    f"TI value {np.around(cast(float, SiTiCalculator.ti(frame_data, previous_frame_data)), 3)}, normalized: {np.around(self.normalize_to_original_si_range(cast(float, SiTiCalculator.ti(frame_data, previous_frame_data))), 3)}"
                )

            self.si_values.append(cast(float, si_value))
            if ti_value is not None:
                self.ti_values.append(cast(float, ti_value))

            previous_frame_data = frame_data

            current_frame += 1

            for callback in self.callbacks:
                callback(si_value, ti_value, current_frame)

            if num_frames not in [None, 0] and current_frame >= num_frames:
                return self.si_values, self.ti_values, current_frame

        return self.si_values, self.ti_values, current_frame

    def get_csv_results(self) -> str:
        """
        Return a CSV string with the results.

        Note that this does not output all data. Also, the first TI value will be output as "None".
        """
        # prepend a zero here
        ti_values_to_output = [None, *self.ti_values]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["input_file", "n", "si", "ti"])
        writer.writeheader()
        for idx, (si_value, ti_value) in enumerate(
            zip(self.si_values, ti_values_to_output)
        ):
            writer.writerow(
                {
                    "input_file": os.path.basename(self.last_input_file)
                    if self.last_input_file is not None
                    else "",
                    "n": idx + 1,
                    "si": np.round(si_value, 3),
                    "ti": np.round(ti_value, 3) if ti_value is not None else None,
                }
            )
        return output.getvalue()

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

    def _log_frame_data(self, frame_data: np.ndarray):
        logger.debug(
            f"  [{np.around(np.min(frame_data), 3)}, {np.around(np.max(frame_data), 3)}], mean {np.around(np.mean(frame_data), 3)}, median {np.around(np.median(frame_data), 3)}"
        )
        if self.show_histogram:
            logger.debug("\n" + SiTiCalculator.plot_histogram(frame_data))

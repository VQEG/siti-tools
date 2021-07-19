#!/usr/bin/env python3
#
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

import argparse
from .siti import (
    DEFAULT_HDR_MODE,
    DEFAULT_SDR_RANGE,
    DEFAULT_EOTF_FUNCTION,
    DEFAULT_GAMMA,
    DEFAULT_L_MIN,
    DEFAULT_L_MAX,
    DEFAULT_L_MIN_HDR,
    DEFAULT_L_MAX_HDR,
    HdrMode,
    SdrRange,
    EotfFunction,
)


class CustomFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    """
    Format missing defaults with empty string.
    See: https://stackoverflow.com/a/34545549/435093
    """

    def _get_help_string(self, action):
        help = action.help

        if "(default: " in action.help:
            return help

        if action.default is not argparse.SUPPRESS:
            defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                if action.default is None:
                    help += ""
                else:
                    help += " (default: %(default)s)"
        return help


def main():
    parser = argparse.ArgumentParser(formatter_class=CustomFormatter)

    group_general = parser.add_argument_group("general")
    group_general.add_argument(
        "input",
        help="Input file, can be Y4M or file in FFmpeg-readable container",
        type=str,
    )
    group_general.add_argument(
        "-n",
        "--num-frames",
        help="Number of frames to calculate, must be >= 2 (default: unlimited)",
        type=int,
    )
    group_general.add_argument("-v", "--verbose", action="store_true")
    group_general.add_argument(
        "-m",
        "--mode",
        help="Select HDR mode",
        type=HdrMode,
        choices=list(HdrMode),
        default=DEFAULT_HDR_MODE,
    )

    group_sdr = parser.add_argument_group("SDR options")
    group_sdr.add_argument(
        "-r",
        "--range",
        help="Specify limited or full range for SDR",
        type=SdrRange,
        choices=list(SdrRange),
        default=DEFAULT_SDR_RANGE,
    )
    group_sdr.add_argument(
        "-e",
        "--eotf-function",
        help="Specify the EOTF function for converting SDR to HDR",
        type=EotfFunction,
        choices=list(EotfFunction),
        default=DEFAULT_EOTF_FUNCTION,
    )
    group_sdr.add_argument(
        "-g",
        "--gamma",
        help="Specify gamma for BT.1886 function",
        default=DEFAULT_GAMMA,
        type=float,
    )

    group_display = parser.add_argument_group("Display options")
    # Valid for ITU-R BT.1886 and ITU-R BT.2100 - TABLE 5
    group_display.add_argument(
        "--l-max",
        help=f"Nominal peak luminance of the display in cd/m2 for achromatic pixels (default: {DEFAULT_L_MAX} for SDR, {DEFAULT_L_MAX_HDR} for HDR)",
        type=float,
    )
    # Valid for ITU-R BT.1886 and ITU-R BT.2100 - TABLE 5
    group_display.add_argument(
        "--l-min",
        help=f"Display luminance for black in cd/m2 (default: {DEFAULT_L_MIN} for SDR, {DEFAULT_L_MIN_HDR} for HDR)",
        type=float,
    )

    cli_args = parser.parse_args()

    print(cli_args)


if __name__ == "__main__":
    main()

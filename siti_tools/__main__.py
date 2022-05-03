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
import json
import logging
import sys
from tqdm import tqdm
from .log import CustomLogFormatter
from .siti import (
    CalculationDomain,
    ColorRange,
    EotfFunction,
    HdrMode,
    Pu21Mode,
    SiTiCalculator,
)


class CustomArgsFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    """
    Format missing defaults with empty string.
    See: https://stackoverflow.com/a/34545549/435093
    """

    def __init__(self, prog) -> None:
        super().__init__(prog, width=100)

    def _get_help_string(self, action):
        help = action.help

        if help is None:
            return help

        if "(default: " in help:
            return help

        if action.default is not argparse.SUPPRESS:
            defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                if action.default is None:
                    help += ""
                else:
                    help += " (default: %(default)s)"
        return help


def setup_logger(level: int = logging.INFO):
    logger = logging.getLogger("siti")
    logger.setLevel(level)

    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(level)

    ch.setFormatter(CustomLogFormatter())

    logger.addHandler(ch)

    return logger


def main():
    parser = argparse.ArgumentParser(prog="siti-tools", formatter_class=CustomArgsFormatter)

    group_io = parser.add_argument_group("input/output")
    group_io.add_argument(
        "input",
        help="Input file, can be Y4M or file in FFmpeg-readable container",
        type=str,
    )
    group_io.add_argument(
        "-s",
        "--settings",
        help="Load settings from previous JSON results file instead of using CLI args",
        type=str,
    )
    group_io.add_argument(
        "-n",
        "--num-frames",
        help="Number of frames to calculate, must be >= 2 (default: unlimited)",
        type=int,
    )
    group_io.add_argument(
        "--max-frames",
        help="Overall number of frames, useful for providing better time estimates from the command-line",
        type=int,
    )
    group_io.add_argument(
        "-f",
        "--format",
        help="Choose the output format (default: json)",
        type=str,
        choices=["json", "csv"],
        default="json",
    )
    group_io.add_argument(
        "-v", "--verbose", action="store_true", help="Show debug info on stderr"
    )
    group_io.add_argument(
        "--show-histogram",
        action="store_true",
        help="Show a histogram for the first frame (computation-intensive, implies --verbose)",
    )
    group_io.add_argument(
        "-q", "--quiet", action="store_true", help="Do not show progress bar"
    )

    group_general = parser.add_argument_group("Video/SI options")
    group_general.add_argument(
        "-c",
        "--calculation-domain",
        help="Select calculation domain",
        type=CalculationDomain,
        choices=list(CalculationDomain),
        default=SiTiCalculator.DEFAULT_CALCULATION_DOMAIN,
    )
    group_general.add_argument(
        "-m",
        "--hdr-mode",
        help="Select HDR mode",
        type=HdrMode,
        choices=list(HdrMode),
        default=SiTiCalculator.DEFAULT_HDR_MODE,
    )
    group_general.add_argument(
        "-b",
        "--bit-depth",
        help="Select bit depth",
        type=int,
        choices=[8, 10, 12],
        default=8,
    )
    group_general.add_argument(
        "-r",
        "--color-range",
        help="Specify limited or full range",
        type=ColorRange,
        choices=list(ColorRange),
        default=SiTiCalculator.DEFAULT_COLOR_RANGE,
    )
    group_general.add_argument(
        "--legacy",
        help="Use legacy mode, disables all other features except for range adjustment",
        action="store_true",
    )

    group_sdr = parser.add_argument_group("SDR options")
    group_sdr.add_argument(
        "-e",
        "--eotf-function",
        help="Specify the EOTF function for converting SDR to HDR",
        type=EotfFunction,
        choices=list(EotfFunction),
        default=SiTiCalculator.DEFAULT_EOTF_FUNCTION,
    )
    group_sdr.add_argument(
        "-g",
        "--gamma",
        help="Specify gamma for BT.1886 function",
        default=SiTiCalculator.DEFAULT_GAMMA,
        type=float,
    )

    group_display = parser.add_argument_group("Display options")
    # Valid for ITU-R BT.1886 and ITU-R BT.2100 - TABLE 5
    group_display.add_argument(
        "--l-max",
        help=f"Nominal peak luminance of the display in cd/m2 for achromatic pixels (default: {SiTiCalculator.DEFAULT_L_MAX} for SDR, {SiTiCalculator.DEFAULT_L_MAX_HDR} for HDR)",
        type=float,
    )
    # Valid for ITU-R BT.1886 and ITU-R BT.2100 - TABLE 5
    group_display.add_argument(
        "--l-min",
        help=f"Display luminance for black in cd/m2 (default: {SiTiCalculator.DEFAULT_L_MIN} for SDR, {SiTiCalculator.DEFAULT_L_MIN_HDR} for HDR)",
        type=float,
    )

    group_pu21 = parser.add_argument_group("PU21 options")
    group_pu21.add_argument(
        "--pu21-mode",
        help="Specify mode for PU21",
        type=Pu21Mode,
        choices=list(Pu21Mode),
        default=SiTiCalculator.DEFAULT_PU21_MODE,
    )

    cli_args = parser.parse_args()

    setup_logger(logging.DEBUG if cli_args.verbose else logging.INFO)

    if cli_args.settings:
        # read existing settings from output file
        with open(cli_args.settings, "r") as results_file:
            results = json.load(results_file)
            settings = results["settings"]
            version: str = settings["version"]
            if not version.startswith("0."):
                raise RuntimeError(
                    "Cannot parse settings with version 1.x"
                )  # TODO: remove later once bumped to 1.x
            del settings["version"]

            # convert strings to Enum
            if "calculation_domain" in settings:
                settings["calculation_domain"] = CalculationDomain[
                    settings["calculation_domain"].upper()
                ]
            if "hdr_mode" in settings:
                settings["hdr_mode"] = HdrMode[settings["hdr_mode"].upper()]
            if "bit_depth" in settings:
                settings["bit_depth"] = settings["bit_depth"]
            if "color_range" in settings:
                settings["color_range"] = ColorRange[settings["color_range"].upper()]
            if "eotf_function" in settings:
                settings["eotf_function"] = EotfFunction[
                    settings["eotf_function"].upper()
                ]
            if "pu21_mode" in settings:
                settings["pu21_mode"] = Pu21Mode[settings["pu21_mode"].upper()]

            si_ti_calculator = SiTiCalculator.from_settings(settings)
    else:
        si_ti_calculator = SiTiCalculator(
            calculation_domain=cli_args.calculation_domain,
            hdr_mode=cli_args.hdr_mode,
            bit_depth=cli_args.bit_depth,
            color_range=cli_args.color_range,
            eotf_function=cli_args.eotf_function,
            l_max=cli_args.l_max,
            l_min=cli_args.l_min,
            gamma=cli_args.gamma,
            pu21_mode=cli_args.pu21_mode,
            verbose=cli_args.verbose,
            show_histogram=cli_args.show_histogram,
            legacy=cli_args.legacy,
        )

    if not cli_args.quiet:
        # render the maximum in the progress bar, rather than just an iterator
        overall_max_frames = max(
            cli_args.num_frames if cli_args.num_frames is not None else 0,
            cli_args.max_frames if cli_args.max_frames is not None else 0,
        )
        pbar = tqdm(total=overall_max_frames if overall_max_frames != 0 else None)

        def frame_callback(_, __, ___):
            pbar.update(1)

        si_ti_calculator.add_frame_callback(frame_callback)

    si_ti_calculator.calculate(
        cli_args.input,
        num_frames=cli_args.num_frames,
    )

    if cli_args.format == "json":
        results = si_ti_calculator.get_results()
        print(json.dumps(results, indent=4))
    elif cli_args.format == "csv":
        results = si_ti_calculator.get_csv_results()
        print(results)
    else:
        raise RuntimeError(f"No such format {cli_args.format}")


if __name__ == "__main__":
    main()

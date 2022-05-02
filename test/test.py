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

import sys
import os
from typing import Dict, List, Tuple, Union
from numpy import NaN
import pytest
import requests
from tqdm import tqdm
from itertools import zip_longest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from siti_tools.file import read_container  # noqa: E402
from siti_tools.siti import (
    SiTiCalculator,
    ColorRange,
    EotfFunction,
    HdrMode,
)  # noqa: E402


def pytest_generate_tests(metafunc):
    """
    This function automatically populates the tests based on the contents of the 'MAIN_SCENARIOS' and 'CALCULATOR_SCENARIOS' variables below.
    """
    test_siti_main_scenario_ids = []
    test_siti_main_argvalues = []
    test_siti_main_argnames = []

    test_siti_calculator_scenario_ids = []
    test_siti_calculator_argvalues = []
    test_siti_calculator_argnames = []

    if metafunc.function.__name__ == "test_siti_main_functions":
        for scenario in metafunc.cls.MAIN_SCENARIOS:
            # e.g. ('basic testing', {'input_file': 'test.mp4', 'ground_truth': 'test.json'})
            scenario_id, scenario_params = scenario
            test_siti_main_scenario_ids.append(scenario_id)
            scenario_kwargs = scenario_params.items()
            test_siti_main_argnames = [x[0] for x in scenario_kwargs]
            test_siti_main_argvalues.append([x[1] for x in scenario_kwargs])

        metafunc.parametrize(
            test_siti_main_argnames,
            test_siti_main_argvalues,
            ids=test_siti_main_scenario_ids,
            scope="class",
        )

    elif metafunc.function.__name__ == "test_siti_calculator":
        for scenario in metafunc.cls.CALCULATOR_SCENARIOS:
            scenario_id, scenario_params = scenario
            test_siti_calculator_scenario_ids.append(scenario_id)
            scenario_kwargs = scenario_params.items()
            test_siti_calculator_argnames = [x[0] for x in scenario_kwargs]
            test_siti_calculator_argvalues.append([x[1] for x in scenario_kwargs])

        metafunc.parametrize(
            test_siti_calculator_argnames,
            test_siti_calculator_argvalues,
            ids=test_siti_calculator_scenario_ids,
            scope="class",
        )


class TestSiti:
    MAIN_SCENARIOS = [
        (
            "foreman_cif",
            {"input_file": "foreman_cif.y4m", "ground_truth": "foreman_cif.csv"},
        ),
        # Add further tests here, by creating ground truth CSV files. You can use
        # the ./generate_raw_siti_values.py helper for doing this.
    ]

    CALCULATOR_SCENARIOS = [
        # These require further instantiation via the SiTiCalculator class, with further meta variables.
        # Add your examples like this:
        #
        # {
        #     "input_file": "<a URL to a remote file, or a filename of a local file in /test/videos/>",
        #     "max_download_len": <bytes to download, set to None for local files>
        #     "ground_truth": "<name of JSON file with ground truth>",
        #     "siti_calculator_kwargs": {
        #       <any options passed to SiTiCalculator as key-value pair>
        #     },
        # },
        #
        #
        (
            "FourPeople_480x270_60.y4m",
            {
                "input_file": "https://media.xiph.org/video/aomctc/test_set/a5_270p/FourPeople_480x270_60.y4m",
                "ground_truth": "FourPeople_480x270_60.json",
                "max_download_len": 10 * 1024 * 1024,  # 10 MiB
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "ParkJoy_480x270_50.y4m",
            {
                "input_file": "https://media.xiph.org/video/aomctc/test_set/a5_270p/ParkJoy_480x270_50.y4m",
                "ground_truth": "ParkJoy_480x270_50.json",
                "max_download_len": 10 * 1024 * 1024,  # 10 MiB
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "SparksElevator_480x270p_5994_10bit.y4m",
            {
                "input_file": "https://media.xiph.org/video/aomctc/test_set/a5_270p/SparksElevator_480x270p_5994_10bit.y4m",
                "ground_truth": "SparksElevator_480x270p_5994_10bit.json",
                "max_download_len": 10 * 1024 * 1024,  # 10 MiB
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "bit_depth": 10,
                },
            },
        ),
        (
            "SparksTruck_2048x1080_5994_hdr10.y4m",
            {
                "input_file": "https://media.xiph.org/video/aomctc/test_set/hdr2_2k/SparksTruck_2048x1080_5994_hdr10.y4m",
                "ground_truth": "SparksTruck_2048x1080_5994_hdr10.json",
                "max_download_len": 50 * 1024 * 1024,  # 50 MiB, should be ~7 frames
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "bit_depth": 10,
                    "hdr_mode": HdrMode.HDR10,
                },
            },
        ),
        (
            "black.y4m",
            {
                "input_file": "black.y4m",
                "ground_truth": "black.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "checkerboard-1x1.y4m",
            {
                "input_file": "checkerboard-1x1.y4m",
                "ground_truth": "checkerboard-1x1.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "checkerboard-8x8.y4m",
            {
                "input_file": "checkerboard-8x8.y4m",
                "ground_truth": "checkerboard-8x8.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "checkerboard-8x8-10bpp-limited.y4m",
            {
                "input_file": "checkerboard-8x8-10bpp-limited.y4m",
                "ground_truth": "checkerboard-8x8-10bpp-limited.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.LIMITED,
                    "bit_depth": 10,
                },
            },
        ),
        (
            "checkerboard-8x8-10bpp.y4m",
            {
                "input_file": "checkerboard-8x8-10bpp.y4m",
                "ground_truth": "checkerboard-8x8-10bpp.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "bit_depth": 10,
                },
            },
        ),
        (
            "foreman_cif.y4m",
            {
                "input_file": "foreman_cif.y4m",
                "ground_truth": "foreman_cif.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "full-range.y4m",
            {
                "input_file": "full-range.y4m",
                "ground_truth": "full-range.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "limited-range.y4m",
            {
                "input_file": "limited-range.y4m",
                "ground_truth": "limited-range.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.LIMITED,
                },
            },
        ),
        (
            "legacy foreman_cif.y4m",
            {
                "input_file": "foreman_cif.y4m",
                "ground_truth": "foreman_cif-legacy.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "legacy": True,
                },
            },
        ),
        (
            "legacy full-range.y4m",
            {
                "input_file": "full-range.y4m",
                "ground_truth": "full-range-legacy.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "legacy": True,
                },
            },
        ),
        (
            "legacy limited-range.y4m",
            {
                "input_file": "limited-range.y4m",
                "ground_truth": "limited-range-legacy.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.LIMITED,
                    "legacy": True,
                },
            },
        ),
        (
            "noise.y4m",
            {
                "input_file": "noise.y4m",
                "ground_truth": "noise.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "white.y4m",
            {
                "input_file": "white.y4m",
                "ground_truth": "white.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                },
            },
        ),
        (
            "sunset-hlg.mov",
            {
                "input_file": "sunset-hlg.mov",
                "ground_truth": "sunset-hlg.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "hdr_mode": HdrMode.HLG,
                    "bit_depth": 10,
                },
            },
        ),
        (
            "lights-hlg.mov",
            {
                "input_file": "lights-hlg.mov",
                "ground_truth": "lights-hlg.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "hdr_mode": HdrMode.HLG,
                    "bit_depth": 10,
                },
            },
        ),
        (
            "fall-hlg.mov",
            {
                "input_file": "fall-hlg.mov",
                "ground_truth": "fall-hlg.json",
                "max_download_len": None,
                "siti_calculator_kwargs": {
                    "color_range": ColorRange.FULL,
                    "hdr_mode": HdrMode.HLG,
                    "bit_depth": 10,
                },
            },
        ),
        # (
        #     "CosmosCaterpillar_2048x858p24_hdr10",
        #     {
        #         "input_file": "https://media.xiph.org/video/aomctc/test_set/hdr2_2k/CosmosCaterpillar_2048x858p24_hdr10.y4m",
        #         "ground_truth": "CosmosCaterpillar_2048x858p24_hdr10.json",
        #     },
        # )
    ]

    @staticmethod
    def _read_ground_truth_csv(ground_truth: str) -> List[Dict[str, float]]:
        ret = []
        with open(ground_truth, "r") as gtf:
            header_read = False
            for line in gtf.readlines():
                if not header_read:
                    header_read = True
                    continue
                line = line.strip()
                si, ti, _ = line.split(",")
                if ti == "" or ti == "None":
                    ti = NaN
                ret.append({"si": float(si), "ti": float(ti)})
        return ret

    @staticmethod
    def _read_ground_truth_json(ground_truth: str) -> Dict:
        """
        Read the ground truth JSON file and return the entire dictionary
        """
        with open(ground_truth, "r") as gtf:
            content = json.load(gtf)
            return content

    @staticmethod
    def _try_download_file(
        remote_path: str, local_path: str, max_download_len: Union[int, None] = None
    ):
        """Download a remote file via HTTP/S

        Args:
            remote_path (str): The remote URL
            local_path (str): The local storage path
            max_download_len (int): The maximum number of bytes to download (default: None)
        """
        print(f"Downloading to {local_path} ...")
        response = requests.get(remote_path, stream=True)
        content_length = int(response.headers.get("content-length", 0))

        if max_download_len is None:
            total_size_in_bytes = content_length
        else:
            total_size_in_bytes = min(content_length, max_download_len)

        total_downloaded = 0
        block_size = 1024 * 1024  # 1 MiB
        progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)
        with open(local_path, "wb") as local_file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                total_downloaded += len(data)
                local_file.write(data)
                if (
                    max_download_len is not None
                    and total_downloaded >= max_download_len
                ):
                    print(
                        f"Stopping download of {local_path} after {total_downloaded} Bytes"
                    )
                    break
        progress_bar.close()

    @staticmethod
    def _download_file_if_needed(input_file: str, max_download_len: Union[int, None] = None):
        """
        Check if a local file already exists for the given URL; if not, download it
        """
        input_file_path = os.path.join(os.path.dirname(__file__), "videos", input_file)
        if not os.path.isfile(input_file_path) and input_file.startswith("https:"):
            local_path = os.path.join(
                os.path.dirname(__file__), "videos", os.path.basename(input_file_path)
            )
            if not os.path.isfile(local_path):
                TestSiti._try_download_file(
                    input_file, local_path, max_download_len=max_download_len
                )

    def test_siti_calculator(
        self,
        input_file: str,
        ground_truth: str,
        max_download_len: int,
        siti_calculator_kwargs: Dict,
    ):
        """
        Test the SiTiCalculator class, with the display model/HDR conversion.

        Args:
            input_file (str): file name of the input file or HTTP(S) path in case of remote video
            ground_truth (str): file name of ground truth JSON file
            max_download_len (int): max length of file to download, in case of remote video
            siti_calculator_kwargs: any arguments passed to the SiTiCalculator class
        """
        print()
        print(f"Testing {input_file}")
        TestSiti._download_file_if_needed(input_file, max_download_len)

        ground_truth_path = os.path.join(
            os.path.dirname(__file__), "ground_truth", ground_truth
        )
        gt = TestSiti._read_ground_truth_json(ground_truth_path)

        print(f"Ground truth: {gt}")

        input_file_path = os.path.join(
            os.path.dirname(__file__), "videos", os.path.basename(input_file)
        )
        calculator = SiTiCalculator(**siti_calculator_kwargs)
        si_values, ti_values, _ = calculator.calculate(input_file_path)

        # we require one more SI value than TI values, since first frame is not defined
        assert len(si_values) == len(ti_values) + 1

        for frame_idx, (si_value, si_gt) in enumerate(zip(si_values, gt["si"])):
            print(f"Frame {frame_idx+1}, SI {si_value}, Ground Truth {si_gt}")
            assert pytest.approx(si_value, 0.01) == si_gt

        for frame_idx, (ti_value, ti_gt) in enumerate(zip(ti_values, gt["ti"])):
            print(f"Frame {frame_idx+1}, TI {ti_value}, Ground Truth {ti_gt}")
            assert pytest.approx(ti_value, 0.01) == ti_gt

    def test_siti_main_functions(self, input_file: str, ground_truth: str):
        """
        Test the raw SI/TI calculation functions.

        Note: This does not test the entire integration with the display model/HDR conversion.

        Args:
            input_file (str): file name of the input file or HTTP(S) path in case of remote video
            ground_truth (str): file name of ground truth file
        """
        print()
        print(f"Testing {input_file}")
        TestSiti._download_file_if_needed(input_file)

        input_file_path = os.path.join(os.path.dirname(__file__), "videos", input_file)
        frame_generator = read_container(input_file_path)

        ground_truth_path = os.path.join(
            os.path.dirname(__file__), "ground_truth", ground_truth
        )
        gt = TestSiti._read_ground_truth_csv(ground_truth_path)

        frame_cnt = 1

        previous_frame_data = None
        for frame_data, gt_data in zip(frame_generator, gt):
            si_value = SiTiCalculator.si(frame_data)
            ti_value = SiTiCalculator.ti(frame_data, previous_frame_data)

            print(f"Frame {frame_cnt}: SI {si_value}, {ti_value}")
            print(f"Ground truth: {gt_data}")

            assert pytest.approx(si_value, 0.01) == gt_data["si"]

            if frame_cnt == 1:
                assert ti_value is None
            else:
                assert pytest.approx(ti_value, 0.01) == gt_data["ti"]

            previous_frame_data = frame_data
            frame_cnt += 1

        print(f"Frames tested: {frame_cnt}")

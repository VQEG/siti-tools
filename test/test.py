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
from typing import Dict, List
from numpy import NaN
import pytest
import requests
from tqdm import tqdm

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
            # e.g. ('basic testing', {'input_file': 'test.mp4', 'ground_truth': 'test.csv'})
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
        ("basic testing", {"input_file": "test.mp4", "ground_truth": "test.csv"}),
        (
            "foreman",
            {"input_file": "foreman_cif.y4m", "ground_truth": "foreman_cif.csv"},
        ),
        # add further tests here
    ]

    CALCULATOR_SCENARIOS = [
        # TODO
        # these require further instantiation via the SiTiCalculator class, with further meta variables
        (
            "FourPeople_480x270_60.y4m",
            {
                "input_file": "https://media.xiph.org/video/aomctc/test_set/a5_270p/FourPeople_480x270_60.y4m",
                "ground_truth": "FourPeople_480x270_60.y4m",
                "siti_calculator_kwargs": {"hdr_mode": HdrMode.HDR10},
            },
        )
        # (
        #     "CosmosCaterpillar_2048x858p24_hdr10",
        #     {
        #         "input_file": "https://media.xiph.org/video/aomctc/test_set/hdr2_2k/CosmosCaterpillar_2048x858p24_hdr10.y4m",
        #         "ground_truth": "CosmosCaterpillar_2048x858p24_hdr10.csv",
        #     },
        # )
    ]

    @staticmethod
    def _read_ground_truth(ground_truth: str) -> List[Dict[str, float]]:
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
    def _try_download_file(remote_path: str, local_path: str):
        """Download a remote file via HTTP/S

        Args:
            remote_path (str): The remote URL
            local_path (str): The local storage path
        """
        print(f"Downloading to {local_path} ...")
        response = requests.get(remote_path, stream=True)
        total_size_in_bytes = int(response.headers.get("content-length", 0))
        block_size = 1024 * 1024  # 1 MiB
        progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)
        with open(local_path, "wb") as local_file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                local_file.write(data)
        progress_bar.close()

    @staticmethod
    def _download_file_if_needed(input_file: str):
        input_file_path = os.path.join(os.path.dirname(__file__), "videos", input_file)
        if not os.path.isfile(input_file_path) and input_file.startswith("https:"):
            local_path = os.path.join(
                os.path.dirname(__file__), "videos", os.path.basename(input_file_path)
            )
            if not os.path.isfile(local_path):
                TestSiti._try_download_file(input_file, local_path)

    def test_siti_calculator(
        self,
        input_file: str,
        ground_truth: str,
        siti_calculator_kwargs: Dict,
    ):
        """
        Test the SiTiCalculator class, with the display model/HDR conversion.

        Args:
            input_file (str): file name of the input file or HTTP(S) path in case of remote video
            ground_truth (str): file name of ground truth CSV file
            siti_calculator_kwargs: any arguments passed to the SiTiCalculator class
        """
        TestSiti._download_file_if_needed(input_file)

        ground_truth_path = os.path.join(
            os.path.dirname(__file__), "ground_truth", ground_truth
        )
        gt = TestSiti._read_ground_truth(ground_truth_path)

        input_file_path = os.path.join(os.path.dirname(__file__), "videos", input_file)
        calculator = SiTiCalculator(**siti_calculator_kwargs)
        si, ti, _ = calculator.calculate(input_file_path)

        frame_cnt = 1

        for siti_results, gt_data in zip(list(zip(si, ti)), gt):
            print(f"Comparing frame {frame_cnt}")

            si_value, ti_value = siti_results

            print(si_value, ti_value)
            print(gt_data)

            assert pytest.approx(si_value, 0.01) == gt_data["si"]

            if frame_cnt == 1:
                assert ti_value is None
            else:
                assert pytest.approx(ti_value, 0.01) == gt_data["ti"]

            frame_cnt += 1

    def test_siti_main_functions(self, input_file: str, ground_truth: str):
        """
        Test the raw SI/TI calculation functions.

        Note: This does not test the entire integration with the display model/HDR conversion.

        Args:
            input_file (str): file name of the input file or HTTP(S) path in case of remote video
            ground_truth (str): file name of ground truth CSV file
        """
        TestSiti._download_file_if_needed(input_file)

        input_file_path = os.path.join(os.path.dirname(__file__), "videos", input_file)
        frame_generator = read_container(input_file_path)

        ground_truth_path = os.path.join(
            os.path.dirname(__file__), "ground_truth", ground_truth
        )
        gt = TestSiti._read_ground_truth(ground_truth_path)

        frame_cnt = 1

        previous_frame_data = None
        for frame_data, gt_data in zip(frame_generator, gt):
            print(f"Comparing frame {frame_cnt}")

            si_value = SiTiCalculator.si(frame_data)
            ti_value = SiTiCalculator.ti(frame_data, previous_frame_data)

            print(si_value, ti_value)
            print(gt_data)

            assert pytest.approx(si_value, 0.01) == gt_data["si"]

            if frame_cnt == 1:
                assert ti_value is None
            else:
                assert pytest.approx(ti_value, 0.01) == gt_data["ti"]

            previous_frame_data = frame_data
            frame_cnt += 1

        print(f"Frames tested: {frame_cnt}")

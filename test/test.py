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
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from siti_tools.file import read_container
from siti_tools.siti import si, ti


def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append([x[1] for x in items])
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


class TestSiti:
    scenarios = [
        ("basic testing", {"input_file": "test.mp4", "ground_truth": "test.csv"}),
        # add further tests here
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
                ret.append({"si": float(si), "ti": float(ti)})
        return ret

    def test_siti(self, input_file: str, ground_truth: str):
        input_file_path = os.path.join(os.path.dirname(__file__), input_file)
        ground_truth_path = os.path.join(os.path.dirname(__file__), ground_truth)

        frame_generator = read_container(input_file_path)
        gt = TestSiti._read_ground_truth(ground_truth_path)

        frame_cnt = 1

        previous_frame_data = None
        for frame_data, gt_data in zip(frame_generator, gt):
            print(f"Comparing frame {frame_cnt}")

            si_value = si(frame_data)
            ti_value = ti(frame_data, previous_frame_data)

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

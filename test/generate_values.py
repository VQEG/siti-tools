#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from siti_tools.file import read_container  # noqa: E402
from siti_tools.siti import si, ti  # noqa: E402


def main():
    previous_frame_data = None
    frame_generator = read_container(sys.argv[1])
    frame_cnt = 1

    print("si,ti,n")
    for frame_data in frame_generator:
        si_value = si(frame_data)
        ti_value = ti(frame_data, previous_frame_data)

        if ti_value is None:
            ti_value = ""

        print(",".join([str(s) for s in [si_value, ti_value, frame_cnt]]))
        frame_cnt += 1
        previous_frame_data = frame_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Need exactly one input file!")
    main()

#!/usr/bin/env python3
import pstats
import cProfile
import os
from siti_tools.siti import ColorRange, HdrMode, SiTiCalculator

here = os.path.dirname(__file__)
main_directory = os.path.abspath(os.path.join(here, "..", ".."))

if __name__ == "__main__":

    profiler = cProfile.Profile()
    calc = SiTiCalculator(color_range=ColorRange.FULL, hdr_mode=HdrMode.SDR)
    profiler.enable()
    calc.calculate(os.path.join(main_directory, "test/videos/foreman_cif.y4m"))
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("tottime")
    stats_file = os.path.join(here, "sdr-output.prof")
    profiler.dump_stats(stats_file)
    stats.print_stats()

    print(f"Output written. Run this to see the results:\n\nsnakeviz {stats_file}")

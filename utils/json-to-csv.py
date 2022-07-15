#!/usr/bin/env python3
#
# Given the input format:
#
# {
#     "si": [
#         39.3424987722349,
#         39.22872485955759,
#         39.224260422855025,
#         39.45848105156672,
#         39.212267784151706,
#         39.214055323440355,
#         39.25991139024761,
#         39.351378133455384,
#         39.34883137114782,
#         39.50381975372975
#     ],
#     "ti": [
#         5.006595555671795,
#         5.291171829162438,
#         5.080387721267477,
#         4.85377769421018,
#         4.220006520485006,
#         3.9500227400754646,
#         4.266750120698417,
#         4.915099768651993,
#         4.7700242511732265
#     ],
#     "settings": {
#         "calculation_domain": "pq",
#         "hdr_mode": "sdr",
#         "bit_depth": 8,
#         "color_range": "full",
#         "eotf_function": "bt1886",
#         "l_max": 300,
#         "l_min": 0.1,
#         "gamma": 2.4,
#         "pu21_mode": "banding",
#         "version": "0.1.2"
#     },
#     "input_file": "foreman_cif.y4m"
# }
#
# Convert it to a CSV file with the following columns:
# - input_file
# - n
# - si
# - ti


import json
import csv
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description="Convert JSON to CSV")
    parser.add_argument("input", help="input JSON file")
    parser.add_argument("output", help="output CSV file")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    # insert an empty element at index 0 of ti
    data["ti"].insert(0, None)

    with open(args.output, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["input_file", "n", "si", "ti"])
        for i in range(len(data["si"])):
            si = round(data["si"][i], 3)
            ti = round(data["ti"][i], 3) if data["ti"][i] is not None else None
            writer.writerow([os.path.basename(data["input_file"]), i + 1, si, ti])


if __name__ == "__main__":
    main()

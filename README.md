# siti-tools

[![Python package](https://github.com/VQEG/siti-tools/actions/workflows/python-package.yml/badge.svg)](https://github.com/VQEG/siti-tools/actions/workflows/python-package.yml)

SI/TI calculation tools.

Calculate spatial information (SI) and temporal information (TI).

**⚠️ Note: This is the main branch of the project. For the legacy version of SI/TI, see [the `legacy` branch](https://github.com/VQEG/siti-tools/tree/legacy)**.

Contents:

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Command Line Usage](#command-line-usage)
  - [Detailed Options](#detailed-options)
  - [Output](#output)
  - [API Usage](#api-usage)
- [Testing](#testing)
- [About](#about)
  - [What is SI/TI?](#what-is-siti)
  - [What is the purpose of this activity?](#what-is-the-purpose-of-this-activity)
  - [Contributors](#contributors)
  - [Acknowledgements](#acknowledgements)
  - [Related Projects](#related-projects)
  - [License](#license)

## Requirements

- Python 3.10.1 or higher
- FFmpeg libraries (v5 or higher)

Under Ubuntu, to get ffmpeg libraries:

    sudo apt update -qq && \
    sudo apt install \
      libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
      libavfilter-dev libswscale-dev libavresample-dev

Under macOS, it is recommended to install ffmpeg via [Homebrew](https://brew.sh):

    brew install ffmpeg

## Installation

Directly install from Git:

```bash
pip3 install --user git+https://github.com/VQEG/siti-tools
```

Or clone this repository and then:

```bash
pip3 install --user .
```

## Usage

This tool can be used via command line or through a Python API.

### Command Line Usage

After installation, simply run:

```
siti-tools /path/to/input/file.mp4
```

to run the tool. It will print JSON output containing info about SI/TI values and other statistics to `stdout`.

You can pass any video file with a container that can be read by FFmpeg. For YUV files, see below.

:warning: We are currently observing a bug with some videos that manifests in an error ("ValueError: cannot reshape array of size …"). See [this issue](https://github.com/VQEG/siti-tools/issues/17) for details. If you encounter this error, please use Y4M files as input instead.

This works for 8-bit standard dynamic range (SDR) content, which will apply to most input files. However, this tool does not automatically handle input that is not 8-bit SDR content. For more info on that, see below.

#### Usage with YUV or Y4M files

We don't recommend working with raw YUV files, as they do not carry the metadata required to decode them. Use Y4M files or any other container format that can be read by FFmpeg.

To convert YUV into Y4M, use the basic command:

```bash
ffmpeg -f rawvideo -pix_fmt yuv420p -framerate 24 -video_size 1920x1080 -i input.yuv -f yuv4mpegpipe output.y4m
```

Adapt the parameters to your input file (i.e., the pixel format, framerate, and resolution).

NOTE: If you are working with 10-bit content (e.g., if your input pixel format is `yuv420p10le`), you must add the `-strict -1` flag to the command above:

```bash
ffmpeg -f rawvideo -pix_fmt yuv420p10le -framerate 24 -video_size 1920x1080 -i input.yuv -f yuv4mpegpipe -strict -1 output.y4m
```

If you just want to convert an existing (e.g. MP4) file into Y4M, use:

```bash
ffmpeg -i input.mp4 -pix_fmt yuv420p output.y4m
```

#### Usage for > 8-bit Content

To deal with input with more than 8-bit, you can choose the bit depth:

```
siti-tools /path/to/input/file.mov --bit-depth 10
```

To check if your input really has 10 bit, you can use `ffprobe`:

```
ffprobe -v error -select_streams v:0 -show_streams test/videos/ParkJoy_480x270_50.y4m -of compact=p=0:nk=1 -show_entries stream=pix_fmt
```

If the pixel format ends with `p10`, you have a 10-bit sequence.

#### Full vs. Limited Range

If your input has full range values (0–255) instead of limited range (16–235), you must specify the following flag:

```
siti-tools /path/to/input/file.mp4 --color-range full
```

This ensures that the values are properly scaled. If you pass a full range content to the tool without specifying the flag, it will print an error.

#### HDR Usage

This tool handles HDR content encoded in HLG or HDR10. For example, if you have a HLG-encoded file with 10 bit per channel, you should call:

```
siti-tools /path/to/input/file-HLG.mov --hdr-mode hlg --bit-depth 10
```

Likewise, if you have an HDR10-encoded file:

```
siti-tools /path/to/input/file-HDR10.mp4 --hdr-mode hdr10 --bit-depth 10
```

You can further tune the HDR parameters. The most important ones are the assumed display luminance values, which can be set via `--l-max` and `--l-min`. We have chosen sane defaults here, but depending on your application you may want to override them.

### Detailed Options

Run `siti-tools -h` for a full list of command line options:

```
usage: siti-tools [-h] [-s SETTINGS] [-n NUM_FRAMES] [--max-frames MAX_FRAMES] [-f {json,csv}] [-v]
                  [--show-histogram] [-q] [-c {pq,pu21}] [-m {sdr,hdr10,hlg}] [-b {8,10,12}]
                  [-r {limited,full}] [--legacy] [-e {bt1886,inv_srgb}] [-g GAMMA] [--l-max L_MAX]
                  [--l-min L_MIN] [--pu21-mode {banding,banding_glare,peaks,peaks_glare}]
                  input

optional arguments:
  -h, --help            show this help message and exit

input/output:
  input                 Input file, can be Y4M or file in FFmpeg-readable container
  -s SETTINGS, --settings SETTINGS
                        Load settings from previous JSON results file instead of using CLI args
  -n NUM_FRAMES, --num-frames NUM_FRAMES
                        Number of frames to calculate, must be >= 2 (default: unlimited)
  --max-frames MAX_FRAMES
                        Overall number of frames, useful for providing better time estimates from
                        the command-line
  -f {json,csv}, --format {json,csv}
                        Choose the output format (default: json)
  -v, --verbose         Show debug info on stderr (default: False)
  --show-histogram      Show a histogram for the first frame (computation-intensive, implies
                        --verbose) (default: False)
  -q, --quiet           Do not show progress bar (default: False)

Video/SI options:
  -c {pq,pu21}, --calculation-domain {pq,pu21}
                        Select calculation domain (default: pq)
  -m {sdr,hdr10,hlg}, --hdr-mode {sdr,hdr10,hlg}
                        Select HDR mode (default: sdr)
  -b {8,10,12}, --bit-depth {8,10,12}
                        Select bit depth (default: 8)
  -r {limited,full}, --color-range {limited,full}
                        Specify limited or full range (default: limited)
  --legacy              Use legacy mode, disables all other features except for range adjustment
                        (default: False)

SDR options:
  -e {bt1886,inv_srgb}, --eotf-function {bt1886,inv_srgb}
                        Specify the EOTF function for converting SDR to HDR (default: bt1886)
  -g GAMMA, --gamma GAMMA
                        Specify gamma for BT.1886 function (default: 2.4)

Display options:
  --l-max L_MAX         Nominal peak luminance of the display in cd/m2 for achromatic pixels
                        (default: 300 for SDR, 1000.0 for HDR)
  --l-min L_MIN         Display luminance for black in cd/m2 (default: 0.1 for SDR, 0.01 for HDR)

PU21 options:
  --pu21-mode {banding,banding_glare,peaks,peaks_glare}
                        Specify mode for PU21 (default: banding)
```

### Output

The tool will output a valid JSON object on `stdout`, with SI and TI scores contained in an array.

To redirect the output to a file, use shell redirection:

```bash
siti-tools input1.mp4 > input1.json
```

Note that the first frame has no TI value by definition, so a file with two frames would produce the following output:

```json
{
    "si": [
        4.678114135021466,
        4.690539260164495
    ],
    "ti": [
        0.33096454208633247
    ],
    "settings": {
        "calculation_domain": "pq",
        "hdr_mode": "sdr",
        "bit_depth": 8,
        "color_range": "full",
        "eotf_function": "bt1886",
        "l_max": 300,
        "l_min": 0.1,
        "gamma": 2.4,
        "pu21_mode": "banding",
        "legacy": false,
        "version": "0.1.2"
    },
    "input_file": "FourPeople_480x270_60.y4m"
}
```

In the `settings` key, you will find information on how the calculation was done. This is useful for allowing values to be reproduced. You can use these settings for further calculation runs. For instance, if you want to use the settings used for `input1` for `input2`, run the following:

```
siti-tools input1.mp4 > input1.json
siti-tools input2.mp4 --settings input1.json > input2.json
```

You can also generate CSV output, which will contain fewer columns but is easier to parse.

```bash
siti-tools input1.mp4 --format csv > input1.csv
siti-tools input2.mp4 --settings input1.json --format csv > input2.csv
```

The output might look like this:

```
input_file,n,si,ti
foreman_cif.y4m,1,39.342,
foreman_cif.y4m,2,39.229,5.007
foreman_cif.y4m,3,39.224,5.291
foreman_cif.y4m,4,39.458,5.08
foreman_cif.y4m,5,39.212,4.854
foreman_cif.y4m,6,39.214,4.22
foreman_cif.y4m,7,39.26,3.95
foreman_cif.y4m,8,39.351,4.267
foreman_cif.y4m,9,39.349,4.915
foreman_cif.y4m,10,39.504,4.77
```

Note that the first TI value is empty by definition.

There is also a handy conversion utility to help you convert JSON to CSV files after you have calculated the scores.

```bash
utils/json-to-csv.py input.json input.csv
```

### API Usage

The tools expose the calculation functions via an API.

For instance, you can directly use the SI/TI functions:

```python
import numpy as np
from siti_tools.siti import SiTiCalculator  # noqa: E402

frame_data = ... # some numpy array
previous_frame_data = ... # some other numpy array

si_value = SiTiCalculator.si(frame_data)
ti_value = SiTiCalculator.ti(frame_data, previous_frame_data)
```

See the `test/generate_raw_siti_values.py` file for an example of how to use those.

Or, you can use the calculator class to do the conversions required for higher bit depths and HDR:

```python
import json
from siti_tools.siti import ColorRange, SiTiCalculator

si_ti_calculator = SiTiCalculator(
            color_range=ColorRange.LIMITED,
            # ... other settings go here
        )

si_ti_calculator.calculate(
    path_to_input_file,
    num_frames=3, # only calculate 3 frames
)

results = si_ti_calculator.get_results()

print(json.dumps(results, indent=4))
```

See the `siti_tools/__main__.py` file on how to specify all options.

## Testing

This repo provides a set of test sequences with expected output values that you can verify against.

First, install the dev dependencies:

```
pip3 install -r requirements.dev.txt
```

Generate the sequences:

```bash
cd test && ./generate_ffmpeg_sources.sh && cd -
```

Then run:

```bash
python3 -m pytest test/test.py -n auto
```

The `-n auto` flag distributes the test to all cores. Remove it if you want to capture stdout with `-s`.

## About

### What is SI/TI?

The following info is given about SI / TI in [ITU-T Recommendation P.910](https://www.itu.int/rec/T-REC-P.910) (10/2023) – "Subjective video quality assessment methods for multimedia applications". This is the most recent version of the document at the time of writing. Version 07/2022 has introduced significant changes to the SI/TI calculation, which are reflected in this repository.

> **Spatial Information**: A measure that indicates the amount of spatial detail in a picture. It is usually higher for more spatially complex scenes. It is not meant to be a measure of entropy nor is it associated with the information defined in communication theory

> **Temporal information**: A measure that indicates the number of temporal changes of a video sequence. It is usually higher for high motion sequences. It is not meant to be a measure of entropy nor associated with the information defined in communication theory.

SI and TI are based on the Sobel filter, which is a simple edge detector. The Sobel filter is applied to the luminance channel of the input video, and the resulting values are aggregated to a single value. For a detailed calculation, see Annex B of ITU-T Rec. P.910 (10/2023)

Further, Clause 7.8 states:

> The selection of test scenes is an important issue. In particular, the spatial information (SI) and temporal information (TI) of the scenes are critical parameters. These parameters play a crucial role in determining the amount of video compression that is possible (compressibility), and consequently, the level of impairment that is suffered when the scene is transmitted over a fixed-rate digital transmission service channel. Fair and relevant video test scenes must be chosen such that their SI and TI is consistent with the video services that the digital transmission service channel was intended to provide. The set of test scenes should span the full range of SI and TI of interest to users of the devices under test.

Regarding the aggregation of SI/TI values, Clause 7.8.4 states:

> Multiple SI and TI values per sequence may be aggregated into single numbers for SI and TI, respectively, by applying appropriate statistical measures such as the minimum, maximum, median, average, or percentiles.
It is recommended to use the average as an aggregation measure.

If you have used a previous version of SI/TI, please consider:

> Note that in the previous versions of Recommendation ITU-T P.910, the respective maximum value was recommended as aggregated score for SI and TI. (…) If the resulting SI and TI values are being compared to those provided in publications or with publicly available databases, deviations may stem from the previously recommended usage of the maximum.

For further information, please refer to the ITU-T Rec. P.910 document.

### What is the purpose of this activity?

The [No-Reference Metrics (NORM)](https://www.its.bldrdoc.gov/vqeg/projects/no-reference-metrics-norm.aspx) working group of the [Video Quality Expert Group (VQEG)](https://www.its.bldrdoc.gov/vqeg/vqeg-home.aspx) has investigated the Spatial Information (SI) and Temporal Information (TI) indicators defined in ITU-T Rec. P.910.

SI and TI have been frequently used by the community to classify sets of video sequences or video databases, primarily for checking that the used material spans an appropriate range of spatiotemporal complexity before further processing the sequences (e.g., encoding them, presenting them to subjects). Since they are easy and quick to calculate, SI/TI are still very relevant today.

VQEG identified several limitations with the current definition of SI/TI, including the following:

- It was not specified how to handle video with limited (16-235) vs. full range (0-255).
- The applicable range of input bit depths (bits per channel) was not specified. This means that it was unclear how to handle content with different bit depths, in particular when comparing sequences of varying bit depth.
- It was undefined how to handle high dynamic range (HDR) content, where the luminance information might be encoded differently compared to standard dynamic range (SDR).

The overall aims of this activity were the following:

- Providing an updated set of calculation functions for SI and TI that cover limited/full range content, higher bit depths, and HDR sequences
- Providing a set of test sequences and expected values (i.e., test vectors) in order to allow others to reproduce the results and verify their own implementation
- Updating the ITU-T Rec. P.910 text to incorporate the new calculation functions

Since ITU-T Rec. P.910 is a normative document, the updated text was be submitted to ITU-T Study Group 12 for approval and subsequently published in the ITU-T Rec. P.910 document version 07/2022.

### Contributors

Code contributors:

- Werner Robitza
- Lukas Krasula
- Cosmin Stejerean

Many others have contributed to the discussion and updating of the ITU-T document. Thank you to all of them!

### Acknowledgements

If you use this software in your research, please include link to this repository.

### Related Projects

- [TelecommunicationTelemediaAssessment/SITI](https://github.com/Telecommunication-Telemedia-Assessment/SITI): Legacy calculations of OpenCV and Python version of SI/TI, values may not necessarily correspond.
- [NabajeetBarman/SI-TI](https://github.com/NabajeetBarman/SI-TI): MATLAB version of SI/TI calculation, values verified against this repository.

### License

MIT License

siti_tools, Copyright (c) 2021-2025 Werner Robitza, Lukas Krasula, Cosmin Stejerean

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

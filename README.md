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
    - [Usage for > 8-bit Content](#usage-for--8-bit-content)
    - [Full vs. Limited Range](#full-vs-limited-range)
    - [HDR Usage](#hdr-usage)
  - [Detailed Options](#detailed-options)
  - [Output](#output)
  - [API Usage](#api-usage)
- [Testing](#testing)
- [About](#about)
  - [What is SI/TI?](#what-is-siti)
    - [Spatial Information](#spatial-information)
    - [Temporal information](#temporal-information)
  - [What is the purpose of this activity?](#what-is-the-purpose-of-this-activity)
  - [Contributors](#contributors)
  - [Acknowledgements](#acknowledgements)
  - [Related Projects](#related-projects)
  - [License](#license)

## Requirements

- Python 3.8 or higher
- FFmpeg 4.x libraries (to run `pyav`) — this does not work yet with FFmpeg 5.x, see https://github.com/PyAV-Org/PyAV/issues/817

Under Ubuntu, to get ffmpeg libraries:

    sudo apt update -qq && \
    sudo apt install \
      libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
      libavfilter-dev libswscale-dev libavresample-dev

Under macOS, it is recommended to install ffmpeg via [Homebrew](https://brew.sh):

    brew install ffmpeg@4
    export PKG_CONFIG_PATH="/opt/homebrew/opt/ffmpeg@4/lib/pkgconfig"

## Installation

Clone this repository and then:

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

This works for 8-bit standard dynamic range (SDR) content, which will apply to most input files. However, this tool does not automatically handle input that is not 8-bit SDR content. For more info on that, see below.

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

The tool will output a valid JSON object on `stdout`, with SI and TI scores contained in an array. Note that the first frame has no TI value by definition, so a file with two frames would produce the following output:

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

The following info is given about SI / TI in ITU-T Recommendation P.910 ("Subjective video quality assessment methods for multimedia applications"):

#### Spatial Information

> The spatial perceptual information (SI) is based on the Sobel filter. Each video frame (luminance plane) at time n (Fn) is first filtered with the Sobel filter [Sobel(Fn)]. The standard deviation over the pixels (stdspace) in each Sobel-filtered frame is then computed. This operation is repeated for each frame in the video sequence and results in a time series of spatial information of the scene. The maximum value in the time series (maxtime) is chosen to represent the spatial information content of the scene. This process can be represented in equation form as:

> ![](http://i.imgur.com/zRXcVJO.png)

#### Temporal information

> The temporal perceptual information (TI) is based upon the motion difference feature, Mn(i, j), which is the difference between the pixel values (of the luminance plane) at the same location in space but at successive times or frames. Mn(i, j) as a function of time (n) is defined as:

> ![](http://i.imgur.com/MRsJtdT.png)

> here Fn(i, j) is the pixel at the ith row and jth column of nth frame in time.
The measure of temporal information (TI) is computed as the maximum over time (maxtime) of the standard deviation over space (stdspace) of Mn(i, j) over all i and j.

> <img src="https://i.imgur.com/XAnKWJw.png" height="19">

> More motion in adjacent frames will result in higher values of TI

### What is the purpose of this activity?

The [No-Reference Metrics (NORM)](https://www.its.bldrdoc.gov/vqeg/projects/no-reference-metrics-norm.aspx) working group of the [Video Quality Expert Group (VQEG)](https://www.its.bldrdoc.gov/vqeg/vqeg-home.aspx) is currently investigating the Spatial Information (SI) and Temporal Information (TI) indicators defined in ITU-T Rec. P.910.

SI and TI have been frequently used by the community to classify sets of video sequences or video databases, primarily for checking that the used material spans an appropriate range of spatiotemporal complexity before further processing the sequences (e.g., encoding them, presenting them to subjects). Since they are easy and quick to calculate, SI/TI are still very relevant today.

VQEG has identified several limitations with the current definition of SI/TI, including the following:

- It is not specified how to handle video with limited (16-235) vs. full range (0-255).
- The applicable range of input bit depths (bits per channel) is not specified. This means that it is unclear how to handle content with different bit depths, in particular when comparing sequences of varying bit depth.
- It is undefined how to handle high dynamic range (HDR) content, where the luminance information might be encoded differently compared to standard dynamic range (SDR).

The overall aims of this activity are the following:

- Providing an updated set of calculation functions for SI and TI that cover limited/full range content, higher bit depths, and HDR sequences
- Providing a set of test sequences and expected values (i.e., test vectors) in order to allow others to reproduce the results and verify their own implementation
- Updating the ITU-T Rec. P.910 text to incorporate the new calculation functions

### Contributors

Code contributors:

- Werner Robitza
- Lukas Krasula

### Acknowledgements

If you use this software in your research, please include link to this repository.

### Related Projects

- [TelecommunicationTelemediaAssessment/SITI](https://github.com/Telecommunication-Telemedia-Assessment/SITI): Legacy calculations of OpenCV and Python version of SI/TI, values may not necessarily correspond.
- [NabajeetBarman/SI-TI](https://github.com/NabajeetBarman/SI-TI): MATLAB version of SI/TI calculation, values verified against this repository.

### License

MIT License

siti_tools, Copyright (c) 2021-2022 Werner Robitza, Lukas Krasula

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

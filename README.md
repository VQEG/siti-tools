# siti-tools

[![Python package](https://github.com/Telecommunication-Telemedia-Assessment/siti-tools/actions/workflows/python-package.yml/badge.svg)](https://github.com/Telecommunication-Telemedia-Assessment/siti-tools/actions/workflows/python-package.yml)

SI/TI calculation tools.

Calculate spatial information (SI) and temporal information (TI) according to ITU-T P.910.

**⚠️ Note: This is the stable branch of the project. For the ongoing VQEG activity related to improving SI/TI, see [the `siti2020` branch](https://github.com/Telecommunication-Telemedia-Assessment/siti-tools/tree/siti2020)**.

Contents:

- [siti-tools](#siti-tools)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [What is SI/TI?](#what-is-siti)
    - [Spatial Information](#spatial-information)
    - [Temporal information](#temporal-information)
  - [Command Line Usage](#command-line-usage)
  - [API Usage](#api-usage)
    - [Combined Calculation](#combined-calculation)
    - [Individual Calculation](#individual-calculation)
  - [Documentation](#documentation)
  - [Acknowledgements](#acknowledgements)
  - [Related Projects](#related-projects)
  - [Testing](#testing)
  - [License](#license)

## Requirements

- Python 3.7 or higher
- FFmpeg libraries (to run `pyav`)

Under Ubuntu, to get ffmpeg libraries:

    sudo apt update -qq && \
    sudo apt install \
      libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
      libavfilter-dev libswscale-dev libavresample-dev

Under macOS, it is recommended to install ffmpeg via [Homebrew](https://brew.sh):

    brew install ffmpeg

## Installation

Run:

    pip3 install --user siti-tools

Alternatively, clone this repository and then:

    pip3 install --user .

## What is SI/TI?

The following info is given about SI / TI in ITU-T Recommendation P.910 ("Subjective video quality assessment methods for multimedia applications"):

### Spatial Information

> The spatial perceptual information (SI) is based on the Sobel filter. Each video frame (luminance plane) at time n (Fn) is first filtered with the Sobel filter [Sobel(Fn)]. The standard deviation over the pixels (stdspace) in each Sobel-filtered frame is then computed. This operation is repeated for each frame in the video sequence and results in a time series of spatial information of the scene. The maximum value in the time series (maxtime) is chosen to represent the spatial information content of the scene. This process can be represented in equation form as:

> ![](http://i.imgur.com/zRXcVJO.png)

### Temporal information

> The temporal perceptual information (TI) is based upon the motion difference feature, Mn(i, j), which is the difference between the pixel values (of the luminance plane) at the same location in space but at successive times or frames. Mn(i, j) as a function of time (n) is defined as:

> ![](http://i.imgur.com/MRsJtdT.png)

> here Fn(i, j) is the pixel at the ith row and jth column of nth frame in time.
The measure of temporal information (TI) is computed as the maximum over time (maxtime) of the standard deviation over space (stdspace) of Mn(i, j) over all i and j.

> <img src="https://i.imgur.com/XAnKWJw.png" height="19">

> More motion in adjacent frames will result in higher values of TI

## Command Line Usage

Run `siti-tools -h` for a list of command line options:

```
usage: siti-tools [-h] [-s SETTINGS] [-n NUM_FRAMES] [-v] [-c {pq,pu21}] [-m {sdr,hdr10,hlg}]
                  [-b {8,10,12}] [-r {limited,full}] [-e {bt1886,inv_srgb}] [-g GAMMA]
                  [--l-max L_MAX] [--l-min L_MIN]
                  [--pu21-mode {banding,banding_glare,peaks,peaks_glare}]
                  input

optional arguments:
  -h, --help            show this help message and exit

general:
  input                 Input file, can be Y4M or file in FFmpeg-readable container
  -s SETTINGS, --settings SETTINGS
                        Load settings from previous JSON results file instead of using CLI args
  -n NUM_FRAMES, --num-frames NUM_FRAMES
                        Number of frames to calculate, must be >= 2 (default: unlimited)
  -v, --verbose
  -c {pq,pu21}, --calculation-domain {pq,pu21}
                        Select calculation domain (default: pq)
  -m {sdr,hdr10,hlg}, --hdr-mode {sdr,hdr10,hlg}
                        Select HDR mode (default: sdr)
  -b {8,10,12}, --bit-depth {8,10,12}
                        Select bit depth (default: 8)
  -r {limited,full}, --color-range {limited,full}
                        Specify limited or full range (default: limited)

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

## API Usage

The tools expose the calculation functions via an API.

See the `test/generate_values.py` file for an example of how to use those.

## Documentation

To read the API documentation, head to https://telecommunication-telemedia-assessment.github.io/siti-tools/.

## Acknowledgements

If you use this software in your research, please include link to this repository.

## Related Projects

- [TelecommunicationTelemediaAssessment/SITI](https://github.com/Telecommunication-Telemedia-Assessment/SITI): Legacy calculations of OpenCV and Python version of SI/TI, values may not necessarily correspond.
- [NabajeetBarman/SI-TI](https://github.com/NabajeetBarman/SI-TI): MATLAB version of SI/TI calculation, values verified against this repository.

## Testing

This repo provides a set of test sequences with expected output values that you can verify against.

Install `pytest`:

```
pip3 install -r requirements.dev.txt
```

Generate the sequences:

```bash
cd test && ./generate_ffmpeg_sources.sh && cd -
```

Then run:

```bash
python3 -m pytest test/test.py
```

## Contributors

- Werner Robitza
- Lukas Krasula

## License

MIT License

siti_tools, Copyright (c) 2021 Werner Robitza

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

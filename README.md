# siti-tools

SI/TI calculation tools.

Contents:

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Acknowledgements](#acknowledgements)
- [Testing](#testing)
- [License](#license)

## Requirements

- Python 3.5 or higher
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

## Usage

The tools expose the following:

- two main functions to calculate SI and TI given an array of frame data (`si` and `ti`)
- a helper function to calculate SI and TI together (`calculate_si_ti`)
- helper functions for reading files (`read_container`, `read_file`)

### Combined Calculation

In the simplest case, run:

```python
from siti_tools.siti import calculate_si_ti

si_values, ti_values, frame_count = calculate_si_ti("/path/to/file.y4m")
```

You can then access the raw values in the individual variables.

⚠️ The first TI value will always be `None`, since it is not defined.

### Individual Calculation

You can also manually calculate the values.

When calculating TI, make sure to compare against the previous frame data:

```python
from siti_tools.file import read_container
from siti_tools.siti import si, ti

previous_frame_data = None
for frame in read_container("/path/to/file.y4m"):
    si_value = si(frame)
    ti_value = ti(frame, previous_frame_data)
    previous_frame_data = frame
```

The `read_container` function returns each frame individually and the loop will exit once it's done.

## Documentation

To read the API documentation, head to https://telecommunication-telemedia-assessment.github.io/siti_tools.

## Acknowledgements

If you use this software in your research, please include link to this repository.

## Testing

Install `pytest`:

```
pip3 install -r requirements.dev.txt
```

Then run:

```bash
python3 -m pytest test/test.py
```

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

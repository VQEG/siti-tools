## [0.4.1] - 2025-10-28

### Bug Fixes

- Fix: dynamic versioning


### Miscellaneous Tasks

- Ci: fix ffmpeg installation

- Ci: increase thresholds for tests

- Chore: bump version to 0.4.1

## [0.4.0] - 2025-10-28

### Bug Fixes

- Fix limited range normalization (#26)

  * normalize to limited range in the 0-1 conversion to fix 10bit normalization differences
  * fix generate ground truth script to run on case insensitive filesystems like macOS, and also account for hdr10
  * update ground truth files
  * increase precision of tests

- Fix: do not imply verbose on showing histogram


### Features

- Feat: provide an --output-file option


### Miscellaneous Tasks

- Chore: move to uv

- Chore: reformat with ruff, update CI

- Chore: bump version to 0.4.0


### Other

- Upgrade dependencies (#24)

  * upgrade dependencies

  * update github workflow to use python 3.10+

  * bump versions for actions

- Add @cosmin, update authors

- Bump python version

- Unify handling of legacy mode and fix rounding issues (#27)

## [0.3.0] - 2024-08-01

### Miscellaneous Tasks

- Chore: update dependencies


### Other

- Fix the implementation of the HLG EOTF function (#23)

  * Fix the implementation of the HLG EOTF function

  * Fix the tests for HLG

---------

Co-authored-by: Lukas <L.Krasula@gmail.com>

- Bump version to 0.3.0

## [0.2.3] - 2023-12-18

### Bug Fixes

- Fix ffmpeg libs

- Fix README installation instructions


### Other

- Update readme, addresses #17

- Fix issue #20 (#21)

  * Remove `-c:v copy` from the FFmpeg command putting YUV content in a Y4M container.

Mention that `-strict -1` is necessary fot 10-bit pixel formats.

  * Make sure the example for 10-bit pixel format actually uses a 10-bit pixel format

- Update readme

- Bump dependencies

- Update dependencies to include release deps

- Bump version to 0.2.3.

## [0.2.2] - 2023-06-27

### Other

- Error on unsupported frame formats

- Add utility for converting JSON output to CSV

- Add version support to CLI

- Explain usage with YUV files

- Update test decode function

- Update dependencies

- Bump version to 0.2.2

## [0.2.1] - 2022-05-13

### Bug Fixes

- Fix link in setup.py

- Fix console script installation


### Other

- Update README

- Bump version to 0.2.1.

## [0.2.0] - 2022-05-03

### Bug Fixes

- Fix test functions

- use JSON for testing the complex class functions
- fall back to one video for testing the simple functions
- prepare using other videos for testing

- Fixes for 10bpp reading, fixes #12

- Fix unit tests

- Fix formula for EOTF output

- Fix issue with CSV output

- Fix call of OETF, fix tests

- Fix logs

- Fix broken link

- Fix CI setup (#14)


### Other

- Update README links

- Implement first conversion functions

- Implementation of eotf_1886, eotf_inv_srgb, eotf_hlg, and oetf_pq

- Update LICENSE and README

- Add new class-based calculation and results

add more CLI flags

rework classes

- Convert to 0-1 range

This converts values into 0-1 for EOTF/OETF handling, and then scales everything
up to 0-255 again for output, regardless of original bit depth.

- Allow reusing settings from previous run, fixes #10

- Add CLI documentation and entry point

- Update test suite

- Remove import

- Update requirements

- Add note on input values

- Simplify test functions

- Add oetf_pu21

- Add typing support for PU21

- Remove comment

- Add options to select PU21

- Limit download size of test videos

- Update dev requirements

- Remove unused import

- Print more info during tests

- Update test functions

- Update test set, fix reading function for Y4M

- Update requirements

- Update README and docs

- Add further test content

- Add logging and fix error with l_min/l_max conversion

- Add CSV output functionality

- Add progress bar/iterator

- Add histogram plots

- Update README

- Make logger global

- Add type casts for type checks

- Remove superfluous scaling for PU21

- Update for newer ffmpeg, update pip

- Add option for total frame count in tqdm bar

- Update README

- Format code

- Add legacy mode

- Improve logs

- Type error

- Add poetry environment

- Update release script

- Update README.md

- Add profiling test

- Improve docs and tests

- ITU-T --> ITU-R

- Code formatting and note

- Minor code style

- Update README links

- Merge branch 'siti2020'

- CI: support only Python 3.8 and higher

- Check for pypandoc on release

- Bump version to 0.2.0.

## [0.1.3] - 2022-03-14

### Other

- Update docs

- Link to development branch

- Add method to specify full range in read_container

- Bump version to 0.1.3.

## [0.1.2] - 2021-05-14

### Bug Fixes

- Fix link


### Other

- Output frame data as integers

- Update README.md

- Update README.md

- Add documentation for method

- Bump version to 0.1.2

## [0.1.1] - 2021-05-13

### Other

- Add new test video, improve test harness

- Add warning for full range passed to limited range function, fixes #2

- Bump version to 0.1.1

## [0.1.0] - 2021-03-08

### Bug Fixes

- Fix flake8 errors


### Other

- Add GitHub Actions CI (#1)

- Bump Python support

- Add status badge

- Bump version to 0.1.0.

## [0.0.2] - 2021-03-08

### Bug Fixes

- Fix setup.py


### Other

- Add CHANGELOG

- Bump version to 0.0.2.

## [0.0.1] - 2021-03-08

### Other

- Initial commit

- Initial commit

- Improve README


# Changelog


## v0.2.3 (2023-12-18)

* Update dependencies to include release deps.

* Bump dependencies.

* Update readme.

* Fix issue #20 (#21)

  * Remove `-c:v copy` from the FFmpeg command putting YUV content in a Y4M container.

  Mention that `-strict -1` is necessary fot 10-bit pixel formats.

  * Make sure the example for 10-bit pixel format actually uses a 10-bit pixel format

* Fix README installation instructions.

* Update readme, addresses #17.

* Fix ffmpeg libs.


## v0.2.2 (2023-06-27)

* Update dependencies.

* Update test decode function.

* Explain usage with YUV files.

* Add version support to CLI.

* Add utility for converting JSON output to CSV.

* Error on unsupported frame formats.


## v0.2.1 (2022-05-13)

* Fix console script installation.

* Fix link in setup.py.

* Update README.


## v0.2.0 (2022-05-03)

* Check for pypandoc on release.

* Fix CI setup (#14)

* CI: support only Python 3.8 and higher.

* Fix broken link.

* Merge branch 'siti2020'

* Update README links.

* Minor code style.

* Code formatting and note.

* ITU-T --> ITU-R.

* Improve docs and tests.

* Add profiling test.

* Update README.md.

* Update release script.

* Add poetry environment.

* Type error.

* Improve logs.

* Fix logs.

* Add legacy mode.

* Format code.

* Update README.

* Add option for total frame count in tqdm bar.

* Update for newer ffmpeg, update pip.

* Fix call of OETF, fix tests.

* Remove superfluous scaling for PU21.

* Fix issue with CSV output.

* Add type casts for type checks.

* Make logger global.

* Update README.

* Add histogram plots.

* Fix formula for EOTF output.

* Add progress bar/iterator.

* Add CSV output functionality.

* Add logging and fix error with l_min/l_max conversion.

* Add further test content.

* Fix unit tests.

* Update README and docs.

* Fixes for 10bpp reading, fixes #12.

* Update requirements.

* Update test set, fix reading function for Y4M.

* Update test functions.

* Print more info during tests.

* Remove unused import.

* Update dev requirements.

* Fix test functions.

  - use JSON for testing the complex class functions
  - fall back to one video for testing the simple functions
  - prepare using other videos for testing

* Limit download size of test videos.

* Add options to select PU21.

* Remove comment.

* Add typing support for PU21.

* Add oetf_pu21.

* Simplify test functions.

* Add note on input values.

* Update requirements.

* Remove import.

* Update test suite.

* Add CLI documentation and entry point.

* Allow reusing settings from previous run, fixes #10.

* Convert to 0-1 range.

  This converts values into 0-1 for EOTF/OETF handling, and then scales everything
  up to 0-255 again for output, regardless of original bit depth.

* Add new class-based calculation and results.

  add more CLI flags

  rework classes

* Update LICENSE and README.

* Implementation of eotf_1886, eotf_inv_srgb, eotf_hlg, and oetf_pq.

* Implement first conversion functions.

* Update README links.


## v0.1.3 (2022-03-14)

* Add method to specify full range in read_container.

* Link to development branch.

* Update docs.


## v0.1.2 (2021-05-14)

* Add documentation for method.

* Fix link.

* Update README.md.

* Update README.md.

* Output frame data as integers.


## v0.1.1 (2021-05-13)

* Add warning for full range passed to limited range function, fixes #2.

* Add new test video, improve test harness.


## v0.1.0 (2021-03-08)

* Add status badge.

* Bump Python support.

* Add GitHub Actions CI (#1)

* Fix flake8 errors.


## v0.0.2 (2021-03-08)

* Fix setup.py.

* Add CHANGELOG.


## v0.0.1 (2021-03-08)

* Improve README.

* Initial commit.

* Initial commit.



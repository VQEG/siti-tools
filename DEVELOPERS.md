# Developer Guides

## Testing

This repo provides a set of test sequences with expected output values that you can verify against.

First, sync the development dependencies:

```bash
uv sync
```

Generate the sequences:

```bash
cd test && ./generate_ffmpeg_sources.sh && cd -
```

Then run:

```bash
uv run pytest test/test.py -n auto
```

The `-n auto` flag distributes the test to all cores. Remove it if you want to capture stdout with `-s`.

## Making Releases

Use https://github.com/slhck/dotfiles/blob/master/scripts/release-python.sh to create a release.

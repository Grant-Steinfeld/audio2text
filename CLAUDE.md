# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[all]"   # includes nltk for analyze subcommand
# or just core deps:
pip install -e .
```

The first `whisper` transcription will download the model weights (~140 MB for `base`, up to 2.9 GB for `large`).

## Commands

```bash
# Transcribe an audio file
audio2text transcribe path/to/audio.mp3
audio2text transcribe path/to/audio.mp3 --model medium --output transcript.txt

# Analyze a transcript with NLTK
audio2text analyze transcript.txt
audio2text analyze transcript.txt --concordance word --lines 10 --output report.txt

# Legacy shim scripts (delegate to the package)
python src/transcribe.py path/to/audio.mp3
python src/analyze.py transcript.txt
```

## Architecture

```
audio2text/          # installable package
  __init__.py        # re-exports: transcribe, analyze_transcript, show_concordance
  transcribe.py      # transcribe(audio_file, model) → str  (wraps openai-whisper)
  analyze.py         # analyze_transcript(text) → dict, show_concordance(text, word)
  cli.py             # argparse CLI with two subcommands: transcribe | analyze
src/                 # thin shims for backward-compat; just call audio2text.cli:main
```

**Two-subcommand CLI** (`audio2text.cli:main`):
- `transcribe` — validates file existence and extension, loads Whisper model, returns plain text
- `analyze` — requires `nltk` optional dep; auto-downloads `punkt_tab` and `stopwords` on first run

**Supported audio formats** (defined in `transcribe.py:SUPPORTED_FORMATS`): `.mp3 .wav .m4a .flac .ogg .opus .aac`

**Whisper model sizes** (`ModelSize` Literal type): `tiny | base | small | medium | large` — `base` is the default.

`nltk` is an optional dependency (`pip install ".[analyze]"` or `".[all]"`). `analyze.py` gracefully degrades with an `ImportError` message if it's missing.

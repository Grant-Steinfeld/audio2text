# Audio to Text Transcription

A Python project that converts audio files to text using OpenAI's Whisper model. Runs entirely locally without requiring API keys.

## Setup

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install directly:
```bash
pip install openai-whisper
```

## Usage

### Basic Usage
```bash
python src/transcribe.py path/to/audio.mp3
```

### Save Output to File
```bash
python src/transcribe.py path/to/audio.mp3 --output transcript.txt
```

### Use Different Model Size
```bash
python src/transcribe.py path/to/audio.mp3 --model small
```

Available models (larger = more accurate, slower):
- `tiny` - fastest, lowest accuracy
- `base` - good balance (default)
- `small` - better accuracy
- `medium` - high accuracy
- `large` - best accuracy, slowest

### Full Example
```bash
python src/transcribe.py ~/Downloads/meeting.mp3 --model medium --output meeting_transcript.txt
```

## Supported Audio Formats
- MP3
- WAV
- M4A
- FLAC
- OGG
- Opus
- AAC

## Notes
- First run will download the model (~1-3 GB depending on model size)
- No internet connection required after model download
- GPU acceleration available if CUDA is installed

## Model Sizes & Requirements
| Model  | Disk Space | Speed | Accuracy |
|--------|-----------|-------|----------|
| tiny   | 139 MB    | ~10x  | Low      |
| base   | 140 MB    | ~1x   | Good     |
| small  | 466 MB    | ~2x   | Better   |
| medium | 1.5 GB    | ~6x   | High     |
| large  | 2.9 GB    | ~25x  | Highest  |

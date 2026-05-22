from pathlib import Path
from typing import Literal

ModelSize = Literal["tiny", "base", "small", "medium", "large"]
SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac"}


def transcribe(audio_file: str, model: ModelSize = "base") -> str:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        audio_file: Path to the audio file.
        model: Whisper model size — tiny/base/small/medium/large.
               Larger models are more accurate but slower.

    Returns:
        Transcribed text as a string.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        ValueError: If the file format is not supported.
    """
    import whisper

    audio_path = Path(audio_file)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    if audio_path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{audio_path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    model_obj = whisper.load_model(model)
    result = model_obj.transcribe(str(audio_path))
    return result["text"]

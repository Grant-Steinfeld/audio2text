import argparse
import sys
from pathlib import Path

from . import transcribe, analyze_transcript, show_concordance


def _cmd_transcribe(args):
    text = transcribe(args.audio_file, model=args.model)
    if args.output:
        Path(args.output).write_text(text)
        print(f"Transcription saved to: {args.output}")
    else:
        print(text)


def _cmd_analyze(args):
    text = Path(args.transcript).read_text()
    analyze_transcript(text, output_file=args.output)
    if args.concordance:
        show_concordance(text, args.concordance, lines=args.lines)


def main():
    parser = argparse.ArgumentParser(
        prog="audio2text",
        description="Convert audio files to text and analyze transcripts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    t = sub.add_parser("transcribe", help="Convert an audio file to text")
    t.add_argument("audio_file", help="Path to audio file (.m4a, .mp3, .wav, …)")
    t.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)",
    )
    t.add_argument("--output", "-o", help="Save transcript to this file")

    a = sub.add_parser("analyze", help="Analyze a transcript file with NLTK")
    a.add_argument("transcript", help="Path to transcript text file")
    a.add_argument("--output", "-o", help="Save analysis report to this file")
    a.add_argument("--concordance", "-c", help="Show concordance for a specific word")
    a.add_argument(
        "--lines", "-l", type=int, default=25, help="Concordance lines to show (default: 25)"
    )

    args = parser.parse_args()

    try:
        if args.command == "transcribe":
            _cmd_transcribe(args)
        elif args.command == "analyze":
            _cmd_analyze(args)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

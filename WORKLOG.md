# audio2text — Working Log

## 2026-05-21

### Context
Revisited the existing `audio2text` project at `/Users/grantsteinfeld/Documents/dev/audio2text`.
Goal: make the audio-to-text converter reusable across projects regardless of language (Python, TypeScript/React, Rust, etc.).

---

### Session: Repackage as installable Python package (Option 3)

Evaluated four approaches for making the converter reusable:

| Option | Approach | Decision |
|--------|----------|----------|
| 1 | MCP Server | Skipped — too much infrastructure for this use case |
| 2 | Anthropic Tool Use | Skipped — requires per-project glue code |
| **3** | **Python package (`pip install -e`)** | **Chosen** |
| 4 | Anthropic Files API | Skipped — incurs API token cost per transcription |

**What was built:**

Created a proper Python package alongside the existing `src/` scripts:

```
audio2text/
├── pyproject.toml          ← pip-installable, defines CLI entry point
├── audio2text/
│   ├── __init__.py         ← public API: transcribe, analyze_transcript, show_concordance
│   ├── transcribe.py       ← core Whisper logic (no CLI concerns)
│   ├── analyze.py          ← NLTK analysis (nltk is an optional dependency)
│   └── cli.py              ← unified CLI with `transcribe` and `analyze` subcommands
└── src/
    ├── transcribe.py       ← updated to thin shim (delegates to package)
    └── analyze.py          ← updated to thin shim (delegates to package)
```

**Public API:**
```python
from audio2text import transcribe, analyze_transcript, show_concordance

text = transcribe("recording.m4a")
text = transcribe("recording.m4a", model="small")
stats = analyze_transcript(text)
```

**CLI entry point (registered via pyproject.toml):**
```bash
audio2text transcribe recording.m4a --model small --output out.txt
audio2text analyze out.txt --concordance word
```

**To use from any other Python project:**
```bash
.venv/bin/pip install -e /Users/grantsteinfeld/Documents/dev/audio2text
```

Installed into existing venv with `pip install -e .` — verified imports and CLI work.

---

### Session: Global Claude Code skill `/transcribe`

Motivation: TypeScript/React and Rust projects can't `import` a Python package.
A global Claude Code skill works at the shell level — language-agnostic.

Created `~/.claude/commands/transcribe.md` — available as `/transcribe` in any Claude Code session.

**Usage:**
```
/transcribe path/to/recording.m4a
/transcribe path/to/recording.m4a --model small
```

The skill resolves the path relative to the current working directory, runs the transcription via the audio2text venv, displays the transcript, then offers to save it, analyze it, or process it further (translate, summarize, extract vocabulary).

---

### Files changed this session

| File | Status |
|------|--------|
| `audio2text/pyproject.toml` | Created |
| `audio2text/audio2text/__init__.py` | Created |
| `audio2text/audio2text/transcribe.py` | Created |
| `audio2text/audio2text/analyze.py` | Created |
| `audio2text/audio2text/cli.py` | Created |
| `audio2text/src/transcribe.py` | Updated (shim) |
| `audio2text/src/analyze.py` | Updated (shim) |
| `~/.claude/commands/transcribe.md` | Created (global skill) |
| `audio2text/WORKLOG.md` | Created |

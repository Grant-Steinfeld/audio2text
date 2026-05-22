# audio2text — Architecture

## What This Is

`audio2text` is a locally-running speech-to-text tool. Its primary role is to serve as the backend for a **Claude Code skill** — when you type `/transcribe` in Claude Code, Claude invokes this tool via a Bash call to transcribe audio on your own machine, with no cloud API or internet connection required after setup.

---

## 1. The `/transcribe` Claude Code Skill

### What a skill is

A Claude Code skill is a Markdown file stored in `~/.claude/commands/<name>.md`. When a user types `/transcribe` in Claude Code, the harness loads that file and injects its content as instructions for the current turn. The skill is the glue between a conversational prompt and a concrete CLI tool — it tells Claude exactly what command to run, how to parse arguments, and what to do with the output.

### How the skill wraps the Python tool

```mermaid
flowchart LR
    subgraph Claude["Claude Code (harness)"]
        Slash["/transcribe audio.mp3\n--model small"]
        Skill["~/.claude/commands/transcribe.md\n(skill definition)"]
        LLM["Claude LLM\n(reads skill, interprets args,\ndecides Bash command)"]
    end

    subgraph Shell["Local machine"]
        Venv["venv/bin/audio2text\n(package entry point)"]
        CLI["audio2text/cli.py"]
        T["transcribe.py"]
        W["OpenAI Whisper\n(local ASR model)"]
    end

    Slash --> Skill
    Skill -- "injected as instructions" --> LLM
    LLM -- "Bash tool call" --> Venv
    Venv --> CLI
    CLI --> T
    T --> W
    W -- "transcript text" --> T
    T -- "return str" --> CLI
    CLI -- "stdout" --> LLM
    LLM -- "displays transcript\noffers next steps" --> User(["User"])
```

### Skill invocation sequence

```mermaid
sequenceDiagram
    participant U as User
    participant H as Claude Code harness
    participant S as transcribe.md (skill)
    participant L as Claude LLM
    participant B as Bash tool
    participant P as audio2text CLI

    U->>H: /transcribe recording.m4a --model small
    H->>S: load skill file, inject $ARGUMENTS
    S-->>L: full instructions + parsed arguments
    L->>B: venv/bin/audio2text transcribe recording.m4a --model small
    B->>P: subprocess exec
    P-->>B: transcript text on stdout
    B-->>L: captured stdout
    L-->>U: display transcript
    L-->>U: offer: save to file / analyze / summarize / translate?
```

### The skill file (`~/.claude/commands/transcribe.md`)

| Part | Purpose |
|---|---|
| **Description line** | One-sentence summary shown in `/help` |
| **`$ARGUMENTS` placeholder** | The harness substitutes the text typed after `/transcribe` here |
| **Steps** | Numbered instructions Claude follows: parse args → resolve path → run the exact `audio2text` CLI command → display output → offer follow-up actions |

The skill hard-codes the venv path (`venv/bin/audio2text transcribe …`) so it always uses the project's installed package rather than any system-wide binary.

---

## 2. Local Python Package Architecture

The `audio2text` Python package is the tool the skill calls. It has two responsibilities: transcription and analysis.

### Package overview

```mermaid
flowchart TD
    subgraph EntryPoints["Entry Points"]
        CLI["audio2text CLI\naudio2text/cli.py"]
        ShimT["src/transcribe.py\n(legacy shim)"]
        ShimA["src/analyze.py\n(legacy shim)"]
        PkgAPI["Python import\nfrom audio2text import …"]
    end

    subgraph Package["audio2text package"]
        Init["__init__.py\nre-exports public API"]

        subgraph Transcribe["transcribe.py"]
            T_Validate["Validate path & extension"]
            T_Device["Auto-select device\nMPS › CUDA › CPU"]
            T_Load["whisper.load_model(size, device)"]
            T_Run["model.transcribe(audio)"]
            T_Return["return text str"]
        end

        subgraph Analyze["analyze.py"]
            A_Check["NLTK available?\n(optional dep)"]
            A_Stats["Tokenize & compute stats\nsentences · words · freq dist\nlexical diversity"]
            A_Report["Print / save report"]
            A_Concordance["show_concordance()\nNLTK Text.concordance()"]
        end
    end

    subgraph External["External Libraries"]
        Whisper["openai-whisper\n(Whisper ASR model —\nweights downloaded on first run)"]
        NLTK["nltk\n(optional — pip install .[analyze])"]
    end

    ShimT & ShimA -- "delegate to" --> CLI
    CLI & PkgAPI --> Init
    Init --> Transcribe & Analyze

    T_Validate --> T_Device --> T_Load --> T_Run --> T_Return
    T_Load -. "downloads weights\n140 MB – 2.9 GB" .-> Whisper
    Whisper --> T_Run

    A_Check -- "present" --> A_Stats --> A_Report --> A_Concordance
    NLTK --> A_Stats & A_Concordance
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing, subcommand routing, error handling |
| `transcribe.py` | File validation, Whisper model loading & inference |
| `analyze.py` | NLTK dependency guard, tokenization, stats, concordance |
| `__init__.py` | Public API surface — `transcribe`, `analyze_transcript`, `show_concordance` |
| `src/*.py` | Backward-compatible shims — delegate directly to `cli.main()` |

---

## 3. How Whisper Works — Is It an LLM?

**No — Whisper is not a large language model.** It is an *automatic speech recognition* (ASR) model. Both share the Transformer architecture, but they are trained on fundamentally different inputs and for different tasks.

### LLM vs. Whisper

| | Large Language Model (e.g. Claude) | Whisper (ASR model) |
|---|---|---|
| **Input** | Text tokens | Raw audio waveform |
| **Trained on** | Vast text corpora | 680,000 hours of labeled audio |
| **Task** | Predict next text token | Convert speech → text |
| **Output** | Text tokens | Text transcript |

### Whisper's internal pipeline

```mermaid
flowchart LR
    Audio["Audio file\n.mp3 / .m4a / .wav …"]
    Mel["Mel Spectrogram\n80-channel frequency\nvs. time representation"]
    Enc["Transformer Encoder\nextracts acoustic features\nfrom spectrogram frames"]
    Dec["Transformer Decoder\nauto-regressively generates\ntext tokens"]
    Text["Transcript text"]

    Audio -- "FFmpeg decode\n→ 16 kHz mono PCM" --> Mel
    Mel -- "convolutional\nfeature extraction" --> Enc
    Enc -- "encoded\naudio features" --> Dec
    Dec -- "token by token" --> Text
```

1. **Audio decoding** — FFmpeg converts any supported format to a 16 kHz mono waveform.
2. **Mel spectrogram** — the waveform is transformed into a 2D representation of frequency energy over time (like a visual fingerprint of the sound). This is what the model "sees" — not raw audio samples.
3. **Encoder** — a stack of Transformer encoder layers reads the spectrogram and produces a dense representation of the acoustic content.
4. **Decoder** — a Transformer decoder generates the transcript one token at a time, attending to the encoder output (cross-attention). This is the same mechanism as a text-based seq2seq model, just conditioned on sound instead of text.

### Why this matters for usage

- **No internet needed** — the model weights are downloaded once and run entirely on your CPU or GPU.
- **Speed vs. accuracy tradeoff** — larger models (`medium`, `large`) have more encoder/decoder layers and produce better transcripts but take longer. `base` is a practical default for most recordings.
- **Multilingual** — Whisper was trained on 98 languages; it can auto-detect language or be directed with `--language`.

### GPU acceleration on Apple Silicon

Whisper out-of-the-box only auto-selects CUDA (NVIDIA). On a Mac it silently falls back to CPU — even on an M-series chip with a capable GPU sitting idle.

`transcribe.py` patches this with explicit device selection:

```mermaid
flowchart LR
    A{"MPS available?\nApple Silicon GPU"}
    B{"CUDA available?\nNVIDIA GPU"}
    C["device = 'mps'"]
    D["device = 'cuda'"]
    E["device = 'cpu'"]

    A -- yes --> C
    A -- no --> B
    B -- yes --> D
    B -- no --> E
    C & D & E --> F["whisper.load_model(size, device=device)"]
```

**Why GPU matters for ASR inference:**

Whisper's encoder and decoder are both Transformer stacks with large matrix multiplications at every layer. These operations map perfectly onto GPU hardware, which can run thousands of them in parallel. On CPU, the same computation is serialised across a handful of cores.

| Device | Who has it | Typical speedup vs. CPU |
|---|---|---|
| CPU | Everyone | 1× (baseline) |
| MPS | Apple Silicon (M1/M2/M3/M4) | ~3–5× |
| CUDA | NVIDIA GPU | ~5–10× |

On this machine (**MacBook Air M4**) you can confirm the active device at runtime:

```python
import torch
device = "mps" if torch.backends.mps.is_available() else \
         "cuda" if torch.cuda.is_available() else "cpu"
print(device)  # → mps
```

# audio2text — Architecture

## How It Works

`audio2text` is an installable Python package that wraps [OpenAI Whisper](https://github.com/openai/whisper) for local audio transcription and NLTK for transcript analysis. No API keys required — everything runs on your machine.

## Component Flow

```mermaid
flowchart TD
    User(["User / calling code"])

    subgraph EntryPoints["Entry Points"]
        CLI["audio2text CLI\naudio2text/cli.py"]
        ShimT["src/transcribe.py\n(legacy shim)"]
        ShimA["src/analyze.py\n(legacy shim)"]
        PkgAPI["Python import\nfrom audio2text import …"]
    end

    subgraph Package["audio2text package"]
        Init["__init__.py\nre-exports public API"]

        subgraph Transcribe["transcribe.py"]
            T_Validate["Validate path\n& extension"]
            T_Load["whisper.load_model(size)"]
            T_Run["model.transcribe(audio)"]
            T_Return["return text str"]
        end

        subgraph Analyze["analyze.py"]
            A_Check["NLTK available?\n(optional dep)"]
            A_Download["Auto-download\npunkt_tab + stopwords"]
            A_Stats["Tokenize & compute\nsentences, words,\nlexical diversity,\nfreq distribution"]
            A_Report["Print / save report"]
            A_Return["return stats dict"]
            A_Concordance["show_concordance()\nNLTK Text.concordance()"]
        end
    end

    subgraph External["External Libraries"]
        Whisper["openai-whisper\n(Whisper model weights\ndownloaded on first run)"]
        NLTK["nltk\n(optional — install with\npip install .[analyze])"]
    end

    subgraph Output["Output"]
        Stdout["stdout — transcript\nor analysis report"]
        File["file — transcript.txt\nor report.txt"]
    end

    User --> CLI
    User --> PkgAPI
    ShimT -- "delegates to" --> CLI
    ShimA -- "delegates to" --> CLI

    CLI -- "transcribe subcommand" --> Init
    CLI -- "analyze subcommand" --> Init
    PkgAPI --> Init

    Init --> Transcribe
    Init --> Analyze

    T_Validate --> T_Load
    T_Load --> T_Run
    T_Run --> T_Return
    T_Load -. "downloads model\n~140 MB–2.9 GB" .-> Whisper
    Whisper --> T_Run

    A_Check -- "missing" --> A_Download
    A_Download --> NLTK
    A_Check -- "present" --> A_Stats
    A_Stats --> A_Report
    A_Report --> A_Return
    A_Report --> A_Concordance
    NLTK --> A_Stats
    NLTK --> A_Concordance

    T_Return --> Stdout
    T_Return --> File
    A_Return --> Stdout
    A_Return --> File
    A_Concordance --> Stdout
```

## Subcommand Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as cli.py
    participant T as transcribe.py
    participant W as Whisper
    participant A as analyze.py
    participant N as NLTK

    note over U,N: Transcription path
    U->>CLI: audio2text transcribe audio.mp3 --model medium
    CLI->>T: transcribe("audio.mp3", model="medium")
    T->>T: validate path & extension
    T->>W: whisper.load_model("medium")
    W-->>T: model object
    T->>W: model.transcribe("audio.mp3")
    W-->>T: {"text": "…"}
    T-->>CLI: transcript string
    CLI->>U: print or write to file

    note over U,N: Analysis path (requires nltk)
    U->>CLI: audio2text analyze transcript.txt --concordance meeting
    CLI->>A: analyze_transcript(text)
    A->>N: sent_tokenize / word_tokenize / FreqDist
    N-->>A: stats
    A-->>CLI: stats dict + printed report
    CLI->>A: show_concordance(text, "meeting")
    A->>N: Text.concordance("meeting")
    N-->>CLI: printed concordance lines
```

## The `/transcribe` Claude Code Skill

### What a skill is

A Claude Code skill is a Markdown file stored in `~/.claude/commands/<name>.md`. When a user types `/transcribe` in Claude Code, the harness loads that file and injects its content as instructions for the current turn. The skill is the glue between a conversational prompt and a concrete CLI tool — it tells Claude exactly what command to run, how to parse arguments, and what to do with the output.

### How a skill wraps a Python tool

```mermaid
flowchart LR
    subgraph Claude["Claude Code (harness)"]
        Slash["/transcribe audio.mp3\n--model small"]
        Skill["~/.claude/commands/transcribe.md\n(skill definition)"]
        LLM["Claude LLM\n(reads skill, interprets args,\ndecides Bash command)"]
    end

    subgraph Shell["Local shell"]
        Venv["venv/bin/audio2text\n(package entry point)"]
        CLI["audio2text/cli.py\nmain()"]
        T["transcribe.py\ntranscribe()"]
        W["openai-whisper"]
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

### The skill file (`~/.claude/commands/transcribe.md`)

The file has three parts:

| Part | Purpose |
|---|---|
| **Description line** | One-sentence summary shown in `/help` |
| **`$ARGUMENTS` placeholder** | The harness substitutes the text typed after `/transcribe` here |
| **Steps** | Numbered instructions Claude follows: parse args → resolve path → run the exact `audio2text` CLI command → display output → offer follow-up actions |

Because the skill hard-codes the venv path (`venv/bin/audio2text transcribe …`), it always uses the project's installed package rather than any system-wide binary.

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

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing, subcommand routing, error handling |
| `transcribe.py` | File validation, Whisper model loading & inference |
| `analyze.py` | NLTK dependency guard, tokenization, stats, concordance |
| `__init__.py` | Public API surface — `transcribe`, `analyze_transcript`, `show_concordance` |
| `src/*.py` | Backward-compatible shims — delegate directly to `cli.main()` |

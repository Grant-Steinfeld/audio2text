from pathlib import Path

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.probability import FreqDist
    from nltk.text import Text

    for _resource, _path in [("punkt_tab", "tokenizers/punkt_tab"), ("stopwords", "corpora/stopwords")]:
        try:
            nltk.data.find(_path)
        except LookupError:
            nltk.download(_resource, quiet=True)

    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False


def _require_nltk():
    if not _NLTK_AVAILABLE:
        raise ImportError(
            "nltk is required for text analysis. "
            "Install it with: pip install nltk"
        )


def analyze_transcript(text: str, output_file: str = None) -> dict:
    """
    Analyze transcript text using NLTK.

    Returns a dict with keys: sentences, words, unique_words,
    lexical_diversity, most_common, avg_word_length.
    Also prints a formatted report and optionally saves it.
    """
    _require_nltk()

    sentences = sent_tokenize(text)
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words("english"))
    filtered = [w for w in words if w.isalnum() and w not in stop_words]

    total_words = len(words)
    unique_words = len(set(words))
    lexical_diversity = unique_words / total_words if total_words else 0
    freq_dist = FreqDist(filtered)
    most_common = freq_dist.most_common(20)
    word_lengths = [len(w) for w in filtered]
    avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0

    lines = [
        "=" * 70,
        "TRANSCRIPT ANALYSIS",
        "=" * 70,
        "",
        "BASIC STATISTICS",
        "-" * 70,
        f"Total Sentences:            {len(sentences)}",
        f"Total Words:                {total_words}",
        f"Unique Words:               {unique_words}",
        f"Lexical Diversity:          {lexical_diversity:.2%}",
        f"Average Words per Sentence: {total_words / len(sentences):.1f}" if sentences else "",
        "",
        "TOP 20 MOST FREQUENT WORDS (excluding stopwords)",
        "-" * 70,
        *[
            f"{i:2d}. {word:20s} - {freq:4d} occurrences ({freq / total_words * 100:5.2f}%)"
            for i, (word, freq) in enumerate(most_common, 1)
        ],
        "",
        "SAMPLE SENTENCES",
        "-" * 70,
        *[f"{i}. {s.strip()}" for i, s in enumerate(sentences[:5], 1)],
        "",
        "WORD LENGTH ANALYSIS",
        "-" * 70,
        f"Average Word Length: {avg_word_length:.1f} characters",
        f"Longest Word:  {max(filtered, key=len) if filtered else 'N/A'}",
        f"Shortest Word: {min(filtered, key=len) if filtered else 'N/A'}",
    ]

    report = "\n".join(lines)
    print(report)

    if output_file:
        Path(output_file).write_text(report)
        print(f"\nAnalysis saved to: {output_file}")

    return {
        "sentences": len(sentences),
        "words": total_words,
        "unique_words": unique_words,
        "lexical_diversity": lexical_diversity,
        "most_common": most_common,
        "avg_word_length": avg_word_length,
    }


def show_concordance(text: str, word: str, width: int = 79, lines: int = 25):
    """Print concordance lines for a word within the transcript."""
    _require_nltk()

    nltk_text = Text(word_tokenize(text.lower()))
    print(f"\nCONCORDANCE FOR '{word.upper()}'")
    print("-" * 70)
    try:
        nltk_text.concordance(word.lower(), width=width, lines=lines)
    except Exception:
        print(f"Word '{word}' not found in text.")

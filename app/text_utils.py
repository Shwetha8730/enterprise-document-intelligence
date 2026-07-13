import re

def split_sentences(text: str):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    sentences = []
    for line in lines:
        parts = re.split(r"(?<=[.!?])\s+", line)
        for p in parts:
            p = p.strip(" -•\t")
            if len(p) > 2:
                sentences.append(p)
    return sentences


def chunk_text(text: str, sentences_per_chunk: int = 4, overlap: int = 1):
    """Split a document into overlapping passage-level chunks for
    semantic indexing - the standard RAG pattern."""
    sentences = split_sentences(text)
    if not sentences:
        return []

    if len(sentences) <= sentences_per_chunk:
        return [" ".join(sentences)]

    chunks = []
    step = max(1, sentences_per_chunk - overlap)
    i = 0
    while i < len(sentences):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        chunks.append(chunk)
        if i + sentences_per_chunk >= len(sentences):
            break
        i += step
    return chunks
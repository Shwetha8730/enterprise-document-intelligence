import re

def split_sentences(text: str):
    # First split on newlines (resumes/invoices are line-oriented),
    # then further split any long lines on sentence punctuation.
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    sentences = []
    for line in lines:
        parts = re.split(r"(?<=[.!?])\s+", line)
        for p in parts:
            p = p.strip(" -•\t")
            if len(p) > 2:
                sentences.append(p)
    return sentences

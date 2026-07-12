import re
import spacy

_nlp = spacy.load("en_core_web_sm")

INVOICE_NUM_RE = re.compile(r"(?:invoice\s*(?:number|#|no\.?)\s*[:\-]?\s*)([A-Za-z0-9\-]+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")

def extract_metadata(text: str, doc_type: str = None) -> dict:
    doc = _nlp(text)

    entities = {"PERSON": [], "ORG": [], "DATE": [], "MONEY": [], "GPE": []}
    for ent in doc.ents:
        if ent.label_ in entities:
            val = ent.text.strip()
            if val not in entities[ent.label_]:
                entities[ent.label_].append(val)

    metadata = {
        "people": entities["PERSON"],
        "organizations": entities["ORG"],
        "dates": entities["DATE"],
        "amounts": entities["MONEY"],
        "locations": entities["GPE"],
        "emails_found": list(set(EMAIL_RE.findall(text))),
    }

    # Domain-specific extras
    invoice_match = INVOICE_NUM_RE.search(text)
    if invoice_match:
        metadata["invoice_number"] = invoice_match.group(1)

    # Flag required-field completeness by doc type (used by the "completeness checker" agent)
    required_fields = {
        "invoice": ["amounts", "dates", "organizations"],
        "resume": ["people"],
        "contract": ["organizations", "dates"],
        "email": ["emails_found", "dates"],
    }
    if doc_type in required_fields:
        missing = [f for f in required_fields[doc_type] if not metadata.get(f)]
        metadata["missing_fields"] = missing

    return metadata

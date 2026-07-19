import re
import spacy

_nlp = spacy.load("en_core_web_sm")

INVOICE_NUM_RE = re.compile(r"(?:invoice\s*(?:number|#|no\.?)\s*[:\-]?\s*)([A-Za-z0-9\-]+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}")
SKILLS_RE = re.compile(r"skills?\s*[:\-]\s*(.+)",re.IGNORECASE,)
POSITION_RE = re.compile(r"position\s*[:\-]\s*(.+)",re.IGNORECASE,)
SALARY_RE = re.compile(r"(?:salary|annual ctc|ctc)\s*[:\-]?\s*([₹$]?[0-9,\.]+)",re.IGNORECASE,)
JOINING_RE = re.compile(r"joining date\s*[:\-]?\s*(.+)",re.IGNORECASE,)
SUBJECT_RE = re.compile(r"subject\s*[:\-]\s*(.+)",re.IGNORECASE,)

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

    # Invoice Metadata
    invoice_match = INVOICE_NUM_RE.search(text)
    if invoice_match:
        metadata["invoice_number"] = invoice_match.group(1)
    
    if doc_type == "invoice":
        if entities["MONEY"]:
            metadata["total_amount"] = entities["MONEY"][-1]

    # Resume Metadata
    if doc_type == "resume":
        phone = PHONE_RE.search(text)
        if phone:
            metadata["phone"] = phone.group()
        skills = SKILLS_RE.search(text)
        if skills:
            metadata["skills"] = [s.strip()
                for s in skills.group(1).split(",")
            ]

    # Contract Metadata
    if doc_type == "contract":
        position = POSITION_RE.search(text)
        salary = SALARY_RE.search(text)
        joining = JOINING_RE.search(text)

        if position:
            metadata["position"] = position.group(1)

        if salary:
            metadata["salary"] = salary.group(1)

        if joining:
            metadata["joining_date"] = joining.group(1)

    # Email Metadata
    if doc_type == "email":
        subject = SUBJECT_RE.search(text)
        if subject:
            metadata["subject"] = subject.group(1)

    # Spreadsheet Metadata
    if doc_type == "spreadsheet":
       lines = [line.strip() for line in text.splitlines() if line.strip()]
       if lines:
          metadata["column_names"] = lines[0].split()
          metadata["row_count"] = max(0, len(lines) - 1)
          metadata["column_count"] = len(lines[0].split())

    # Presentation Metadata
    if doc_type == "presentation":
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            metadata["title"] = lines[0]
        if len(lines) > 1:
            metadata["topics"] = lines[1:]

    #completeness check 
    required_fields = {
        "invoice": ["amounts", "dates", "organizations"],
        "resume": ["people"],
        "contract": ["organizations", "dates"],
        "email": ["emails_found", "dates"],
        "spreadsheet": ["column_names", "row_count", "column_count"],
        "presentation": ["title", "topics"],
    }
    if doc_type in required_fields:
      missing = [f for f in required_fields[doc_type] if not metadata.get(f)]
      metadata["missing_fields"] = missing

    return metadata

from app.metadata_extractor import extract_metadata

text = """
Invoice Number: INV-3391
Date: July 5, 2026
Bill To: Nexora Technologies Pvt Ltd
Total Due: $4180
Email: accounts@nexora.com
Location: Bangalore
"""

result = extract_metadata(text, "invoice")

print(result)
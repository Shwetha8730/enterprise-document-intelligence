from app.text_utils import split_sentences

text = """
Invoice Number: INV-3391
Bill To: Nexora Technologies

Subtotal: $3800
Tax: $380
Total Due: $4180

Thank you for your business.
"""

print(split_sentences(text))
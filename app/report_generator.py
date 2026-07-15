from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import darkblue
from reportlab.lib.units import inch

from datetime import datetime


def generate_pdf_report(filename, result):

    output_file = "analysis_report.pdf"

    styles = getSampleStyleSheet()

    title = styles["Heading1"]
    title.alignment = TA_CENTER
    title.textColor = darkblue

    heading = styles["Heading2"]
    normal = styles["BodyText"]

    doc = SimpleDocTemplate(output_file)

    story = []

    story.append(Paragraph("Enterprise AI Document Intelligence Platform", title))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("<b>Analysis Report</b>", heading))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"<b>Document:</b> {filename}", normal))
    story.append(Spacer(1, 0.15 * inch))

    classification = result["classification"]

    story.append(
        Paragraph(
            f"<b>Predicted Type:</b> {classification['predicted_type']}",
            normal,
        )
    )

    story.append(
        Paragraph(
            f"<b>Confidence:</b> {classification['confidence']*100:.2f}%",
            normal,
        )
    )

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Extracted Metadata</b>", heading))

    metadata = result["metadata"]

    for key, value in metadata.items():

        if value:

            if isinstance(value, list):
                value = ", ".join(value)

            story.append(
                Paragraph(
                    f"<b>{key.replace('_',' ').title()}:</b> {value}",
                    normal,
                )
            )

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Summary</b>", heading))

    story.append(Paragraph(result["summary"], normal))

    story.append(Spacer(1, 0.2 * inch))

    completeness = result["completeness_check"]

    story.append(Paragraph("<b>Completeness Check</b>", heading))
    story.append(Paragraph(completeness["recommendation"], normal))

    story.append(Spacer(1, 0.4 * inch))

    story.append(
        Paragraph(
            f"Generated on: {datetime.now().strftime('%d %B %Y %I:%M %p')}",
            normal,
        )
    )

    doc.build(story)

    return output_file
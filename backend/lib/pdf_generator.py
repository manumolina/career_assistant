import io
import re

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


def generate_pdf(
    cv_analysis: str,
    job_offer_analysis: str,
    strengths: list[str],
    weaknesses: list[str],
    recommendation: str,
    match_percentage: int,
    four_week_plan: str,
    additional_considerations: str = None
) -> io.BytesIO:
    """Generate PDF with all analysis results"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )

    week_heading_style = ParagraphStyle(
        'WeekHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=HexColor('#1e40af'),
        spaceAfter=8,
        spaceBefore=16,
        leftIndent=0
    )

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=6,
        leftIndent=20,
        bulletIndent=10
    )

    # Title
    story.append(Paragraph("Application Analysis", title_style))
    story.append(Spacer(1, 0.3*inch))

    # Match Percentage
    match_color = HexColor('#10b981') if match_percentage >= 70 else HexColor('#f59e0b') if match_percentage >= 50 else HexColor('#ef4444')
    match_style = ParagraphStyle(
        'MatchStyle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=match_color,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    story.append(Paragraph(f"Match: {match_percentage}%", match_style))
    story.append(Spacer(1, 0.2*inch))

    # Recommendation
    story.append(Paragraph("Recommendation", heading_style))
    story.append(Paragraph(recommendation, body_style))
    story.append(Spacer(1, 0.2*inch))

    # Strengths
    story.append(Paragraph("Strengths", heading_style))
    for strength in strengths:
        story.append(Paragraph(f"• {strength}", body_style))
    story.append(Spacer(1, 0.2*inch))

    # Weaknesses
    story.append(Paragraph("Weaknesses", heading_style))
    for weakness in weaknesses:
        story.append(Paragraph(f"• {weakness}", body_style))
    story.append(PageBreak())

    # Four Week Plan
    story.append(Paragraph("4-Week Plan", heading_style))

    # Parse and format the 4-week plan
    plan_text = four_week_plan.strip()

    # Try to detect weeks using regex (handles both "Semana X" and "Week X")
    week_pattern = re.compile(
        r'(Semana\s*\d+|Week\s*\d+)\s*:\s*([\s\S]*?)(?=(?:Semana\s*\d+|Week\s*\d+)\s*:|$)',
        re.IGNORECASE | re.DOTALL
    )

    weeks = []
    for match in week_pattern.finditer(plan_text):
        week_number = match.group(1)
        week_content = match.group(2).strip()
        weeks.append((week_number, week_content))

    if weeks:
        # Format each week with proper spacing
        for week_num, week_content in weeks:
            # Extract title (everything until first period or "Objetivos:")
            title_match = re.match(r'^([^\.]+?)(?:\.|Objetivos:|Acciones:|Actions|Goals:)', week_content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                content = week_content[len(title_match.group(0)):].strip()
            else:
                # Fallback: use first sentence as title
                first_period = week_content.find('.')
                if first_period != -1:
                    title = week_content[:first_period].strip()
                    content = week_content[first_period + 1:].strip()
                else:
                    title = week_content.split('\n')[0].strip()
                    content = '\n'.join(week_content.split('\n')[1:]).strip()

            # Add week heading
            story.append(Paragraph(f"{week_num}: {title}", week_heading_style))

            # Process content line by line
            if content:
                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    # Check if it's a bullet point
                    if line.startswith(('-', '•', '*')):
                        bullet_text = line[1:].strip()
                        story.append(Paragraph(f"• {bullet_text}", bullet_style))
                    # Check if it's a section header
                    elif re.match(r'^(Objetivos|Acciones|Actions|Goals):', line, re.IGNORECASE):
                        story.append(Paragraph(f"<b>{line}</b>", body_style))
                    else:
                        story.append(Paragraph(line, body_style))

            story.append(Spacer(1, 0.15*inch))
    else:
        # Fallback: if no weeks detected, format line by line
        for line in plan_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Check for week headers
            week_header_match = re.match(r'^(semana\s*\d+|week\s*\d+)\s*:\s*(.+)$', line, re.IGNORECASE)
            if week_header_match:
                week_num = week_header_match.group(1)
                week_title = week_header_match.group(2)
                # Extract title from week_title
                first_period = week_title.find('.')
                if first_period != -1:
                    title = week_title[:first_period].strip()
                else:
                    title = week_title.strip()
                story.append(Paragraph(f"{week_num}: {title}", week_heading_style))
            elif line.startswith(('-', '•', '*')):
                bullet_text = line[1:].strip()
                story.append(Paragraph(f"• {bullet_text}", bullet_style))
            else:
                story.append(Paragraph(line, body_style))

    story.append(Spacer(1, 0.2*inch))

    # Additional Considerations
    if additional_considerations:
        story.append(Paragraph("Additional Considerations", heading_style))
        story.append(Paragraph(additional_considerations, body_style))
        story.append(Spacer(1, 0.2*inch))

    # Analysis Details
    story.append(PageBreak())
    story.append(Paragraph("Detailed CV Analysis", heading_style))
    cv_paragraphs = cv_analysis.split('\n')
    for para in cv_paragraphs[:20]:  # Limit length
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Detailed Job Offer Analysis", heading_style))
    offer_paragraphs = job_offer_analysis.split('\n')
    for para in offer_paragraphs[:20]:  # Limit length
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

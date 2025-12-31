from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
import io
from typing import List


def generate_pdf(
    cv_analysis: str,
    job_offer_analysis: str,
    strengths: List[str],
    weaknesses: List[str],
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
    
    # Title
    story.append(Paragraph("Análisis de Candidatura", title_style))
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
    story.append(Paragraph(f"Coincidencia: {match_percentage}%", match_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Recommendation
    story.append(Paragraph("Recomendación", heading_style))
    story.append(Paragraph(recommendation, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Strengths
    story.append(Paragraph("Puntos Fuertes", heading_style))
    for strength in strengths:
        story.append(Paragraph(f"• {strength}", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Weaknesses
    story.append(Paragraph("Puntos Débiles", heading_style))
    for weakness in weaknesses:
        story.append(Paragraph(f"• {weakness}", body_style))
    story.append(PageBreak())
    
    # Four Week Plan
    story.append(Paragraph("Plan de 4 Semanas", heading_style))
    plan_paragraphs = four_week_plan.split('\n')
    for para in plan_paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Additional Considerations
    if additional_considerations:
        story.append(Paragraph("Consideraciones Adicionales", heading_style))
        story.append(Paragraph(additional_considerations, body_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Analysis Details
    story.append(PageBreak())
    story.append(Paragraph("Análisis Detallado del CV", heading_style))
    cv_paragraphs = cv_analysis.split('\n')
    for para in cv_paragraphs[:20]:  # Limit length
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Análisis Detallado de la Oferta", heading_style))
    offer_paragraphs = job_offer_analysis.split('\n')
    for para in offer_paragraphs[:20]:  # Limit length
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


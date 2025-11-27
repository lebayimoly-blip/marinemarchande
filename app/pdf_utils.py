from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

# Palette MarineGab
MARINE_BLUE = colors.HexColor("#003366")
MARINE_GREEN = colors.HexColor("#007A3D")
MARINE_GOLD = colors.HexColor("#FFD700")
MARINE_LIGHT = colors.HexColor("#F5F5F5")

def build_pdf(file_path: str, title: str, data: list, logo_path: str = "app/static/logo.png"):
    """
    Génère un PDF stylisé avec logo, titre, tableau et pied de page.
    :param file_path: chemin du fichier PDF à générer
    :param title: titre du document
    :param data: liste de listes [[label, valeur], ...]
    :param logo_path: chemin du logo MarineGab
    """
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle(
        'MarineTitle',
        parent=styles['Title'],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=MARINE_BLUE,
        alignment=1,  # centré
        spaceAfter=20
    )

    footer_style = ParagraphStyle(
        'MarineFooter',
        parent=styles['Normal'],
        fontSize=10,
        textColor=MARINE_BLUE,
        alignment=1  # centré
    )

    # Logo
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=80, height=80))
        elements.append(Spacer(1, 12))

    # Titre
    elements.append(Paragraph(f"{title}", title_style))
    elements.append(Spacer(1, 20))

    # Tableau stylisé
    table = Table(data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), MARINE_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        # Corps du tableau
        ('BACKGROUND', (0, 1), (-1, -1), MARINE_LIGHT),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, MARINE_BLUE),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Pied de page valorisant OLOUOMO LAB
    footer_text = (
        f"MarineGab — Par "
        f"<font color='{MARINE_GOLD}'><b>OLOUOMO LAB</b></font> © 2025"
    )
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)

    # Génération
    doc.build(elements)

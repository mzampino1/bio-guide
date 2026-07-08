import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Cross-module pipeline dependencies
from guide.image_creation import generate_visual_assets
from processing.observation_analytics import get_peak_month_for_species

def _build_species_grid(species_list, cursor, body_style):
    """
    Helper function to transform a species array into a clean 2-column visual grid layout.
    """
    grid_data = []
    current_row = []
    
    for idx, species in enumerate(species_list):
        taxon_id = species.get("taxon_id")
        img_path = f"tmp/species_{taxon_id}.png"
        if not os.path.exists(img_path):
            img_path = "tmp/species_placeholder.png"
            
        species_photo = Image(img_path, width=1.3*inch, height=1.0*inch)
        
        # Pull peak metrics from database on-the-fly
        peak = get_peak_month_for_species(cursor, taxon_id)
        peak_text = f"<br/>Peak: <b>{peak['month_name']}</b> ({peak['sightings_in_peak_month']} obs)" if peak else ""
        
        card_text = f"""
        <b>#{idx+1} {species['common_name']}</b><br/>
        <i>{species['scientific_name']}</i><br/>
        Sightings: <b>{species['sightings']}</b>{peak_text}
        """
        species_details = Paragraph(card_text, body_style)
        
        card_table = Table([[species_photo, species_details]], colWidths=[1.4*inch, 2.1*inch])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9F9F9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        current_row.append(card_table)
        
        if len(current_row) == 2:
            grid_data.append(current_row)
            current_row = []
            
    if current_row:
        current_row.append("")
        grid_data.append(current_row)
        
    catalog_table = Table(grid_data, colWidths=[3.6*inch, 3.6*inch])
    catalog_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (0,0), 4),
        ('LEFTPADDING', (1,0), (1,-1), 4),
    ]))
    return catalog_table


def build_pdf_guide(location, top_overall, top_plants, top_animals, relative_abundance, monthly_trends, hotspots, cursor):
    """
    Compiles complete biodiversity metrics into a multi-page, publication-quality PDF.
    """
    # Consolidate all species variants to ensure assets download completely
    all_distinct_species = {s['taxon_id']: s for s in (top_overall + top_plants + top_animals)}.values()
    generate_visual_assets(monthly_trends, all_distinct_species, hotspots)
    
    os.makedirs("output", exist_ok=True)
    pdf_filename = f"output/{location.lower().replace(' ', '_')}_biodiversity_guide.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    PRIMARY_COLOR = colors.HexColor("#1B5E20")
    TEXT_COLOR = colors.HexColor("#212121")
    
    title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=24, leading=28, textColor=PRIMARY_COLOR, alignment=1, spaceAfter=4)
    subtitle_style = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#757575"), alignment=1, spaceAfter=15)
    section_style = ParagraphStyle('SecHeading', parent=styles['Heading2'], fontSize=14, leading=18, textColor=PRIMARY_COLOR, spaceBefore=12, spaceAfter=8, keepWithNext=True)
    body_style = ParagraphStyle('RepBody', parent=styles['Normal'], fontSize=9, leading=13, textColor=TEXT_COLOR)
    
    story = []
    
    # ==========================================
    # PAGE 1: TITLE, VISUAL MAPS & TRENDS
    # ==========================================
    story.append(Paragraph(f"Biodiversity Field Guide: {location}", title_style))
    story.append(Paragraph("Data Gathered via iNaturalist", subtitle_style))
    
    map_img = Image("tmp/location_map.png", width=3.5*inch, height=1.6*inch) if os.path.exists("tmp/location_map.png") else ""
    chart_img = Image("tmp/trend_chart.png", width=3.5*inch, height=1.6*inch) if os.path.exists("tmp/trend_chart.png") else ""
    
    visual_table = Table([[map_img, chart_img]], colWidths=[3.6*inch, 3.6*inch])
    visual_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(visual_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Relative Abundance Table Block
    story.append(Paragraph("Ecosystem Relative Abundance Distribution (Top 10)", section_style))
    abundance_rows = [["Rank", "Species (Common Name / Scientific Name)", "Sightings", "Ecosystem Share"]]
    for idx, species in enumerate(relative_abundance[:10]):
        abundance_rows.append([
            str(idx+1),
            f"{species['common_name']} ({species['scientific_name']})",
            str(species['sightings']),
            f"{species['percentage']}%"
        ])
    
    abundance_table = Table(abundance_rows, colWidths=[0.5*inch, 4.3*inch, 1.1*inch, 1.3*inch])
    abundance_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
    ]))
    story.append(abundance_table)
    
    # ==========================================
    # PAGE 2: SPECIES SECTIONS
    # ==========================================
    story.append(PageBreak())
    
    # Section A: Top 10 Overall
    story.append(Paragraph("Top 10 Most Common Overall Species", section_style))
    story.append(_build_species_grid(top_overall, cursor, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section B: Top 10 Plants
    story.append(Paragraph("Top 10 Dominant Regional Flora (Plants)", section_style))
    story.append(_build_species_grid(top_plants, cursor, body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Section C: Top 10 Animals
    story.append(Paragraph("Top 10 Dominant Regional Fauna (Animals)", section_style))
    story.append(_build_species_grid(top_animals, cursor, body_style))
    
    doc.build(story)
    print(f"\nPDF Generation Complete. File available at: {pdf_filename}")
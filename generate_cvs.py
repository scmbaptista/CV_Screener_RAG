#!/usr/bin/env python3
"""
Synthetic CV Generator
Generates 25-30 realistic, fake CVs in PDF format.
All data is loaded from data/cv_data.json for easy customization.
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from faker import Faker
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "data" / "cvs"
DATA_FILE = Path(__file__).parent / "data" / "cv_data.json"

# --- Load data from JSON ---

def load_cv_data() -> dict:
    """Load all CV generation data from the JSON file."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Data file not found: {DATA_FILE}\n"
            f"Please ensure data/cv_data.json exists."
        )
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

CV_DATA = load_cv_data()

# --- Avatar Generation ---

def generate_avatar(name: str, output_path: Path, size=200):
    """Generate a colored circle avatar with initials."""
    hue = sum(ord(c) for c in name) % 360
    import colorsys
    h = hue / 360.0
    r, g, b = colorsys.hls_to_rgb(h, 0.55, 0.7)
    rgb = (int(r * 255), int(g * 255), int(b * 255))

    img = Image.new("RGB", (size, size), rgb)
    draw = ImageDraw.Draw(img)

    border = 8
    draw.ellipse([border, border, size - border, size - border], fill=(255, 255, 255))
    inner_border = 12
    draw.ellipse([inner_border, inner_border, size - inner_border, size - inner_border], fill=rgb)

    initials = "".join([n[0] for n in name.split()[:2]]).upper()
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=80)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) / 2
    y = (size - text_height) / 2 - 10
    draw.text((x, y), initials, fill=(255, 255, 255), font=font)

    img.save(output_path, quality=95)
    return output_path

# --- CV Builder ---

def create_cv(candidate_id: int, output_dir: Path):
    """Generate a single synthetic CV as PDF."""

    gender = random.choice(["male", "female"])
    first_name = fake.first_name_male() if gender == "male" else fake.first_name_female()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"

    email = f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}"
    phone = fake.phone_number()
    city = fake.city()
    country = random.choice(CV_DATA["countries"])

    role = random.choice(CV_DATA["roles"])
    years_exp = random.randint(2, 15)

    # Generate work experience
    num_jobs = random.randint(2, 5)
    experiences = []
    current_date = datetime.now()
    for i in range(num_jobs):
        duration_months = random.randint(8, 36)
        end_date = current_date
        start_date = end_date - timedelta(days=duration_months * 30)
        company = random.choice(CV_DATA["companies"])
        job_title = role if i == 0 else random.choice(CV_DATA["roles"])

        # Build description from templates
        desc_parts = []
        for _ in range(random.randint(2, 4)):
            template = random.choice(CV_DATA["experience_descriptions"])
            desc = template.format(
                platform=fake.bs(),
                users=f"{random.randint(1000, 500000):,}",
                architecture=random.choice(CV_DATA["architectures"]),
                system=random.choice(CV_DATA["systems"]),
                pct=random.randint(20, 70),
                team_size=random.randint(2, 8),
                target=random.choice(CV_DATA["optimization_targets"]),
                team=random.choice(CV_DATA["collaboration_teams"]),
                product=random.choice(CV_DATA["products"]),
                security=random.choice(CV_DATA["security_systems"])
            )
            desc_parts.append(desc)

        experiences.append({
            "title": job_title,
            "company": company,
            "start": start_date.strftime("%b %Y"),
            "end": "Present" if i == 0 else end_date.strftime("%b %Y"),
            "description": " ".join(desc_parts)
        })
        current_date = start_date - timedelta(days=random.randint(30, 90))

    # Generate education
    num_degrees = random.randint(1, 2)
    educations = []
    for i in range(num_degrees):
        uni = random.choice(CV_DATA["universities"])
        degree = random.choice(CV_DATA["degree_types"])
        field = random.choice(CV_DATA["fields"])
        year = datetime.now().year - years_exp - random.randint(0, 5) - (i * 3)

        educations.append({
            "degree": f"{degree} in {field}",
            "institution": uni["name"],
            "abbr": uni["abbr"],
            "location": uni["location"],
            "year": str(year)
        })

    # Generate skills
    num_skills = random.randint(8, 18)
    skills = random.sample(CV_DATA["skills"], num_skills)

    # Generate languages
    native = random.choice(CV_DATA["languages"])
    languages = [(native, "Native")]
    other_langs = random.sample([l for l in CV_DATA["languages"] if l != native], random.randint(1, 3))
    for lang in other_langs:
        level = random.choice(["Fluent", "Professional", "Conversational"])
        languages.append((lang, level))

    # Generate summary
    domain = random.choice(CV_DATA["domains"])
    tech = random.choice(skills)
    summary_template = random.choice(CV_DATA["summary_templates"])
    summary = summary_template.format(role=role.lower(), years=years_exp, domain=domain, tech=tech)

    # Generate certifications (optional)
    certifications = []
    if random.random() > 0.3:
        certs = random.sample(CV_DATA["certifications"], random.randint(1, 3))
        certifications = certs

    # --- Build PDF ---
    filename = f"cv_{candidate_id:03d}_{full_name.replace(' ', '_').lower()}.pdf"
    filepath = output_dir / filename

    avatar_path = output_dir / f"avatar_{candidate_id:03d}.png"
    generate_avatar(full_name, avatar_path)

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        'Name', parent=styles['Heading1'], fontSize=24,
        textColor=colors.HexColor('#1a365d'), spaceAfter=6, fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=10, leading=14,
        alignment=TA_JUSTIFY, spaceAfter=8, textColor=colors.HexColor('#2d3748')
    )
    section_style = ParagraphStyle(
        'Section', parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor('#2c5282'), spaceAfter=8, spaceBefore=12,
        fontName='Helvetica-Bold', borderColor=colors.HexColor('#2c5282'),
        borderWidth=2, borderPadding=5, backColor=colors.HexColor('#ebf8ff')
    )
    job_title_style = ParagraphStyle(
        'JobTitle', parent=styles['Normal'], fontSize=11,
        fontName='Helvetica-Bold', textColor=colors.HexColor('#1a202c'), spaceAfter=2
    )
    job_meta_style = ParagraphStyle(
        'JobMeta', parent=styles['Normal'], fontSize=9,
        textColor=colors.HexColor('#718096'), spaceAfter=4
    )
    job_desc_style = ParagraphStyle(
        'JobDesc', parent=styles['Normal'], fontSize=9, leading=12,
        textColor=colors.HexColor('#4a5568'), spaceAfter=8, leftIndent=10
    )

    story = []

    # Header with avatar
    header_data = [
        [RLImage(str(avatar_path), width=2.5 * cm, height=2.5 * cm),
         Paragraph(f"""<b>{full_name}</b><br/>
         <font size=11 color='#4a5568'>{role}</font><br/>
         <font size=9 color='#718096'>{city}, {country} | {email} | {phone}</font>""", body_style)]
    ]
    header_table = Table(header_data, colWidths=[3 * cm, 14 * cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.2 * cm))

    # Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 0.2 * cm))

    # Work Experience
    story.append(Paragraph("WORK EXPERIENCE", section_style))
    for exp in experiences:
        story.append(Paragraph(f"{exp['title']} — {exp['company']}", job_title_style))
        story.append(Paragraph(f"{exp['start']} – {exp['end']}", job_meta_style))
        story.append(Paragraph(exp['description'], job_desc_style))

    # Education
    story.append(Paragraph("EDUCATION", section_style))
    for edu in educations:
        edu_text = f"<b>{edu['degree']}</b> — {edu['institution']} ({edu['abbr']})<br/>"
        edu_text += f"<font size=9 color='#718096'>{edu['location']} | Graduated: {edu['year']}</font>"
        story.append(Paragraph(edu_text, job_desc_style))

    # Skills
    story.append(Paragraph("SKILLS", section_style))
    skills_text = " • ".join(skills)
    story.append(Paragraph(f"<font size=10>{skills_text}</font>", body_style))

    # Languages
    story.append(Paragraph("LANGUAGES", section_style))
    lang_text = " | ".join([f"{lang} ({level})" for lang, level in languages])
    story.append(Paragraph(f"<font size=10>{lang_text}</font>", body_style))

    # Certifications
    if certifications:
        story.append(Paragraph("CERTIFICATIONS", section_style))
        cert_text = "<br/>• ".join([""] + certifications)
        story.append(Paragraph(f"<font size=10>{cert_text}</font>", body_style))

    # Footer
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
    story.append(Paragraph(
        f"<font size=8 color='#a0aec0'>This CV was generated synthetically for demonstration purposes. Candidate ID: {candidate_id:03d}</font>",
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.HexColor('#a0aec0'))
    ))

    doc.build(story)
    avatar_path.unlink()

    return {
        "id": candidate_id,
        "filename": filename,
        "name": full_name,
        "role": role,
        "email": email,
        "location": f"{city}, {country}",
        "skills": skills,
        "education": [e["abbr"] for e in educations],
        "years_exp": years_exp
    }


def generate_all_cvs(count: int = 30):
    """Generate the full dataset of synthetic CVs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for f in OUTPUT_DIR.glob("cv_*.pdf"):
        f.unlink()

    metadata = []
    print(f"Generating {count} synthetic CVs...")
    for i in range(1, count + 1):
        meta = create_cv(i, OUTPUT_DIR)
        metadata.append(meta)
        print(f"  ✓ {meta['filename']} — {meta['name']} ({meta['role']}, {meta['years_exp']}y exp)")

    print(f"\nDone! {count} CVs saved to {OUTPUT_DIR}")
    return metadata


if __name__ == "__main__":
    generate_all_cvs(30)

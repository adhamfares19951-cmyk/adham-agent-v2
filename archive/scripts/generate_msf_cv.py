import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

output_path = r"C:\Projects\adham-agent\dist_pages\MSF_Data_Entry_Adham_Alhabbash_CV.pdf"
desktop_path = os.path.expanduser(r"~\Desktop\MSF_Data_Entry_Adham_Alhabbash_CV.pdf")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# 1 Page Geometry: 612 x 792 pt
doc = SimpleDocTemplate(
    output_path,
    pagesize=letter,
    leftMargin=30,
    rightMargin=30,
    topMargin=24,
    bottomMargin=24
)

styles = getSampleStyleSheet()

# Custom styles
primary_color = colors.HexColor("#0B2545")    # Deep Navy
accent_color = colors.HexColor("#134074")     # Slate Navy
text_dark = colors.HexColor("#1D2D44")        # Charcoal text
text_muted = colors.HexColor("#4A5568")       # Slate grey
divider_color = colors.HexColor("#CBD5E1")    # Subtle line

name_style = ParagraphStyle(
    "Name",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=20,
    textColor=primary_color,
    alignment=1
)

title_style = ParagraphStyle(
    "Title",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=13,
    textColor=accent_color,
    alignment=1
)

contact_style = ParagraphStyle(
    "Contact",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=11,
    textColor=text_muted,
    alignment=1
)

section_heading = ParagraphStyle(
    "SectionHeading",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=primary_color,
    spaceBefore=0,
    spaceAfter=2
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.2,
    leading=10.5,
    textColor=text_dark
)

job_title_style = ParagraphStyle(
    "JobTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.8,
    leading=11,
    textColor=text_dark
)

company_style = ParagraphStyle(
    "Company",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.2,
    leading=10.5,
    textColor=text_muted
)

date_style = ParagraphStyle(
    "Date",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.2,
    leading=10.5,
    textColor=accent_color,
    alignment=2
)

bullet_style = ParagraphStyle(
    "Bullet",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=text_dark,
    leftIndent=10,
    firstLineIndent=-6,
    spaceAfter=1.5
)

skill_header = ParagraphStyle(
    "SkillHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.2,
    leading=10.5,
    textColor=primary_color
)

story = []

# --- HEADER ---
story.append(Paragraph("ADHAM F. A. ALHABBASH", name_style))
story.append(Spacer(1, 2))
story.append(Paragraph("MEDICAL DATA ENTRY OPERATOR & HEALTHCARE RECORDS SPECIALIST", title_style))
story.append(Spacer(1, 2))
contact_line = "Khan Younis, Gaza Strip, Palestine | Phone / WhatsApp: +972-599561140 | Email: adoomafares@gmail.com"
story.append(Paragraph(contact_line, contact_style))
story.append(Spacer(1, 5))
story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=5, spaceBefore=0))

# --- PROFESSIONAL SUMMARY ---
story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading))
summary_text = (
    "Detail-driven <b>Data Entry & Medical Information Specialist</b> with extensive experience extracting, verifying, and digitizing "
    "clinical patient records across major healthcare facilities and international humanitarian programs in Gaza, including <b>Nasser Medical Complex (UNDP)</b> "
    "and the <b>Palestinian Red Crescent Society (PRCS)</b>. Proven proficiency in systematic data extraction from physical paper archives and electronic health databases, "
    "cross-referencing patient records, and standardizing case logs with 100% data fidelity. Fully proficient in <b>MS Excel, Word, and Google Sheets</b> with immediate adaptability "
    "to epidemiological research platforms including <b>REDCap, Epi Info, and Fuchia</b>. Grounded in medical terminology, rigorous patient confidentiality standards, and an unwavering "
    "commitment to MSF core humanitarian principles and operational research protocols."
)
story.append(Paragraph(summary_text, body_style))
story.append(Spacer(1, 5))
story.append(HRFlowable(width="100%", thickness=0.5, color=divider_color, spaceAfter=4, spaceBefore=0))

# --- PROFESSIONAL EXPERIENCE ---
story.append(Paragraph("RELEVANT EXPERIENCE", section_heading))

def build_job_header(role, org, dates):
    col1 = Paragraph(f"<b>{role}</b> - {org}", job_title_style)
    col2 = Paragraph(dates, date_style)
    t = Table([[col1, col2]], colWidths=[420, 132])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    return t

# 1. Nasser Medical Complex - Emergency Healthcare Data Volunteer
story.append(build_job_header("Medical Data & Emergency IT Volunteer", "Nasser Medical Complex", "2023 - 2024"))
story.append(Paragraph("• Systematically logged, organized, and tracked emergency admissions, patient intake logs, and clinical records under severe emergency operating conditions.", bullet_style))
story.append(Paragraph("• Maintained high data completeness and strict patient confidentiality, ensuring accurate records handover between clinical and administrative units.", bullet_style))
story.append(Paragraph("• Troubleshot and restored operational continuity for clinical data terminals, hospital management systems, and printers to prevent clinical documentation delays.", bullet_style))
story.append(Spacer(1, 3))

# 2. Al-Fokhari Municipality - Data Entry Specialist
story.append(build_job_header("Data Entry & Archiving Specialist", "Al-Fokhari Municipality", "2021 - 2022"))
story.append(Paragraph("• Digitized and archived thousands of legacy physical paper files into structured electronic databases with zero data loss and rigorous validation routines.", bullet_style))
story.append(Paragraph("• Executed high-volume alphanumeric data entry using advanced MS Excel formulas (VLOOKUP, validation rules, deduplication) to clean and audit historical registries.", bullet_style))
story.append(Paragraph("• Audited database inputs against source documents to identify discrepancies, missing fields, and duplicates, maintaining full audit trails.", bullet_style))
story.append(Spacer(1, 3))

# 3. Nasser Medical Complex - UNDP Project
story.append(build_job_header("Health Informatics & IT Support Technician", "Nasser Medical Complex - UNDP Project", "2019 - 2020"))
story.append(Paragraph("• Supported hospital departmental databases and clinical record terminals across inpatient, surgical, and emergency wards within a UNDP-funded program.", bullet_style))
story.append(Paragraph("• Ensured data security, strict physical and digital patient file confidentiality, and reliable backup procedures adhering to institutional healthcare standards.", bullet_style))
story.append(Paragraph("• Collaborated directly with medical and administrative staff to streamline patient documentation flows and resolve computerized entry errors.", bullet_style))
story.append(Spacer(1, 3))

# 4. Joint Council for Solid Waste Management
story.append(build_job_header("Field Operations Data Monitor", "Joint Council for Solid Waste Management (JCSWM)", "2024"))
story.append(Paragraph("• Conducted systematic field monitoring, daily data collection, logistical tracking, and compiled quantitative operational reports for executive management.", bullet_style))
story.append(Paragraph("• Maintained rigorous operational data verification, ensuring discrepancy-free reporting in humanitarian and municipal services.", bullet_style))
story.append(Spacer(1, 3))

# 5. Palestinian Red Crescent Society (PRCS)
story.append(build_job_header("Humanitarian Field & IT Support Specialist", "Palestinian Red Crescent Society (PRCS)", "2018"))
story.append(Paragraph("• Deployed and maintained secure communication and data infrastructure connecting humanitarian coordination units and emergency response centers.", bullet_style))
story.append(Paragraph("• Adhered to international humanitarian standards, data confidentiality guidelines, and protective protocols in conflict-affected environments.", bullet_style))

story.append(Spacer(1, 4))
story.append(HRFlowable(width="100%", thickness=0.5, color=divider_color, spaceAfter=4, spaceBefore=0))

# --- KEY COMPETENCIES & TECHNICAL SKILLS ---
story.append(Paragraph("TECHNICAL SKILLS & KEY COMPETENCIES", section_heading))

skills_data = [
    [
        Paragraph("<b>Data Management & Research:</b>", skill_header),
        Paragraph("High-speed alphanumeric data entry, Medical record extraction & auditing, Paper-to-electronic data migration, Discrepancy reconciliation, Operational research protocol adherence.", body_style)
    ],
    [
        Paragraph("<b>Software & Research Platforms:</b>", skill_header),
        Paragraph("<b>MS Excel</b> (Advanced: VLOOKUP, pivot tables, data cleaning, validation), MS Word, Google Workspace, rapid adaptability to <b>REDCap, Epi Info, Fuchia</b>.", body_style)
    ],
    [
        Paragraph("<b>Healthcare Knowledge & Ethics:</b>", skill_header),
        Paragraph("Medical terminology familiarity, Patient confidentiality protocols, Data protection compliance, Clinical archiving standards, Trauma & patient intake workflow understanding.", body_style)
    ],
    [
        Paragraph("<b>Humanitarian Competencies:</b>", skill_header),
        Paragraph("Strict alignment with <b>MSF principles</b> (neutrality, impartiality, independence), extreme attention to detail, high stress resilience, collaborative teamwork in emergency settings.", body_style)
    ],
    [
        Paragraph("<b>Languages:</b>", skill_header),
        Paragraph("<b>Arabic:</b> Native (fluent spoken & written) | <b>English:</b> Professional working & technical proficiency (fluent spoken & written).", body_style)
    ]
]

skills_table = Table(skills_data, colWidths=[150, 402])
skills_table.setStyle(TableStyle([
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING', (0,0), (-1,-1), 0),
    ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ('TOPPADDING', (0,0), (-1,-1), 1),
    ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
]))
story.append(skills_table)

story.append(Spacer(1, 4))
story.append(HRFlowable(width="100%", thickness=0.5, color=divider_color, spaceAfter=4, spaceBefore=0))

# --- EDUCATION & CERTIFICATIONS ---
story.append(Paragraph("EDUCATION & CERTIFICATIONS", section_heading))

edu_text = (
    "<b>Diploma in Computer Technical Support & Information Systems</b> - University College of Science and Technology, Khan Younis (2015)<br/>"
    "<b>Professional Certifications:</b> ICDL (International Computer Driving Licence - 40h) · CompTIA A+ Professional (60h) · Cisco CCNA Networking · Specialized Data Entry & Archiving"
)
story.append(Paragraph(edu_text, body_style))

doc.build(story)

# Also copy to desktop
import shutil
shutil.copy(output_path, desktop_path)

print("PDF generated successfully at:")
print(" - Output:", output_path)
print(" - Desktop:", desktop_path)
print(" - File size:", os.path.getsize(output_path), "bytes")

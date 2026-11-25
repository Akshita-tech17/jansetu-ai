"""
Module 5: Pre-filled UP e-District Draft PDF Builder.
Renders bilingual Devanagari + English application forms using ReportLab.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from schemas import FormSlots, EligibilityResult

load_dotenv()

FONTS_DIR = Path(__file__).resolve().parent.parent / "data" / "fonts"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = FONTS_DIR / "NotoSansDevanagari-Regular.ttf"
FONT_REGISTERED = False

if FONT_PATH.exists():
    try:
        pdfmetrics.registerFont(TTFont("Devanagari", str(FONT_PATH)))
        FONT_REGISTERED = True
    except Exception as e:
        print(f"[Font Warning] Could not register Devanagari font: {e}")

MAIN_FONT = "Devanagari" if FONT_REGISTERED else "Helvetica"
BOLD_FONT = "Devanagari" if FONT_REGISTERED else "Helvetica-Bold"


def build_application_pdf(
    slots: FormSlots,
    eligibility: EligibilityResult,
    output_path: str = None
) -> str:
    """Generates an official-looking Uttar Pradesh e-District pre-filled application draft."""
    if not output_path:
        ref_id = uuid.uuid4().hex[:8].upper()
        output_path = str(OUTPUTS_DIR / f"UP_eDistrict_{ref_id}.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        "HeaderTitle",
        fontName=BOLD_FONT,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0D3B66"),
        alignment=1
    )
    sub_header_style = ParagraphStyle(
        "SubHeaderTitle",
        fontName=MAIN_FONT,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#333333"),
        alignment=1
    )
    section_title = ParagraphStyle(
        "SectionTitle",
        fontName=BOLD_FONT,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0D3B66")
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=MAIN_FONT,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#222222")
    )
    badge_style = ParagraphStyle(
        "Badge",
        fontName=BOLD_FONT,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#087E43"),
        alignment=1
    )

    story = []

    # 1. Top Decorative Government Header
    story.append(Paragraph("<b>UTTAR PRADESH e-DISTRICT CITIZEN SERVICES</b>", header_style))
    story.append(Paragraph("उत्तर प्रदेश ई-डिस्ट्रिक्ट — जन कल्याण आवेदन प्रारूप (Draft)", sub_header_style))
    story.append(Paragraph("<font size=8 color='#666666'>Powered by JanSetu AI Vernacular Citizen Assistant • AI Kaushal Hackathon</font>", sub_header_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0D3B66"), spaceBefore=2, spaceAfter=8))

    # Reference & Metadata Bar
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    app_id = f"UP-EDIST-{uuid.uuid4().hex[:8].upper()}"
    meta_data = [
        [
            Paragraph(f"<b>Application Ref No:</b> {app_id}", body_style),
            Paragraph(f"<b>Date/Time:</b> {current_time}", body_style),
            Paragraph("<b>Status:</b> PRE-CHECK VERIFIED", badge_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[200, 180, 160])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # 2. Scheme & Applicant Details Table
    story.append(Paragraph("1. आवेदक एवं योजना का विवरण (Applicant & Scheme Details)", section_title))
    story.append(Spacer(1, 6))

    scheme_names_map = {
        "old_age_pension": "उत्तर प्रदेश वृद्धावस्था पेंशन योजना (UP Old-Age Pension Scheme)",
        "income_cert": "आय प्रमाण पत्र (Income Certificate)",
        "caste_cert": "जाति प्रमाण पत्र (Caste Certificate)",
        "pm_kisan": "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN)",
        "jansunwai": "जनसुनवाई - नागरिक शिकायत (Jansunwai IGRS)"
    }
    scheme_display = scheme_names_map.get(slots.scheme_type, slots.scheme_type or "सरकारी जनकल्याण योजना")

    residency_display = "ग्रामीण (Rural)" if slots.residency_type == "rural" else (
        "शहरी (Urban)" if slots.residency_type == "urban" else "दर्ज नहीं"
    )
    income_display = f"₹ {int(slots.annual_income):,}/- प्रति वर्ष" if slots.annual_income else "उपलब्ध नहीं"

    details_data = [
        [Paragraph("<b>लक्षित योजना (Scheme Name):</b>", body_style), Paragraph(scheme_display, body_style)],
        [Paragraph("<b>आवेदक का नाम (Applicant Name):</b>", body_style), Paragraph(slots.applicant_name or "दर्ज नहीं", body_style)],
        [Paragraph("<b>पिता / पति का नाम (Father/Spouse):</b>", body_style), Paragraph(slots.father_or_husband_name or "उपलब्ध नहीं", body_style)],
        [Paragraph("<b>आयु (Age):</b>", body_style), Paragraph(f"{slots.age} वर्ष" if slots.age else "उपलब्ध नहीं", body_style)],
        [Paragraph("<b>जनपद / जिला (District):</b>", body_style), Paragraph(slots.district or "उत्तर प्रदेश", body_style)],
        [Paragraph("<b>क्षेत्रीय निवास (Residency Type):</b>", body_style), Paragraph(residency_display, body_style)],
        [Paragraph("<b>परिवार की कुल वार्षिक आय (Annual Income):</b>", body_style), Paragraph(income_display, body_style)],
    ]
    if slots.grievance_summary:
        details_data.append([
            Paragraph("<b>शिकायत विवरण (Grievance Summary):</b>", body_style),
            Paragraph(slots.grievance_summary, body_style)
        ])

    details_table = Table(details_data, colWidths=[200, 340])
    details_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DEE4")),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F8F9FA")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 14))

    # 3. Grounded Eligibility Assessment
    story.append(Paragraph("2. नियम आधारित पात्रता सत्यापन (Grounded Eligibility Check)", section_title))
    story.append(Spacer(1, 6))

    status_color = colors.HexColor("#087E43") if eligibility.is_eligible else colors.HexColor("#CF222E")
    status_text = "पूर्णतः पात्र (ELIGIBLE)" if eligibility.is_eligible else "अपात्र अथवा अपूर्ण (INCOMPLETE)"

    elig_data = [
        [Paragraph("<b>पात्रता परिणाम (Result):</b>", body_style), Paragraph(f"<b><font color='{status_color}'>{status_text}</font></b>", body_style)],
        [
            Paragraph("<b>सत्यापित मानदंड (Evaluated Rules):</b>", body_style),
            Paragraph("<br/>".join([f"• {r}" for r in eligibility.reasons]) if eligibility.reasons else "सभी प्राथमिक शर्तें पूर्ण", body_style)
        ],
        [
            Paragraph("<b>नियम संदर्भ (Official Rule Citations):</b>", body_style),
            Paragraph("<br/>".join([f"• {c}" for c in eligibility.citations]) if eligibility.citations else "UP Govt Scheme Guidelines", body_style)
        ]
    ]
    elig_table = Table(elig_data, colWidths=[200, 340])
    elig_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DEE4")),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F8F9FA")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(elig_table)
    story.append(Spacer(1, 14))

    # 4. Digital Signature & Interoperability Barcode/JSON Box
    story.append(Paragraph("3. ई-डिस्ट्रिक्ट पोर्टल एकीकरण डेटा (Machine-Readable Interop Payload)", section_title))
    story.append(Spacer(1, 4))
    raw_json_snippet = slots.model_dump_json(exclude_none=True)
    json_para = Paragraph(f"<font size=7 face='Courier' color='#333333'>{raw_json_snippet}</font>", body_style)
    json_table = Table([[json_para]], colWidths=[540])
    json_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EAEFF5")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#B0C4DE")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(json_table)
    story.append(Spacer(1, 12))

    # Declaration Footer
    footer_text = "<b>नागरिक स्व-घोषणा:</b> प्रमाणित किया जाता है कि मेरे द्वारा दी गई उपरोक्त जानकारी सत्य एवं सही है। किसी भी असत्य विवरण के लिए मैं स्वयं उत्तरदायी रहूँगा/रहूँगी।"
    story.append(Paragraph(f"<font size=8 color='#555555'>{footer_text}</font>", body_style))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    print("Testing PDF Builder...")
    sample_slots = FormSlots(
        scheme_type="old_age_pension",
        applicant_name="रामेश्वर प्रसाद",
        father_or_husband_name="काशीनाथ प्रसाद",
        age=62,
        district="वाराणसी",
        residency_type="rural",
        annual_income=42000
    )
    sample_eligibility = EligibilityResult(
        is_eligible=True,
        reasons=[
            "आवेदक की आयु 62 वर्ष है (न्यूनतम 60 वर्ष की शर्त पूर्ण)।",
            "वार्षिक आय ₹42,000/- ग्रामीण सीमा (₹46,080/-) के अंतर्गत है।",
            "अन्य किसी सरकारी पेंशन का लाभार्थी नहीं है।"
        ],
        citations=[
            "old_age_pension.md - पात्रता मानदंड",
            "समाज कल्याण विभाग, उत्तर प्रदेश शासन नियमावली"
        ]
    )
    test_pdf = str(OUTPUTS_DIR / "sample_up_application.pdf")
    build_application_pdf(sample_slots, sample_eligibility, test_pdf)
    print(f"Generated PDF at: {test_pdf} (Exists: {os.path.exists(test_pdf)})")

"""
forms/filing_service.py: "Ending in Something Filed" Engine.
Simulates official submission to UP e-District & Family ID (एक परिवार, एक पहचान) portals,
and generates the legal Submission Acknowledgment Receipt (आवेदन पावती पत्र).
"""
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from core.family_id import FamilyProfile
from core.discovery_engine import MatchedScheme

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
FONTS_DIR = Path(__file__).resolve().parent.parent / "data" / "fonts"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = FONTS_DIR / "NotoSansDevanagari-Regular.ttf"
FONT_NAME = "Devanagari" if FONT_PATH.exists() else "Helvetica"
BOLD_FONT = "Devanagari" if FONT_PATH.exists() else "Helvetica-Bold"


def file_applications_and_generate_receipt(
    profile: FamilyProfile,
    selected_schemes: List[MatchedScheme],
    output_path: str = None
) -> Dict[str, Any]:
    """
    Simulates final transaction filing into UP e-District & Family ID APIs.
    Produces official Acknowledgment Receipt PDF with tracking number and SLA date.
    """
    app_number = f"UP-EDIST-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    filing_timestamp = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    sla_resolution_date = (datetime.now() + timedelta(days=15)).strftime("%d-%m-%Y")

    if not output_path:
        output_path = str(OUTPUTS_DIR / f"Avedan_Pavti_{app_number}.pdf")

    # Build the official filing receipt PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "ReceiptHeader",
        fontName=BOLD_FONT,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0D3B66"),
        alignment=1
    )
    sub_header_style = ParagraphStyle(
        "ReceiptSubHeader",
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#333333"),
        alignment=1
    )
    sec_title = ParagraphStyle(
        "SecTitle",
        fontName=BOLD_FONT,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0D3B66")
    )
    body_style = ParagraphStyle(
        "ReceiptBody",
        fontName=FONT_NAME,
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1A202C")
    )
    success_badge = ParagraphStyle(
        "SuccessBadge",
        fontName=BOLD_FONT,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#15803D"),
        alignment=1
    )

    story = []

    # 1. State Emblem & Header
    story.append(Paragraph("<b>उत्तर प्रदेश शासन — एकीकृत ई-डिस्ट्रिक्ट एवं परिवार पहचान पत्र (Family ID)</b>", header_style))
    story.append(Paragraph("<b>APPLICATION SUBMISSION ACKNOWLEDGMENT RECEIPT (आवेदन पावती पत्र)</b>", header_style))
    story.append(Paragraph("<font size=8 color='#555555'>प्रदत्त सेवा: जनसेतु एआई एकीकृत नागरिक सहायक पोर्टल (JanSetu AI) • उत्तर प्रदेश जनहित गारंटी अधिनियम 2011</font>", sub_header_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0D3B66"), spaceBefore=2, spaceAfter=8))

    # 2. Tracking Box
    track_data = [
        [
            Paragraph(f"<b>आवेदन क्रमांक (Ref No):</b><br/><b><font size=11 color='#0D3B66'>{app_number}</font></b>", body_style),
            Paragraph(f"<b>परिवार आईडी (Family ID):</b><br/>{profile.family_id}", body_style),
            Paragraph(f"<b>जमा करने का समय:</b><br/>{filing_timestamp}", body_style),
            Paragraph("<b>आवेदन स्थिति:</b><br/><b><font color='#15803D'>जमा एवं प्रेषित (FILED)</font></b>", success_badge)
        ]
    ]
    track_table = Table(track_data, colWidths=[150, 130, 130, 130])
    track_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#86EFAC")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(track_table)
    story.append(Spacer(1, 10))

    # 3. Family Profile Section
    story.append(Paragraph("1. आवेदक एवं परिवार पहचान पत्र विवरण (Family Profile Details)", sec_title))
    story.append(Spacer(1, 4))

    profile_data = [
        [Paragraph("<b>परिवार के मुखिया:</b>", body_style), Paragraph(profile.head_name, body_style),
         Paragraph("<b>राशन कार्ड संख्या:</b>", body_style), Paragraph(profile.ration_card_number, body_style)],
        [Paragraph("<b>जनपद (District):</b>", body_style), Paragraph(profile.district, body_style),
         Paragraph("<b>विकास खंड / तहसील:</b>", body_style), Paragraph(profile.block_or_ward, body_style)],
        [Paragraph("<b>ग्राम / मोहल्ला:</b>", body_style), Paragraph(profile.village_or_mohalla, body_style),
         Paragraph("<b>क्षेत्रीय निवास:</b>", body_style), Paragraph("ग्रामीण (Rural)" if profile.residency_type == "rural" else "शहरी", body_style)],
        [Paragraph("<b>सत्यापित वार्षिक आय:</b>", body_style), Paragraph(f"₹ {int(profile.annual_income):,}/-", body_style),
         Paragraph("<b>सामाजिक श्रेणी / भूमि:</b>", body_style), Paragraph(f"{profile.social_category} / {profile.land_holding_acres} एकड़", body_style)]
    ]
    prof_table = Table(profile_data, colWidths=[130, 140, 130, 140])
    prof_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#F8FAFC")),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(prof_table)
    story.append(Spacer(1, 10))

    # 4. Schemes Filed Table
    story.append(Paragraph("2. एकमुश्त निस्तारित योजनाएं (Bundled Schemes Successfully Filed)", sec_title))
    story.append(Spacer(1, 4))

    scheme_rows = [
        [
            Paragraph("<b>क्र.</b>", body_style),
            Paragraph("<b>योजना का नाम (Scheme)</b>", body_style),
            Paragraph("<b>लाभार्थी (Beneficiary)</b>", body_style),
            Paragraph("<b>वार्षिक देय लाभ (Benefit)</b>", body_style),
            Paragraph("<b>निस्तारण प्राधिकारी (Authority)</b>", body_style)
        ]
    ]
    for idx, s in enumerate(selected_schemes, 1):
        scheme_rows.append([
            Paragraph(str(idx), body_style),
            Paragraph(f"<b>{s.scheme_name}</b><br/><font size=8 color='#555555'>{s.department}</font>", body_style),
            Paragraph(f"{s.beneficiary_name} ({s.relation})", body_style),
            Paragraph(f"<font color='#0D3B66'><b>{s.annual_benefit}</b></font>", body_style),
            Paragraph("सक्षम अधिकारी (तहसील/ब्लॉक)", body_style)
        ])

    scheme_table = Table(scheme_rows, colWidths=[25, 205, 120, 110, 80])
    scheme_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(scheme_table)
    story.append(Spacer(1, 10))

    # 5. Service Delivery SLA & Interoperability Barcode Box
    story.append(Paragraph("3. जनहित गारंटी सेवा गारंटी एवं ई-डिस्ट्रिक्ट टोकन (SLA & Direct Dispatch Token)", sec_title))
    story.append(Spacer(1, 4))

    sla_data = [
        [
            Paragraph(f"<b>उत्तर प्रदेश जनहित गारंटी अधिनियम के तहत सेवा निस्तारण की निर्धारित समय सीमा: 15 कार्य दिवस (अंतिम तिथि: {sla_resolution_date})</b><br/>"
                      f"<font size=8 color='#555555'>संबंधित विभाग के अधिकारी (BDO/तहसीलदार) को डिजिटल रूप से प्रेषित। SMS द्वारा नागरिक को आवेदन प्रगति भेजी जा रही है।</font><br/>"
                      f"<font size=7 face='Courier' color='#0D3B66'>DISPATCH_HASH: SHA256:{uuid.uuid4().hex.upper()[:32]} | EDISTRICT_PORTAL_INGESTION_STATUS: 200_OK</font>", body_style)
        ]
    ]
    sla_table = Table(sla_data, colWidths=[540])
    sla_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(sla_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<font size=8 color='#64748B'>* यह पावती उत्तर प्रदेश शासन के फैमिली आईडी (Family ID - Ek Parivar Ek Pehchan) एकीकृत डिजिटल फ्रेमवर्क द्वारा स्वतः जारी की गई है। इसके लिए किसी सरकारी कार्यालय में भौतिक चक्कर लगाने की आवश्यकता नहीं है।</font>", body_style))

    doc.build(story)

    return {
        "status": "FILED_SUCCESSFULLY",
        "application_number": app_number,
        "family_id": profile.family_id,
        "head_name": profile.head_name,
        "filing_timestamp": filing_timestamp,
        "sla_resolution_date": sla_resolution_date,
        "schemes_filed_count": len(selected_schemes),
        "receipt_pdf_url": f"/outputs/{Path(output_path).name}"
    }


if __name__ == "__main__":
    from core.family_id import lookup_family
    from core.discovery_engine import discover_schemes_for_family
    prof = lookup_family("24018291024")
    basket = discover_schemes_for_family(prof)
    receipt = file_applications_and_generate_receipt(prof, basket.matched_schemes)
    print("Filing Receipt Generated:")
    print(receipt)


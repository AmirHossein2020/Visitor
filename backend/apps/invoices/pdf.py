from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
FONT_NAME = "InvoiceDejaVu"
FONT_BOLD = "InvoiceDejaVuBold"


def register_fonts():
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_DIR / "DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, FONT_DIR / "DejaVuSans-Bold.ttf"))


def fa(value):
    return get_display(arabic_reshaper.reshape(str(value or "")))


def persian_digits(value):
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def money(value):
    return fa(f"{value:,.2f} تومان")


def decimal_text(value):
    rendered = f"{value:f}".rstrip("0").rstrip(".")
    return persian_digits(rendered or "0")


def shaped_paragraph(value, style, max_chars=50):
    words = str(value or "").split()
    if not words:
        return Paragraph("", style)
    lines, current = [], []
    for word in words:
        candidate = " ".join((*current, word))
        if current and len(candidate) > max_chars:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return Paragraph("<br/>".join(fa(line) for line in lines), style)


def info_table(title, fields, styles):
    rows = [[Paragraph(fa(title), styles["section_title"])]]
    for label, value in fields:
        if value:
            rows.append([
                shaped_paragraph(value, styles["value"], 58),
                Paragraph(fa(label), styles["label"]),
            ])
    table = Table(rows, colWidths=[145 * mm, 35 * mm], hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#E8E8E8")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
        ("INNERGRID", (0, 1), (-1, -1), 0.35, colors.HexColor("#777777")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def build_invoice_pdf(invoice):
    register_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"invoice-{invoice.invoice_number}",
        author=invoice.seller_name,
    )
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("FaTitle", parent=base["Title"], fontName=FONT_BOLD, fontSize=18, leading=25, alignment=TA_CENTER, textColor=colors.black),
        "seller": ParagraphStyle("FaSeller", parent=base["Heading2"], fontName=FONT_BOLD, fontSize=12, leading=18, alignment=TA_CENTER),
        "section_title": ParagraphStyle("FaSection", parent=base["Heading3"], fontName=FONT_BOLD, fontSize=10, leading=15, alignment=TA_CENTER),
        "label": ParagraphStyle("FaLabel", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=8.5, leading=13, alignment=TA_RIGHT),
        "value": ParagraphStyle("FaValue", parent=base["BodyText"], fontName=FONT_NAME, fontSize=8.5, leading=13, alignment=TA_RIGHT),
        "cell": ParagraphStyle("FaCell", parent=base["BodyText"], fontName=FONT_NAME, fontSize=7.5, leading=11, alignment=TA_CENTER),
        "cell_right": ParagraphStyle("FaCellRight", parent=base["BodyText"], fontName=FONT_NAME, fontSize=7.5, leading=11, alignment=TA_RIGHT),
        "small": ParagraphStyle("FaSmall", parent=base["BodyText"], fontName=FONT_NAME, fontSize=8, leading=12, alignment=TA_RIGHT),
        "status": ParagraphStyle("FaStatus", parent=base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#555555")),
    }

    issued = timezone.localtime(invoice.issued_at)
    date_text = persian_digits(issued.strftime("%Y/%m/%d - %H:%M"))
    header = Table([
        [Paragraph(fa("فاکتور فروش"), styles["title"])],
        [Paragraph(fa(invoice.seller_name), styles["seller"])],
        [Table([[
            Paragraph(fa(f"تاریخ صدور: {date_text}"), styles["small"]),
            Paragraph(fa(f"شماره فاکتور: {invoice.invoice_number}"), styles["small"]),
        ]], colWidths=[90 * mm, 90 * mm])],
    ], colWidths=[180 * mm])
    header.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story = [header, Spacer(1, 5 * mm)]

    if invoice.revision_number > 1:
        story.extend([
            Paragraph(fa(f"نسخه اصلاحی {persian_digits(invoice.revision_number)}"), styles["status"]),
            Spacer(1, 3 * mm),
        ])

    if invoice.status == invoice.Status.CANCELLED:
        story.extend([Paragraph(fa("باطل شده"), styles["status"]), Spacer(1, 3 * mm)])
    elif invoice.status == invoice.Status.SUPERSEDED:
        root = invoice.revision_of or invoice
        replacement = root.revisions.filter(revision_number=invoice.revision_number + 1).first()
        label = f"جایگزین شده با فاکتور {replacement.invoice_number}" if replacement else "جایگزین شده"
        story.extend([Paragraph(fa(label), styles["status"]), Spacer(1, 3 * mm)])

    story.extend([
        info_table("مشخصات فروشنده", [
            ("نام فروشنده / شرکت", invoice.seller_name),
            ("شماره تماس", invoice.seller_phone_number),
            ("کد اقتصادی", invoice.seller_economic_code),
            ("شناسه ملی", invoice.seller_national_id),
            ("شماره ثبت", invoice.seller_registration_number),
            ("کد پستی", invoice.seller_postal_code),
            ("نشانی", invoice.seller_address),
        ], styles),
        Spacer(1, 3 * mm),
        info_table("مشخصات خریدار", [
            ("نام خریدار", invoice.buyer_name),
            ("نام شرکت", invoice.buyer_company_name),
            ("شماره تماس", invoice.buyer_phone_number),
            ("کد اقتصادی", invoice.buyer_economic_code),
            ("کد پستی", invoice.buyer_postal_code),
            ("نشانی", invoice.buyer_address),
        ], styles),
        Spacer(1, 5 * mm),
    ])

    table_data = [[Paragraph(fa(label), styles["label"]) for label in ("مبلغ کل", "قیمت واحد", "واحد", "تعداد", "برند", "شرح کالا", "ردیف")]]
    for index, item in enumerate(invoice.items.all(), start=1):
        table_data.append([
            Paragraph(money(item.line_total), styles["cell"]),
            Paragraph(money(item.unit_price), styles["cell"]),
            shaped_paragraph(item.unit, styles["cell"], 12),
            Paragraph(decimal_text(item.quantity), styles["cell"]),
            shaped_paragraph(item.brand or "—", styles["cell"], 15),
            shaped_paragraph(item.product_name, styles["cell_right"], 25),
            Paragraph(persian_digits(index), styles["cell"]),
        ])
    items_table = Table(table_data, colWidths=[31 * mm, 31 * mm, 18 * mm, 18 * mm, 25 * mm, 47 * mm, 10 * mm], repeatRows=1, hAlign="RIGHT")
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCDCDC")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([items_table, Spacer(1, 5 * mm)])

    totals = Table([
        [Paragraph(money(invoice.subtotal), styles["value"]), Paragraph(fa("جمع جزء"), styles["label"])],
        [Paragraph(money(invoice.discount_amount), styles["value"]), Paragraph(fa("تخفیف"), styles["label"])],
        [Paragraph(money(invoice.tax_amount), styles["value"]), Paragraph(fa("مالیات"), styles["label"])],
        [Paragraph(money(invoice.duties_amount), styles["value"]), Paragraph(fa("عوارض"), styles["label"])],
        [Paragraph(money(invoice.final_amount), styles["label"]), Paragraph(fa("مبلغ نهایی"), styles["label"])],
    ], colWidths=[55 * mm, 35 * mm], hAlign="LEFT")
    totals.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E5E5E5")), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(totals)

    if invoice.notes:
        story.extend([Spacer(1, 4 * mm), KeepTogether([
            Paragraph(fa("یادداشت"), styles["section_title"]),
            Table([[shaped_paragraph(invoice.notes, styles["value"], 90)]], colWidths=[180 * mm], style=TableStyle([("BOX", (0, 0), (-1, -1), 0.7, colors.black), ("PADDING", (0, 0), (-1, -1), 6)])),
        ])])

    signatures = Table([[
        Paragraph(fa("مهر و امضای خریدار"), styles["section_title"]),
        Paragraph(fa("مهر و امضای فروشنده"), styles["section_title"]),
    ]], colWidths=[90 * mm, 90 * mm], rowHeights=[32 * mm])
    signatures.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 7)]))
    story.extend([Spacer(1, 6 * mm), signatures])

    def page_footer(canvas, document):
        canvas.saveState()
        canvas.setFont(FONT_NAME, 7)
        canvas.drawCentredString(A4[0] / 2, 7 * mm, fa(f"صفحه {persian_digits(document.page)}"))
        canvas.restoreState()

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return buffer.getvalue()

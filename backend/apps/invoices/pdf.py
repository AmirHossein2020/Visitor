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
    PageBreak,
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
    rendered = f"{value:,.2f}".rstrip("0").rstrip(".")
    return fa(f"{rendered} ریال")


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
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def flowables_height(flowables, width):
    """Return the actual vertical space required by a list of flowables."""
    return sum(flowable.wrap(width, A4[1])[1] for flowable in flowables)


def items_table(rows, styles):
    header = [Paragraph(fa(label), styles["label"]) for label in (
        "مبلغ کل", "قیمت واحد", "واحد", "تعداد", "برند", "شرح کالا", "ردیف",
    )]
    table = Table(
        [header, *rows],
        colWidths=[31 * mm, 31 * mm, 18 * mm, 18 * mm, 25 * mm, 47 * mm, 10 * mm],
        repeatRows=1,
        hAlign="RIGHT",
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCDCDC")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def append_paginated_items(story, rows, styles, first_page_space, page_space, ending):
    """Split item rows explicitly while reserving the final invoice block."""
    ending_gap = Spacer(1, 3 * mm)
    ending_height = flowables_height([ending_gap, *ending], 180 * mm)
    remaining = list(rows)
    available = first_page_space

    while remaining:
        complete_table = items_table(remaining, styles)
        if flowables_height([complete_table], 180 * mm) + ending_height <= available:
            story.extend([complete_table, ending_gap, KeepTogether(ending)])
            return

        page_rows = []
        # A final page with several item rows looks intentional and avoids a
        # nearly-empty ending page. Small invoices still retain every possible
        # row with the ending block when they fit on one page.
        final_rows_to_reserve = min(3, len(remaining))
        max_nonfinal_rows = len(remaining) - final_rows_to_reserve
        for count in range(1, max_nonfinal_rows + 1):
            candidate = items_table(remaining[:count], styles)
            if flowables_height([candidate], 180 * mm) > available:
                break
            page_rows = remaining[:count]

        if page_rows:
            story.extend([items_table(page_rows, styles), PageBreak()])
            remaining = remaining[len(page_rows):]
        elif available == page_space:
            # An extraordinarily tall row or ending block cannot be kept on a
            # single A4 page. Let ReportLab split that exceptional content
            # rather than repeatedly inserting empty pages.
            story.extend([complete_table, ending_gap, *ending])
            return
        else:
            story.append(PageBreak())
        available = page_space

    story.extend([items_table([], styles), ending_gap, KeepTogether(ending)])


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
        "title": ParagraphStyle("FaTitle", parent=base["Title"], fontName=FONT_BOLD, fontSize=17, leading=21, alignment=TA_CENTER, textColor=colors.black),
        "seller": ParagraphStyle("FaSeller", parent=base["Heading2"], fontName=FONT_BOLD, fontSize=11, leading=15, alignment=TA_CENTER),
        "section_title": ParagraphStyle("FaSection", parent=base["Heading3"], fontName=FONT_BOLD, fontSize=9, leading=12, alignment=TA_CENTER),
        "label": ParagraphStyle("FaLabel", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=8, leading=11, alignment=TA_RIGHT),
        "value": ParagraphStyle("FaValue", parent=base["BodyText"], fontName=FONT_NAME, fontSize=8, leading=11, alignment=TA_RIGHT),
        "cell": ParagraphStyle("FaCell", parent=base["BodyText"], fontName=FONT_NAME, fontSize=7.5, leading=10, alignment=TA_CENTER),
        "cell_right": ParagraphStyle("FaCellRight", parent=base["BodyText"], fontName=FONT_NAME, fontSize=7.5, leading=10, alignment=TA_RIGHT),
        "small": ParagraphStyle("FaSmall", parent=base["BodyText"], fontName=FONT_NAME, fontSize=8, leading=10, alignment=TA_RIGHT),
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
    header.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story = [header, Spacer(1, 3 * mm)]

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
        Spacer(1, 3 * mm),
    ])

    item_rows = []
    for index, item in enumerate(invoice.items.all(), start=1):
        item_rows.append([
            Paragraph(money(item.line_total), styles["cell"]),
            Paragraph(money(item.unit_price), styles["cell"]),
            shaped_paragraph(item.unit, styles["cell"], 12),
            Paragraph(decimal_text(item.quantity), styles["cell"]),
            shaped_paragraph(item.brand or "—", styles["cell"], 15),
            shaped_paragraph(item.product_name, styles["cell_right"], 25),
            Paragraph(persian_digits(index), styles["cell"]),
        ])
    totals = Table([
        [Paragraph(money(invoice.subtotal), styles["value"]), Paragraph(fa("جمع جزء"), styles["label"])],
        [Paragraph(money(invoice.discount_amount), styles["value"]), Paragraph(fa("تخفیف"), styles["label"])],
        [Paragraph(money(invoice.tax_amount), styles["value"]), Paragraph(fa("مالیات"), styles["label"])],
        [Paragraph(money(invoice.duties_amount), styles["value"]), Paragraph(fa("عوارض"), styles["label"])],
        [Paragraph(money(invoice.final_amount), styles["label"]), Paragraph(fa("مبلغ نهایی"), styles["label"])],
    ], colWidths=[55 * mm, 35 * mm], hAlign="LEFT")
    totals.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#666666")), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E5E5E5")), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    ending = [totals]

    if invoice.notes:
        ending.extend([Spacer(1, 2 * mm),
            Paragraph(fa("یادداشت"), styles["section_title"]),
            Table([[shaped_paragraph(invoice.notes, styles["value"], 90)]], colWidths=[180 * mm], style=TableStyle([("BOX", (0, 0), (-1, -1), 0.7, colors.black), ("PADDING", (0, 0), (-1, -1), 4)])),
        ])

    signatures = Table([[
        Paragraph(fa("مهر و امضای خریدار"), styles["section_title"]),
        Paragraph(fa("مهر و امضای فروشنده"), styles["section_title"]),
    ]], colWidths=[90 * mm, 90 * mm], rowHeights=[25 * mm])
    signatures.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5)]))
    ending.extend([Spacer(1, 3 * mm), signatures])

    prefix_height = flowables_height(story, doc.width)
    append_paginated_items(
        story,
        item_rows,
        styles,
        first_page_space=doc.height - prefix_height,
        page_space=doc.height,
        ending=ending,
    )

    def page_footer(canvas, document):
        canvas.saveState()
        canvas.setFont(FONT_NAME, 7)
        canvas.drawCentredString(A4[0] / 2, 7 * mm, fa(f"صفحه {persian_digits(document.page)}"))
        canvas.restoreState()

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return buffer.getvalue()

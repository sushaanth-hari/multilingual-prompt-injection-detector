from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

def generate_pdf_report(detections: list, stats: dict) -> str:
    os.makedirs("data/reports", exist_ok=True)
    filename = f"data/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    LM = RM = inch
    PW = A4[0] - LM - RM

    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )

    S = getSampleStyleSheet()

    def P(name, **kw):
        return ParagraphStyle(name, parent=S['Normal'], **kw)

    TITLE = P('TI', fontSize=22,
              textColor=colors.HexColor('#1a5cd4'),
              alignment=TA_CENTER,
              fontName='Helvetica-Bold', spaceAfter=4)
    SUB   = P('SU', fontSize=10,
              textColor=colors.HexColor('#6b8cba'),
              alignment=TA_CENTER, spaceAfter=3)
    DATE  = P('DA', fontSize=8,
              textColor=colors.HexColor('#9ab0d0'),
              alignment=TA_CENTER, spaceAfter=16)
    SEC   = P('SE', fontSize=12,
              textColor=colors.HexColor('#1a5cd4'),
              fontName='Helvetica-Bold',
              spaceBefore=16, spaceAfter=7)
    NOTE  = P('NO', fontSize=8,
              textColor=colors.HexColor('#6b8cba'), spaceAfter=5)
    FOOT  = P('FO', fontSize=7,
              textColor=colors.HexColor('#9ab0d0'),
              alignment=TA_CENTER)

    H_BG  = colors.HexColor('#1a5cd4')
    H_BG2 = colors.HexColor('#0d1b3e')
    ROW1  = colors.HexColor('#f0f4ff')
    ROW2  = colors.HexColor('#e4eeff')
    GRID  = colors.HexColor('#c8d8ff')
    WHITE = colors.white

    def tbl(hbg=H_BG):
        return TableStyle([
            ('BACKGROUND',    (0,0), (-1,0),  hbg),
            ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
            ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,0),  9),
            ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',      (0,1), (-1,-1), 8),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('RIGHTPADDING',  (0,0), (-1,-1), 8),
            ('GRID',          (0,0), (-1,-1), 0.4, GRID),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [ROW1, ROW2]),
        ])

    els = []

    # HEADER
    els += [
        Paragraph("InjectionGuard", TITLE),
        Paragraph("Multilingual Prompt Injection Detection Report", SUB),
        Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y  |  %H:%M:%S')}",
            DATE
        ),
        HRFlowable(width="100%", thickness=2,
                   color=H_BG, spaceAfter=12),
    ]

    # SUMMARY
    els.append(Paragraph("Summary Statistics", SEC))
    sd = [
        ['Metric',                 'Value'],
        ['Total Prompts Analyzed', str(stats.get('total_checked', 0))],
        ['Threats Detected',        str(stats.get('injections_found', 0))],
        ['Safe Prompts',            str(stats.get('safe_prompts', 0))],
        ['Languages Detected',      str(len(stats.get('languages_detected', {})))],
    ]
    st = Table(sd, colWidths=[PW*0.65, PW*0.35])
    st.setStyle(tbl())
    els += [st, Spacer(1, 10)]

    # LANGUAGE BREAKDOWN
    langs = stats.get('languages_detected', {})
    if langs:
        els.append(Paragraph("Language Breakdown", SEC))
        total = sum(langs.values()) or 1
        ld = [['Language', 'Count', 'Percentage']]
        for lang, cnt in sorted(langs.items(), key=lambda x: -x[1]):
            ld.append([lang.upper(), str(cnt), f"{cnt/total*100:.1f}%"])
        lt = Table(ld, colWidths=[PW*0.40, PW*0.30, PW*0.30])
        lt.setStyle(tbl(H_BG2))
        els += [lt, Spacer(1, 10)]

    # RISK BREAKDOWN
    rc = stats.get('risk_breakdown', {})
    if rc:
        els.append(Paragraph("Risk Level Breakdown", SEC))
        RCOL = {
            'CRITICAL': colors.HexColor('#e74c3c'),
            'HIGH':     colors.HexColor('#e67e22'),
            'MEDIUM':   colors.HexColor('#f39c12'),
            'LOW':      colors.HexColor('#3498db'),
            'SAFE':     colors.HexColor('#1db954'),
        }
        ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE']
        rd = [['Risk Level', 'Count', 'Indicator']]
        added = []
        for level in ORDER:
            if level in rc:
                rd.append([level, str(rc[level]), '●'])
                added.append(level)
        rt = Table(rd, colWidths=[PW*0.40, PW*0.30, PW*0.30])
        rts = tbl()
        for i, lvl in enumerate(added, 1):
            if lvl in RCOL:
                rts.add('TEXTCOLOR', (2,i),(2,i), RCOL[lvl])
                rts.add('FONTSIZE',  (2,i),(2,i), 14)
        rt.setStyle(rts)
        els += [rt, Spacer(1, 10)]

    # DETECTION HISTORY
    if detections:
        els.append(Paragraph("Detection History", SEC))
        els.append(Paragraph(
            f"Showing {min(len(detections), 50)} most recent entries:",
            NOTE
        ))
        CW = [
            PW * 0.05,
            PW * 0.33,
            PW * 0.08,
            PW * 0.13,
            PW * 0.10,
            PW * 0.31,
        ]
        hd = [['#', 'Prompt', 'Lang', 'Risk', 'Conf', 'Timestamp']]
        for i, d in enumerate(detections[:50], 1):
            raw = d.get('original_text', '')
            txt = (raw[:30] + '…') if len(raw) > 30 else raw
            hd.append([
                str(i),
                txt,
                str(d.get('detected_language', '-')).upper()[:3],
                d.get('risk_level', '-'),
                f"{d.get('confidence', 0):.0f}%",
                str(d.get('timestamp', '-'))[:16],
            ])
        ht = Table(hd, colWidths=CW)
        hts = tbl()
        hts.add('FONTSIZE', (0,0), (-1,0),  8)
        hts.add('FONTSIZE', (0,1), (-1,-1), 7)
        hts.add('ALIGN',    (1,1), (1,-1),  'LEFT')
        hts.add('ALIGN',    (5,1), (5,-1),  'LEFT')
        for i, d in enumerate(detections[:50], 1):
            if d.get('is_injection'):
                hts.add('TEXTCOLOR', (3,i),(3,i),
                        colors.HexColor('#e74c3c'))
                hts.add('FONTNAME',  (3,i),(3,i), 'Helvetica-Bold')
        ht.setStyle(hts)
        els.append(ht)

    # FOOTER
    els += [
        Spacer(1, 20),
        HRFlowable(width="100%", thickness=1,
                   color=GRID, spaceAfter=7),
        Paragraph(
            "Generated by InjectionGuard  —  "
            "Multilingual Prompt Injection Detector",
            FOOT
        )
    ]

    doc.build(els)
    return filename
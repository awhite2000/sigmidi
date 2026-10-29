#!/usr/bin/env python3
"""Build the illustrated user guide from docs/user-manual.md using ReportLab."""
from pathlib import Path
import hashlib
import html
import json
import re

from PIL import Image as PILImage
from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/user-manual.md'
OUTPUT = ROOT / 'output/pdf/sigmidi-foot-controller-0.1-user-manual.pdf'
WIDTH, HEIGHT = A4
MARGIN = 45
CONTENT = WIDTH - 2 * MARGIN
INK = colors.HexColor('#162f32')
TEAL = colors.HexColor('#18786e')
PURPLE = colors.HexColor('#665f9b')
PALE = colors.HexColor('#edf5f1')


def inline(text):
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#126b63">\1</font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return re.sub(r'\[([^]]+)\]\(([^)]+)\)',
                  r'<a href="\2" color="#18786e"><u>\1</u></a>', text)


def signal_path():
    d = Drawing(CONTENT, 100)
    boxes = [(2, 136, 'SIGMIDI', 'BLE MIDI peripheral'),
             (186, 136, 'BLE MIDI dongle', 'Central + DIN output'),
             (370, 132, 'MIDI DEVICE', 'MIDI IN')]
    for x, w, title, sub in boxes:
        d.add(Rect(x, 24, w, 65, rx=8, ry=8, fillColor=PALE,
                   strokeColor=TEAL, strokeWidth=1))
        d.add(String(x+w/2, 63, title, fontName='ManualBold', fontSize=11,
                     textAnchor='middle', fillColor=INK))
        d.add(String(x+w/2, 43, sub, fontName='Manual', fontSize=8.5,
                     textAnchor='middle', fillColor=INK))
    for x, end, label in [(141, 182, 'BLE'), (325, 366, 'DIN')]:
        d.add(Line(x, 58, end-5, 58, strokeColor=PURPLE, strokeWidth=2))
        d.add(Polygon([end, 58, end-7, 62, end-7, 54], fillColor=PURPLE,
                      strokeColor=PURPLE))
        d.add(String((x+end)/2, 74, label, fontName='Manual', fontSize=8,
                     textAnchor='middle', fillColor=PURPLE))
    return d


class Manual(SimpleDocTemplate):
    def afterFlowable(self, item):
        if isinstance(item, Paragraph) and item.style.name == 'Chapter':
            name = item.getPlainText()
            key = 'chapter-' + str(self.page)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(name, key, level=0, closed=False)
            self.chapters.append({'title': name, 'page': self.page})


def main():
    font_dir = Path('/System/Library/Fonts/Supplemental')
    for name, filename in [('Manual', 'Arial.ttf'), ('ManualBold', 'Arial Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily('Manual', normal='Manual', bold='ManualBold',
                                  italic='Manual', boldItalic='ManualBold')
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('Chapter', fontName='ManualBold', fontSize=23, leading=27,
                        textColor=INK, spaceAfter=14, keepWithNext=True))
    s.add(ParagraphStyle('Section', fontName='ManualBold', fontSize=12.5, leading=16,
                        textColor=TEAL, spaceBefore=9, spaceAfter=6, keepWithNext=True))
    s.add(ParagraphStyle('Copy', fontName='Manual', fontSize=10, leading=13.4,
                        textColor=INK, spaceAfter=7))
    s.add(ParagraphStyle('SmallCopy', parent=s['Copy'], fontSize=8.5, leading=11,
                        spaceAfter=5))
    s.add(ParagraphStyle('Cell', parent=s['Copy'], fontSize=9, leading=11.7,
                        spaceAfter=0))
    s.add(ParagraphStyle('Caption', parent=s['Copy'], fontSize=8.2, leading=10.5,
                        textColor=colors.HexColor('#506268'), alignment=TA_CENTER,
                        spaceBefore=4, spaceAfter=7))
    path_diagram = signal_path()
    renderSVG.drawToFile(path_diagram, str(ROOT/'docs/manual-signal-path.svg'))
    story = []
    sections = SOURCE.read_text().split('<!-- page -->')
    images = []
    for page_index, section in enumerate(sections):
        if page_index:
            story.append(PageBreak())
        lines = section.strip().splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith('# '):
                story.append(Paragraph(inline(line[2:]), s['Chapter']))
                i += 1
            elif line.startswith('## '):
                story.append(Paragraph(inline(line[3:]), s['Section']))
                i += 1
            elif line.startswith('!['):
                refs = re.findall(r'!\[([^]]*)\]\(([^)]+)\)', line)
                cells = []
                for caption, relative in refs:
                    if relative == 'manual-signal-path.svg':
                        story.extend([path_diagram, Spacer(1, 5)])
                        continue
                    path = (SOURCE.parent/relative).resolve()
                    images.append(path)
                    w, h = PILImage.open(path).size
                    available = (CONTENT-12)/2 if len(refs) == 2 else CONTENT
                    if len(refs) == 2 and w == 280:
                        available = min(available, 215)
                    if len(refs) == 1 and w == 280:
                        available = 215
                    target_h = available * h/w
                    if page_index == 0:
                        # Keep the whole branded render without clipping its geometry.
                        target_h = min(target_h, 232)
                        available = target_h*w/h
                    group = [Image(str(path), width=available, height=target_h),
                             Paragraph(inline(caption), s['Caption'])]
                    if len(refs) == 2:
                        cells.append(group)
                    else:
                        story.append(KeepTogether(group))
                if cells:
                    table = Table([cells], colWidths=[CONTENT/2]*2)
                    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                                ('LEFTPADDING',(0,0),(-1,-1),3),
                                                ('RIGHTPADDING',(0,0),(-1,-1),3)]))
                    story.append(table)
                i += 1
            elif line.startswith('|'):
                rows = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    cells = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r'[-:]+', v) for v in cells):
                        rows.append(cells)
                    i += 1
                n = len(rows[0])
                # Balance columns by their typical content, not the longest outlier.
                weights = [max(7, sum(min(len(row[c]), 90) for row in rows)/len(rows))**.6
                           for c in range(n)]
                widths = [CONTENT*w/sum(weights) for w in weights]
                if n == 2 and page_index == 0:
                    widths = [CONTENT*.87, CONTENT*.13]
                content = [[Paragraph(('<b>'+inline(v)+'</b>') if j == 0 else inline(v),
                                      s['Cell']) for v in row]
                           for j, row in enumerate(rows)]
                table = Table(content, colWidths=widths, repeatRows=1, hAlign='LEFT')
                table.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,0),PALE),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9f8')]),
                    ('LINEBELOW',(0,0),(-1,0),.8,TEAL),
                    ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d6e1de')),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
                ]))
                story.extend([table, Spacer(1,8)])
            else:
                paragraph = [line]
                i += 1
                numbered = bool(re.match(r'\d+\. ', line))
                while (not numbered and i < len(lines) and lines[i].strip() and
                       not lines[i].startswith(('#','|','!['))):
                    paragraph.append(lines[i].strip())
                    i += 1
                text = ' '.join(paragraph)
                style = s['SmallCopy'] if text.startswith('**[S') else s['Copy']
                story.append(Paragraph(inline(text), style))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Manual(str(OUTPUT), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                 topMargin=49, bottomMargin=43,
                 title='SIGMIDI Foot Controller v0.1 - User manual', author='SIGMIDI project')
    doc.chapters = []

    def page_frame(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(TEAL)
        canvas.rect(0, HEIGHT-7, WIDTH, 7, stroke=0, fill=1)
        canvas.setFont('ManualBold', 8)
        canvas.setFillColor(INK)
        canvas.drawString(MARGIN, HEIGHT-28, 'SIGMIDI  /  FOOT CONTROLLER')
        canvas.setFont('Manual', 8)
        canvas.drawRightString(WIDTH-MARGIN, HEIGHT-28, 'USER MANUAL  v0.1')
        canvas.setStrokeColor(colors.HexColor('#c9d8d3'))
        canvas.line(MARGIN, 32, WIDTH-MARGIN, 32)
        canvas.setFillColor(colors.HexColor('#506268'))
        canvas.drawString(MARGIN, 20, 'Performance Mode  /  Editing Mode  /  MIDI Device')
        canvas.drawRightString(WIDTH-MARGIN, 20, str(_doc.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    # Extra pages indicate accidental overflow of one of the designed page spreads.
    assert len(doc.chapters) == len(sections)
    assert [c['page'] for c in doc.chapters] == list(range(1,len(sections)+1)), doc.chapters
    manifest = {
        'title': 'SIGMIDI Foot Controller v0.1 User manual', 'configuration_schema': 6,
        'pages': len(sections), 'page_size': 'A4', 'preferred_variant': 'Left',
        'source': str(SOURCE.relative_to(ROOT)),
        'pdf': str(OUTPUT.relative_to(ROOT)), 'chapters': doc.chapters,
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'pdf_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'images': {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(set(images))},
        'HX_reference': 'Supplied CC table, cross-checked against official Line 6 sources',
        'BLE_dongle_hardware_tested': False,
        'device_menu_sources': ['src/ui.cpp', 'src/display.cpp', 'src/config.cpp',
                                'src/core.cpp', 'src/counters.cpp', 'web/index.html'],
        'HX_setup_in_appendix_only': True,
    }
    (ROOT/'docs/user-manual-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'pdf':str(OUTPUT),'pages':len(sections)},indent=2))


if __name__ == '__main__':
    main()

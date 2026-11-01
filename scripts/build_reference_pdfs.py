#!/usr/bin/env python3
"""Render the project documentation Markdown that has no designed PDF into output/pdf/reference/.

The assembly guide, bill of materials and user manual have their own generators. The
design/fusion copies of leds, power, printing-tolerances and resistor-ladders differ from
the docs/ versions only in link paths, so only the docs/ versions are rendered. Links to
rendered Markdown point at the matching PDF.
"""
from pathlib import Path
import hashlib
import html
import json
import os
import re
import subprocess

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/reference'
SOURCES = [
    'README.md', 'docs/hardware.md', 'docs/firmware.md', 'docs/bringup.md', 'docs/power.md',
    'docs/leds.md', 'docs/resistor-ladders.md', 'docs/printing-tolerances.md', 'docs/web-flasher.md',
    'docs/device-workflows/README.md', 'design/README.md', 'design/front-panel.md',
    'design/branding/README.md', 'design/electrical/README.md', 'design/kicad/README.md',
    'design/fusion/README.md', 'design/fusion/print/README.md', 'design/fusion/modular/README.md',
    'design/fusion/mirrored/README.md', 'design/fusion/nano-esp32/README.md',
    'design/fusion/archive/README.md', 'distribution/README.md', 'distribution/web-flasher/README.md',
    'flasher/README.md', 'previews/README.md',
]
# Markdown that already has its own PDF.
DESIGNED = {
    'docs/assembly-guide.md': 'output/pdf/sigmidi-foot-controller-0.1-assembly-guide.pdf',
    'docs/bill-of-materials.md': 'output/pdf/sigmidi-foot-controller-0.1-bill-of-materials.pdf',
    'docs/user-manual.md': 'output/pdf/sigmidi-foot-controller-0.1-user-manual.pdf',
}
WIDTH, HEIGHT = A4
MARGIN = 45
CONTENT = WIDTH - 2 * MARGIN
INK = colors.HexColor('#162f32')
TEAL = colors.HexColor('#18786e')
PALE = colors.HexColor('#edf5f1')
GRAY = colors.HexColor('#506268')


def output_for(source):
    """docs/hardware.md -> output/pdf/reference/docs-hardware.pdf; README.md -> readme.pdf."""
    stem = source[:-3].replace('/README', '').replace('/', '-').lower()
    return OUT / (stem + '.pdf')


PDFS = {**{s: output_for(s) for s in SOURCES}, **{s: ROOT / p for s, p in DESIGNED.items()}}


def inline(text, source, output):
    def target(match):
        label, link = match.groups()
        if '://' in link or link.startswith(('#', 'mailto:')):
            href = link
        else:
            path, _, anchor = link.partition('#')
            resolved = (ROOT / source).parent / path
            key = resolved.resolve().relative_to(ROOT).as_posix() if resolved.resolve().is_relative_to(ROOT) else None
            if key in PDFS:
                resolved = PDFS[key]
            href = Path(os.path.relpath(resolved.resolve(), output.parent)).as_posix()
        return '\0' + label + '\1' + href + '\2'
    text = re.sub(r'\[([^]]*)\]\(([^)]+)\)', target, text)
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#126b63">\1</font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return re.sub('\0([^\1]*)\1([^\2]*)\2', r'<a href="\2" color="#18786e"><u>\1</u></a>', text)


def styles():
    font_dir = Path('/System/Library/Fonts/Supplemental')
    for name, filename in [('Manual', 'Arial.ttf'), ('ManualBold', 'Arial Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily('Manual', normal='Manual', bold='ManualBold', italic='Manual', boldItalic='ManualBold')
    copy = ParagraphStyle('Copy', fontName='Manual', fontSize=10, leading=13.4, textColor=INK, spaceAfter=7)
    return {
        'Chapter': ParagraphStyle('Chapter', fontName='ManualBold', fontSize=21, leading=25, textColor=INK,
                                  spaceAfter=12, keepWithNext=True),
        'Section': ParagraphStyle('Section', fontName='ManualBold', fontSize=12.5, leading=16, textColor=TEAL,
                                  spaceBefore=9, spaceAfter=6, keepWithNext=True),
        'Sub': ParagraphStyle('Sub', fontName='ManualBold', fontSize=10.5, leading=14, textColor=INK,
                              spaceBefore=6, spaceAfter=4, keepWithNext=True),
        'Copy': copy,
        'Bullet': ParagraphStyle('Bullet', parent=copy, leftIndent=14, bulletIndent=3, spaceAfter=4),
        'Cell': ParagraphStyle('Cell', parent=copy, fontSize=9, leading=11.7, spaceAfter=0),
        'Caption': ParagraphStyle('Caption', parent=copy, fontSize=8.2, leading=10.5, textColor=GRAY,
                                  alignment=TA_CENTER, spaceBefore=4, spaceAfter=7),
        'Code': ParagraphStyle('Code', fontName='Courier', fontSize=7.6, leading=9.4, textColor=INK,
                               backColor=colors.HexColor('#f4f7f6'), borderPadding=5, spaceBefore=4, spaceAfter=10),
    }


def image(path, caption, s, source, output, pixels=None):
    if path.suffix == '.svg' and path.with_suffix('.png').exists():
        path = path.with_suffix('.png')
    w, h = PILImage.open(path).size
    width = min(CONTENT, (pixels or w) * 0.75)
    height = width * h / w
    if height > 300:
        width, height = width * 300 / height, 300
    group = [Image(str(path), width=width, height=height)]
    if caption:
        group.append(Paragraph(inline(caption, source, output), s['Caption']))
    return KeepTogether(group)


def table(rows, s, source, output):
    n = len(rows[0])
    rows = [row + [''] * (n - len(row)) for row in rows]
    weights = [max(7, sum(min(len(row[c]), 90) for row in rows) / len(rows)) ** .6 for c in range(n)]
    widths = [CONTENT * w / sum(weights) for w in weights]
    cells = [[Paragraph(('<b>' + inline(v, source, output) + '</b>') if j == 0 else inline(v, source, output), s['Cell'])
              for v in row] for j, row in enumerate(rows)]
    t = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PALE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9f8')]),
        ('LINEBELOW', (0, 0), (-1, 0), .8, TEAL), ('LINEBELOW', (0, 1), (-1, -1), .25, colors.HexColor('#d6e1de')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    return [t, Spacer(1, 8)]


def story(source, output, s, images):
    lines = (ROOT / source).read_text().splitlines()
    out, i, title = [], 0, None
    code_chars = int((CONTENT - 10) / (s['Code'].fontSize * 0.6))
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line or line.startswith('<!--'):
            i += 1
        elif line.startswith('```'):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                block.append(lines[i].rstrip())
                i += 1
            i += 1
            out.append(Preformatted('\n'.join(block), s['Code'], maxLineLength=code_chars, newLineChars='  '))
        elif m := re.match(r'(#{1,6}) (.*)', line):
            level = len(m.group(1))
            title = title or m.group(2)
            out.append(Paragraph(inline(m.group(2), source, output), s[['Chapter', 'Section'][level - 1] if level < 3 else 'Sub']))
            i += 1
        elif m := re.match(r'<img src="([^"]+)"', line):
            path = (ROOT / source).parent / m.group(1)
            images.append(path)
            size = re.search(r'width="(\d+)"', line)
            out.append(image(path, '', s, source, output, int(size.group(1)) if size else None))
            i += 1
        elif line.startswith('!['):
            for caption, link in re.findall(r'!\[([^]]*)\]\(([^)]+)\)', line):
                path = ((ROOT / source).parent / link).resolve()
                images.append(path)
                out.append(image(path, caption, s, source, output))
            i += 1
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', v) for v in cells):
                    rows.append(cells)
                i += 1
            out.extend(table(rows, s, source, output))
        elif m := re.match(r'([-*]|\d+\.) (.*)', line):
            item = [m.group(2)]
            i += 1
            while i < len(lines) and lines[i].startswith((' ', '\t')) and lines[i].strip():
                item.append(lines[i].strip())
                i += 1
            bullet = '•' if m.group(1) in '-*' else m.group(1)
            out.append(Paragraph(inline(' '.join(item), source, output), s['Bullet'], bulletText=bullet))
        else:
            paragraph = [line.lstrip('> ')]
            i += 1
            while (i < len(lines) and lines[i].strip() and
                   not re.match(r'(#|\||!\[|```|<|[-*] |\d+\. )', lines[i].strip())):
                paragraph.append(lines[i].strip().lstrip('> '))
                i += 1
            out.append(Paragraph(inline(' '.join(paragraph), source, output), s['Copy']))
    return title or source, out


def render(source, s, images):
    output = output_for(source)
    title, flow = story(source, output, s, images)
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=49,
                            bottomMargin=43, title=f'SIGMIDI Foot Controller v0.1 - {title}', author='SIGMIDI project')

    def frame(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(TEAL)
        canvas.rect(0, HEIGHT - 7, WIDTH, 7, stroke=0, fill=1)
        canvas.setFont('ManualBold', 8)
        canvas.setFillColor(INK)
        canvas.drawString(MARGIN, HEIGHT - 28, 'SIGMIDI  /  FOOT CONTROLLER')
        canvas.setFont('Manual', 8)
        canvas.drawRightString(WIDTH - MARGIN, HEIGHT - 28, source + '  v0.1')
        canvas.setStrokeColor(colors.HexColor('#c9d8d3'))
        canvas.line(MARGIN, 32, WIDTH - MARGIN, 32)
        canvas.setFillColor(GRAY)
        canvas.drawString(MARGIN, 20, title)
        canvas.drawRightString(WIDTH - MARGIN, 20, str(_doc.page))
        canvas.restoreState()

    doc.build(flow, onFirstPage=frame, onLaterPages=frame)
    return {'source': source, 'pdf': str(output.relative_to(ROOT)), 'title': title, 'pages': doc.page,
            'source_sha256': hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
            'pdf_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    s = styles()
    OUT.mkdir(parents=True, exist_ok=True)
    # Every documentation Markdown file is either rendered here, has a designed PDF, or is a
    # link-path copy of a rendered docs/ file.
    copies = {f'design/fusion/{n}.md' for n in ('leds', 'power', 'printing-tolerances', 'resistor-ladders')}
    listed = subprocess.run(['git', 'ls-files', '*.md'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tracked = {name for name in listed.split() if not name.startswith(('managed_components/', 'licenses/'))}
    assert tracked - {'AGENTS.md'} - copies - set(DESIGNED) == set(SOURCES), tracked ^ (set(SOURCES) | copies | set(DESIGNED) | {'AGENTS.md'})
    for copy in copies:
        a = re.sub(r'\]\([^)]*\)', '](...)', (ROOT / copy).read_text())
        b = re.sub(r'\]\([^)]*\)', '](...)', (ROOT / 'docs' / Path(copy).name).read_text())
        assert a == b, copy
    images = []
    documents = [render(source, s, images) for source in SOURCES]
    expected = {output_for(source).name for source in SOURCES}
    for stale in OUT.glob('*.pdf'):
        if stale.name not in expected:
            stale.unlink()
    manifest = {'title': 'SIGMIDI Foot Controller v0.1 reference PDFs', 'page_size': 'A4', 'documents': documents,
                'designed_pdfs': DESIGNED, 'link_path_copies_not_rendered': sorted(copies),
                'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'images': {str(p.resolve().relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(set(images))}}
    (ROOT / 'docs/reference-pdfs-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'pdfs': len(documents), 'pages': sum(d['pages'] for d in documents)}, indent=2))


if __name__ == '__main__':
    main()

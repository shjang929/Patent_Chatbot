"""PDF 좌표를 이용한 단락 복원과 대표도 영역 추출."""
from io import BytesIO
import re

import pdfplumber


def paragraph_text(lines):
    output, previous = [], None
    for line in lines:
        if previous is not None:
            height = max(previous['bottom'] - previous['top'], 1)
            if line['top'] - previous['top'] > height * 1.9:
                output.append('')
        output.append(line['text'])
        previous = line
    return '\n'.join(output)


def extract_layout(pdf_bytes):
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        return [paragraph_text(page.extract_text_lines()) for page in document.pages]


def extract_representative_drawing(pdf_bytes):
    """대표도 표제 아래의 큰 이미지 영역만 선택합니다. 없으면 추측하지 않습니다."""
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        for number, page in enumerate(document.pages[:3], start=1):
            labels = [line for line in page.extract_text_lines()
                      if re.fullmatch(r'대표도(?:\s*[-–]?\s*도\s*\d+)?', re.sub(r'\s+', '', line['text']))]
            for label in labels:
                candidates = [img for img in page.images if img['top'] >= label['bottom'] - 2
                              and img['width'] > 80 and img['height'] > 60]
                if not candidates:
                    continue
                target = min(candidates, key=lambda img: img['top'])
                bbox = (max(0, target['x0'] - 3), max(0, target['top'] - 3),
                        min(page.width, target['x1'] + 3), min(page.height, target['bottom'] + 3))
                buffer = BytesIO()
                page.crop(bbox).to_image(resolution=180).original.save(buffer, format='PNG')
                return {'image': buffer.getvalue(), 'page': number}
    return None

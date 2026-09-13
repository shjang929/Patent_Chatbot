"""한국어 명세서에서 명칭과 비인용 청구항을 규칙으로 추출합니다."""
import re

REFERENCE = re.compile(r'(?:청구\s*항\s*제?\s*\d+|제\s*\d+\s*항)')
HEADING = re.compile(r'^\s*청구\s*항\s*(\d+)\s*$')
FOOTER = re.compile(r'^\s*(?:(?:공개|등록)특허\s+\S+|[-–]\s*\d+\s*[-–])\s*$')


def extract_specification(pages):
    title = ''
    abstract_lines, abstract_pages = [], []
    lines = [(page['page'], line) for page in pages for line in page.get('layout_text', page['text']).splitlines()
             if not FOOTER.match(line)]
    # 공개공보의 (57) 요약 또는 별도 요약서 구역을 읽습니다.
    reading_abstract = False
    for page, line in lines:
        start = re.match(r'^\s*(?:\(57\)\s*요\s*약|요\s*약\s*서)\s*(.*)$', line)
        if start and not reading_abstract:
            reading_abstract = True
            if start.group(1).strip():
                abstract_lines.append(start.group(1))
                abstract_pages.append(page)
            continue
        if reading_abstract:
            compact = re.sub(r'\s+', '', line)
            if (re.match(r'^\s*\(\d+\)', line)
                    or compact.startswith(('대표도', '청구범위', '명세서', '발명의설명'))):
                break
            if compact in ('요약', '[요약]'):
                continue
            abstract_lines.append(line)
            if line.strip() and page not in abstract_pages:
                abstract_pages.append(page)
    for index, (_, line) in enumerate(lines):
        match = re.search(r'\(54\)\s*발명의\s*명칭\s*(.*)', line)
        if match:
            parts = [match.group(1)]
            for _, following in lines[index + 1:]:
                if re.match(r'\s*\(\d+\)', following):
                    break
                parts.append(following)
            title = '\n'.join(parts).strip()
            break
    claims, current, active = [], None, False
    claim_lines = [(p['page'], line) for p in pages
                   for line in p.get('layout_text', p['text']).splitlines()
                   if not FOOTER.match(line)]
    for page, line in claim_lines:
        if re.fullmatch(r'\s*청\s*구\s*범\s*위\s*', line):
            active = True
            continue
        if not active:
            continue
        if re.fullmatch(r'\s*발명(?:의|을\s*실시하기\s*위한)\s*(?:설명|상세한\s*설명|구체적인\s*내용)\s*', line):
            break
        match = HEADING.match(line)
        if match:
            current = {'number': int(match.group(1)), 'lines': [], 'pages': [page]}
            claims.append(current)
        elif current is not None:
            current['lines'].append(line)
            if line.strip() and page not in current['pages']:
                current['pages'].append(page)
    result = []
    for claim in claims:
        text = '\n'.join(claim['lines']).strip()
        if text and not REFERENCE.search(text) and not re.fullmatch(r'삭제[.\s]*', text):
            result.append({'number': claim['number'], 'text': text, 'pages': claim['pages']})
    return {'title': title, 'abstract': '\n'.join(abstract_lines).strip(),
            'abstract_pages': abstract_pages, 'claims': result}

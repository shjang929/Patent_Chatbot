"""원문 단락은 유지하고 PDF 지면의 강제 줄바꿈만 화면에서 풀어 줍니다."""
import html
import re


def reflow_text(text, source_text):
    vocabulary = set(re.findall(r'[가-힣A-Za-z0-9]+', source_text))
    paragraphs = []
    for paragraph in re.split(r'\n\s*\n', text.strip()):
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not lines:
            continue
        combined = lines[0]
        for line in lines[1:]:
            left = re.search(r'[가-힣A-Za-z0-9]+$', combined)
            right = re.match(r'[가-힣A-Za-z0-9]+', line)
            # 같은 문서에 온디바이스/모델을 등이 있으면 단어 중간의 지면 줄바꿈을 복원합니다.
            join_word = left and right and left.group() + right.group() in vocabulary
            combined += ('' if join_word else ' ') + line
        paragraphs.append(combined)
    return '\n\n'.join(paragraphs)


def original_text_html(text, source_text):
    paragraphs = reflow_text(text, source_text).split('\n\n')
    return ''.join('<p style="white-space:normal;word-break:keep-all;overflow-wrap:break-word;line-height:1.8;margin:0 0 1em">'
                   + html.escape(paragraph) + '</p>' for paragraph in paragraphs)

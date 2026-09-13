"""PDF를 페이지 번호와 텍스트 목록으로 변환합니다."""
from io import BytesIO

from pypdf import PdfReader

from config import MAX_PAGES, MAX_PDF_BYTES
from pdf_layout import extract_layout


def extract_pages(pdf_bytes):
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError('PDF는 10MB 이하로 올려 주세요.')
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if reader.is_encrypted:
            raise ValueError('암호가 없는 PDF를 사용해 주세요.')
        if len(reader.pages) > MAX_PAGES:
            raise ValueError(f'PDF는 {MAX_PAGES}페이지 이하로 올려 주세요.')
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            pages.append({'page': number, 'text': page.extract_text() or ''})
    except ValueError:
        raise
    except Exception as error:
        raise ValueError('PDF를 읽지 못했습니다. 정상적인 PDF인지 확인해 주세요.') from error
    if not any(page['text'].strip() for page in pages):
        raise ValueError('추출할 글자가 없습니다. 스캔본 대신 텍스트 PDF를 사용해 주세요.')
    try:
        for page, layout in zip(pages, extract_layout(pdf_bytes)):
            page['layout_text'] = layout
    except Exception:
        # 좌표 분석에 실패해도 기본 텍스트 검색은 유지합니다.
        pass
    return pages

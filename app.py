"""Streamlit 화면: 업로드 → 검색 → 답변 → 근거 확인."""
import base64
import hashlib
import os
from pathlib import Path

import streamlit as st

from chatbot import generate_answer
from pdf_loader import extract_pages
from retriever import build_index, search, split_pages
from claim_extractor import extract_specification
from pdf_layout import extract_representative_drawing
from text_display import original_text_html

ASSETS_DIR = Path(__file__).with_name('assets')
AVATARS = {'assistant': str(ASSETS_DIR / 'assistant_avatar.png'), 'user': str(ASSETS_DIR / 'user_avatar.png')}
NOTE_PATH = Path(__file__).with_name('question_memo.txt')
HERO_BG_PATH = ASSETS_DIR / 'hero_background.jpg'
HERO_BG_B64 = base64.b64encode(HERO_BG_PATH.read_bytes()).decode('ascii') if HERO_BG_PATH.exists() else ''

st.set_page_config(page_title='Patent Chatbot', page_icon='📄', layout='wide')
st.html("""
<link rel="stylesheet" as="style" crossorigin
      href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable.css" />
<style>
:root {
    /* 세련된 느낌의 UI 서체. CDN 로딩에 실패해도 운영체제별 기본 고딕체로
       자연스럽게 대체되도록 폴백을 넉넉히 둡니다. */
    --app-font: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont,
        'Apple SD Gothic Neo', 'Malgun Gothic', 'Segoe UI', system-ui, sans-serif;
}
/* Streamlit은 마크다운/헤더 요소마다 자체 폰트를 다시 지정해두기 때문에
   html, body에만 적용하면 상속이 끊깁니다. 전체 요소에 적용하고,
   Material 아이콘 리거처 폰트만 별도로 다시 지켜줍니다(아래에서 더 높은
   구체성으로 재정의). */
* {
    font-family: var(--app-font) !important;
}
/* stIconMaterial 외에도 stToastDynamicIcon 등 Material 리거처 폰트를 쓰는
   요소가 있어, "Icon"이 들어간 모든 data-testid를 포괄적으로 지켜줍니다. */
[data-testid*="Icon"] {
    font-family: 'Material Symbols Rounded' !important;
}
h1, h2, h3, h4, h5, h6 {
    letter-spacing: -0.02em;
}

/* 비활성 버튼에 마우스를 올렸을 때 브라우저 기본 "금지" 커서(빨간 원)가 뜨는
   것을 막아 경고처럼 보이지 않게 합니다. 대신 버튼의 help 텍스트로
   이유(예: 저장된 기록이 없습니다)를 말풍선으로 안내합니다. */
button:disabled, button:disabled * {
    cursor: help !important;
}
[data-testid="stFileUploaderDropzone"] {
    min-height: 140px; border: 2px dashed #83a7c8; border-radius: 14px;
    background: #f5f9fd; padding: 22px;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: #2563eb; background: #edf5ff; }

.app-title { display: flex; align-items: center; gap: 12px; margin: 0 0 0.3rem 0; }
.app-title-text { font-size: 2.25rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.03em; }
.app-title-icon-wrap {
    position: relative; display: inline-flex; overflow: hidden; border-radius: 50%;
}
.app-title-icon {
    width: 40px; height: 40px; position: relative; z-index: 1; display: block;
}
.app-title-icon-wrap::after {
    content: ''; position: absolute; inset: -6px;
    background: linear-gradient(115deg, transparent 30%, rgba(255,255,255,0.85) 50%, transparent 70%);
    transform: translateX(-120%);
    animation: title-shine 3s ease-in-out infinite;
}
@keyframes title-shine {
    0%, 60% { transform: translateX(-120%); }
    80%, 100% { transform: translateX(120%); }
}

/* Q&A 섹션 제목: 옵션 3(fact_check) 아이콘 + 은은한 부양(float) 효과.
   st.header()와 동일한 글자 크기·굵기(36px / 600)로 맞춰 다른 헤더와 통일감을 줍니다. */
.qa-title { display: flex; align-items: center; gap: 10px; }
.qa-title-text { font-size: 36px; font-weight: 600; line-height: 1.2; letter-spacing: -0.02em; }
.qa-title-icon {
    width: 30px; height: 30px; display: block; flex-shrink: 0;
    animation: title-float 2.6s ease-in-out infinite;
}
@keyframes title-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-6px); }
}

/* 사이드바를 화면 오른쪽으로 이동. Streamlit 사이드바는 메인 콘텐츠와 별개로
   뷰포트에 고정되어 있어 스크롤해도 항상 화면에 보입니다(네이티브 동작, JS 불필요). */
[data-testid="stSidebar"] { order: 1; }

.site-search-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 1.05rem; /* 기존 부제목 대비 약 30% 축소 */
    font-weight: 600;
    color: #0047ab; /* 코발트 블루 */
    margin: 0 0 0.5rem 0;
}
.site-search-badge { width: 20px; height: 20px; flex-shrink: 0; animation: badge-sheen 3.2s ease-in-out infinite; }
@keyframes badge-sheen {
    0%, 100% { filter: brightness(1); }
    50% { filter: brightness(1.3); }
}
[data-testid="stSidebar"] [data-testid="stIconMaterial"] {
    color: #0047ab !important; /* 코발트 블루 */
    fill: #0047ab !important;
}
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
}
/* Note 메모장을 연한 그레이 톤으로 */
[data-testid="stSidebar"] [data-testid="stTextAreaRootElement"] {
    background-color: #eef0f2 !important;
    border-color: #d5d8dc !important;
}
[data-testid="stSidebar"] [data-testid="stTextAreaRootElement"] textarea {
    background-color: #eef0f2 !important;
    color: #333333 !important;
}
[data-testid="stSidebar"] [data-testid="stTextAreaRootElement"] textarea::placeholder {
    color: #8a8f96 !important;
}
</style>""")

# 배경 이미지는 큰 base64 문자열을 담기 때문에 위의 스타일과 별도 블록으로 분리합니다.
st.html(f"""<style>
/* 클래스 선택자 사용: 채팅 입력창이 추가되면 이 요소의 data-testid가
   "stMain"에서 "stAppScrollToBottomContainer"로 바뀌지만 클래스는 stMain으로 유지됩니다. */
.stMain {{
    background-image:
        linear-gradient(180deg, rgba(255,255,255,0.82) 0%, rgba(255,255,255,0.68) 35%, rgba(255,255,255,0.82) 100%),
        url('data:image/jpeg;base64,{HERO_BG_B64}');
    background-size: cover;
    background-position: center top;
    background-repeat: no-repeat;
}}
.st-key-hero-panel {{
    margin-bottom: 0.5rem;
}}
/* 배경 사진 위에 놓이는 글자의 가독성을 위한 흰색 글로우 (하얀 박스 안 글자에는
   영향이 거의 없어 안전합니다). */
.stMain p,
.stMain [data-testid="stCaptionContainer"],
.stMain .app-title-text,
.stMain .qa-title-text {{
    text-shadow: 0 1px 2px rgba(255,255,255,0.85), 0 1px 10px rgba(255,255,255,0.6);
}}
.st-key-summary-card {{
    background: #ffffff;
    border-radius: 18px;
    padding: 1.9rem 2rem 2.2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.12);
    margin-bottom: 1.5rem;
}}
</style>""")

if st.session_state.get('pdf_uploader') is None:
    # 업로드된 PDF가 없는 상태(창을 새로 띄웠을 때 포함, 업로드 파일을 지웠을 때 포함)에서는
    # Note 메모도 함께 비웁니다. 사이드바가 그려지기 전에 처리해야 합니다.
    st.session_state.pop('question_memo', None)
if 'question_memo' not in st.session_state:
    st.session_state.question_memo = ''

with st.sidebar:
    st.markdown(
        '<div class="site-search-title">'
        '<svg class="site-search-badge" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M12 2L19 5V11C19 16 16 19.5 12 21C8 19.5 5 16 5 11V5L12 2Z" fill="#0047ab"/>'
        '<circle cx="11" cy="10.5" r="3.2" stroke="white" stroke-width="1.4"/>'
        '<line x1="13.3" y1="12.8" x2="16" y2="15.5" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '</svg>'
        '특허 원문 검색 사이트</div>',
        unsafe_allow_html=True,
    )
    for name, url in [
        ('KIPRIS', 'https://www.kipris.or.kr/khome/main.do'),
        ('USPTO', 'https://www.uspto.gov/patents/search/patent-public-search'),
        ('Espacenet', 'https://worldwide.espacenet.com/?locale=kr_EP'),
        ('WIPO PATENTSCOPE', 'https://patentscope.wipo.int/search/en/search.jsf'),
    ]:
        with st.container(border=True):
            st.link_button(name, url, icon=':material/open_in_new:', width='stretch')

    st.divider()
    st.markdown(
        '<div class="site-search-title">'
        '<svg class="site-search-badge" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="4" y="3" width="14" height="18" rx="2" fill="#0047ab"/>'
        '<line x1="7" y1="8" x2="15" y2="8" stroke="white" stroke-width="1.3" stroke-linecap="round"/>'
        '<line x1="7" y1="11.5" x2="15" y2="11.5" stroke="white" stroke-width="1.3" stroke-linecap="round"/>'
        '<line x1="7" y1="15" x2="12" y2="15" stroke="white" stroke-width="1.3" stroke-linecap="round"/>'
        '<path d="M15 15.5L20 10.5L21.5 12L16.5 17L14.5 17.5L15 15.5Z" fill="#0047ab" stroke="white" stroke-width="0.8"/>'
        '</svg>'
        'Note</div>',
        unsafe_allow_html=True,
    )
    st.text_area(
        'Note',
        key='question_memo',
        height=160,
        placeholder='자유롭게 기록하세요.',
        label_visibility='collapsed',
    )

    def _save_memo():
        NOTE_PATH.write_text(st.session_state.question_memo, encoding='utf-8')
        try:
            os.startfile(str(NOTE_PATH))  # Windows: 저장과 동시에 메모장으로 바로 열어줍니다.
        except Exception:
            pass
        st.toast(f'메모를 저장했습니다: {NOTE_PATH.name}', icon=':material/save:')

    st.button(
        '파일로 저장',
        icon=':material/save:',
        on_click=_save_memo,
        disabled=not st.session_state.get('question_memo', ''),
        width='stretch',
        key='save_memo_btn',
        help=None if st.session_state.get('question_memo', '') else '저장할 내용이 없습니다.',
    )

with st.container(key='hero-panel'):
    st.markdown(
        '<div class="app-title">'
        '<span class="app-title-icon-wrap">'
        '<svg class="app-title-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="12" cy="12" r="11" fill="#1e3a8a"/>'
        '<path d="M7.5 12.5L10.5 15.5L16.5 9" stroke="white" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
        '</span>'
        '<span class="app-title-text">Hee\'s patent chatbot</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.write('명세서의 주요 내용을 확인하고 궁금한 내용을 질문하세요.')

    uploaded = st.file_uploader(
        'PDF 파일을 폴더에서 아래 영역으로 끌어다 놓으세요',
        type=['pdf'],
        max_upload_size=10,
        key='pdf_uploader',
    )
    st.caption('PDF 한 개 · 최대 10MB / 150페이지 · 클릭해서 선택할 수도 있습니다.')
    if uploaded is None:
        for key in ('document_id', 'index', 'pages', 'messages', 'summary', 'summary_parts', 'summary_error'):
            st.session_state.pop(key, None)
        st.stop()

pdf_bytes = uploaded.getvalue()
document_id = hashlib.sha256(pdf_bytes).hexdigest() + ':layout-v1'
if st.session_state.get('document_id') != document_id:
    # 문서가 바뀌면 이전 문서의 검색 결과와 대화를 비웁니다.
    for key in ('document_id', 'index', 'pages', 'messages', 'summary', 'summary_parts', 'summary_error'):
        st.session_state.pop(key, None)
    try:
        with st.spinner('PDF를 읽고 검색을 준비하고 있습니다...'):
            pages = extract_pages(pdf_bytes)
            index = build_index(split_pages(pages))
        st.session_state.update(document_id=document_id, pages=pages, index=index, messages=[], summary_parts=[], drawing=None)
        try:
            st.session_state.drawing = extract_representative_drawing(pdf_bytes)
        except Exception:
            st.session_state.drawing = None
    except ValueError as error:
        st.error(str(error))
        st.stop()

pages = st.session_state.pages
st.success(f'{len(pages)}페이지 · 검색 준비 완료')
empty_pages = [page['page'] for page in pages if not page['text'].strip()]
if empty_pages:
    st.warning(f'텍스트를 추출하지 못한 페이지: {empty_pages}. 해당 페이지는 검색에서 제외됩니다.')
specification = extract_specification(pages)
source_text = '\n'.join(page['text'] for page in pages)
with st.container(key='summary-card'):
    st.header('발명의 명칭')
    if specification['title']:
        st.write(specification['title'])
    else:
        st.info('발명의 명칭을 찾지 못했습니다. 원문을 확인해 주세요.')
    st.header('요약서 원문')
    if specification['abstract']:
        st.html(original_text_html(specification['abstract'], source_text))
        st.caption('PDF 페이지: ' + ', '.join(map(str, specification['abstract_pages'])))
    else:
        st.info('요약서 구역을 찾지 못했습니다. 원문을 확인해 주세요.')
    st.header('대표도')
    if st.session_state.get('drawing'):
        drawing = st.session_state.drawing
        st.image(drawing['image'], caption=f"대표도 · PDF {drawing['page']}페이지")
    else:
        st.caption('대표도 이미지를 자동으로 찾지 못했습니다.')
    st.header('독립항 원문')
    if not specification['claims']:
        st.warning('독립항을 자동으로 추출하지 못했습니다. 청구범위의 형식을 확인해 주세요.')
    for claim in specification['claims']:
        with st.container(border=True):
            st.subheader(f"청구항 {claim['number']}")
            st.html(original_text_html(claim['text'], source_text))
            st.caption('PDF 페이지: ' + ', '.join(map(str, claim['pages'])))

st.markdown(
    '<div class="qa-title">'
    '<svg class="qa-title-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="4.5" y="3" width="15" height="18" rx="2.2" fill="#0047ab"/>'
    '<rect x="9.3" y="1.2" width="5.4" height="2.6" rx="1" fill="#0047ab"/>'
    '<line x1="8.2" y1="9.2" x2="15.8" y2="9.2" stroke="white" stroke-opacity="0.55" stroke-width="1.3" stroke-linecap="round"/>'
    '<line x1="8.2" y1="13" x2="15.8" y2="13" stroke="white" stroke-opacity="0.55" stroke-width="1.3" stroke-linecap="round"/>'
    '<line x1="8.2" y1="16.8" x2="13.2" y2="16.8" stroke="white" stroke-opacity="0.55" stroke-width="1.3" stroke-linecap="round"/>'
    '<path d="M7.6 12.2L10 14.6L16.4 8.2" stroke="white" stroke-width="2.1" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
    '<span class="qa-title-text">Hee\'s patent에 질문하기</span>'
    '</div>',
    unsafe_allow_html=True,
)
history_exists = bool(st.session_state.messages)
if st.button(
    '질문·답변 기록 지우기',
    icon=':material/ink_eraser:',
    disabled=not history_exists,
    help=None if history_exists else '저장된 기록이 없습니다.',
):
    st.session_state.messages = []
    st.success('질문·답변 기록을 지웠습니다. PDF와 독립항 원문은 유지됩니다.')
st.caption('질문·답변 기록을 지워도 업로드한 PDF와 독립항 원문은 유지됩니다.')


def show_message(message):
    with st.chat_message(message['role'], avatar=AVATARS.get(message['role'])):
        st.markdown(message['content'])
        if message.get('sources'):
            with st.expander('검색된 참고 원문 확인'):
                st.caption('아래는 모델에 전달한 원문입니다. 답변의 인용과 직접 비교하세요.')
                for source in message['sources']:
                    st.markdown(f"**PDF p.{source['page']}**")
                    st.text(source['text'])


for message in st.session_state.messages:
    show_message(message)

question = st.chat_input('예: 이 문서의 배터리 냉각 장치는 어떻게 작동하나요?', max_chars=1000)
if question and question.strip():
    user_message = {'role': 'user', 'content': question}
    show_message(user_message)
    try:
        with st.spinner('관련 원문을 찾아 답변을 작성하고 있습니다...'):
            sources = search(question, st.session_state.index)
            answer = generate_answer(question, sources)
        assistant_message = {'role': 'assistant', 'content': answer, 'sources': sources}
        st.session_state.messages.extend([user_message, assistant_message])
        show_message(assistant_message)
    except ValueError as error:
        st.error(str(error))

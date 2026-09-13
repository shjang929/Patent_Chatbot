# Patent_Chatbot
특허 PDF에서 발명의 명칭과 다른 청구항을 인용하지 않는 독립항 원문을 표시하고, 명세서 내용에 대해 자유롭게 질문할 수 있는 로컬 Streamlit 앱입니다.

## 주요 기능

- 발명의 명칭, 요약서 원문, 독립항 원문과 PDF 페이지 표시
- 대표도 자동 추출
- 질문과 관련된 원문 검색 및 Groq 모델을 통한 답변 생성
- 검색된 참고 원문 확인 및 대화 기록 삭제

## 실행 방법

Python 3.12 환경에서 검증했습니다. Windows PowerShell 기준으로 실행합니다.

```powershell
git clone https://github.com/shjang929/Patent_Chatbot.git
cd Patent_Chatbot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

생성된 `.env`에 본인의 Groq API 키를 입력합니다.

```dotenv
GROQ_API_KEY=본인의_API_키
GROQ_MODEL=openai/gpt-oss-20b
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 표시된 로컬 주소를 열고 특허 PDF를 업로드합니다. 원문 표시는 API 키 없이 가능하며, AI 질문·답변에는 API 키가 필요합니다. 질문·답변 시 질문과 검색된 문서 일부가 Groq API로 전송됩니다.

## 지원 범위

- 텍스트가 포함된 PDF, 최대 10MB·150페이지
- 암호화된 PDF 및 텍스트가 없는 스캔 PDF는 지원하지 않음
- 문서 형식에 따라 제목·독립항·대표도 자동 추출 결과가 달라질 수 있음

## 테스트

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

API 호출은 테스트에서 모의 처리합니다. `.env`, Streamlit 비밀 설정, 임시 파일 및 로컬 샘플 PDF는 Git 업로드 대상에서 제외합니다.

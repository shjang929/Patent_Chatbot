"""Groq 연결 설정. 키는 코드에 직접 적지 않습니다."""
import os

from groq import Groq


def create_client():
    api_key = os.getenv('GROQ_API_KEY', '').strip()
    if not api_key:
        raise ValueError('.env 파일에 GROQ_API_KEY를 입력해 주세요.')
    return Groq(api_key=api_key, timeout=30.0, max_retries=0)


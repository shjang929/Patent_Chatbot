"""프로젝트 전체에서 사용하는 설정."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))

MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 3
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PAGES = 150


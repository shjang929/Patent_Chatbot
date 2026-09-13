from pathlib import Path
from io import BytesIO
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def test_original_claims_without_api(self):
        pages = [{'page': 1, 'text': '(54) 발명의 명칭 시험 장치\n(57) 요약\n청구범위\n청구항 1\n센서를 포함하는 장치.\n청구항 2\n제1항에 있어서, 제어부를 포함하는 장치.\n발명의 설명'}]
        with (patch('streamlit.file_uploader', return_value=BytesIO(b'fixture')),
              patch('pdf_loader.extract_pages', return_value=pages),
              patch('api_client.create_client') as api):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=20)
            self.assertFalse(app.exception)
            self.assertTrue(any(item.value == '청구항 1' for item in app.subheader))
            self.assertFalse(any(item.value == '청구항 2' for item in app.subheader))
            api.assert_not_called()

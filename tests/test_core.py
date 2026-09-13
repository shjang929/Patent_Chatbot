import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pypdf import PdfWriter

from chatbot import generate_answer
from pdf_loader import extract_pages
from retriever import build_index, search, split_pages


class CoreTests(unittest.TestCase):
    def test_page_numbers_survive_search(self):
        pages = [
            {'page': 2, 'text': '배터리 냉각 장치는 냉각수를 순환시켜 온도를 낮춘다.'},
            {'page': 7, 'text': '광학 렌즈는 빛을 굴절시켜 영상을 형성한다.'},
        ]
        results = search('배터리 냉각수', build_index(split_pages(pages)))
        self.assertEqual(results[0]['page'], 2)
        self.assertIn('냉각수', results[0]['text'])

    def test_no_overlap_returns_no_results(self):
        index = build_index(split_pages([{'page': 1, 'text': '배터리 냉각 장치'}]))
        self.assertEqual(search('zzzzzz', index), [])

    def test_chunk_coverage_and_pages(self):
        text = 'abcdefghijklmno'
        chunks = split_pages([{'page': 4, 'text': text}], chunk_size=6, overlap=2)
        self.assertEqual(chunks[0]['text'], 'abcdef')
        self.assertEqual(chunks[-1]['text'], 'mno')
        self.assertTrue(all(chunk['page'] == 4 for chunk in chunks))
        with self.assertRaises(ValueError):
            split_pages([], chunk_size=3, overlap=3)

    def test_blank_and_invalid_pdf(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        data = BytesIO()
        writer.write(data)
        for value in (data.getvalue(), b'not a pdf'):
            with self.assertRaises(ValueError):
                extract_pages(value)

    def test_no_sources_skips_api(self):
        with patch('chatbot.create_client') as client:
            self.assertIn('찾지 못했습니다', generate_answer('질문', []))
            client.assert_not_called()

    def test_api_receives_question_and_page(self):
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='설명 [PDF p.2]'))])
        with patch('chatbot.create_client') as factory:
            factory.return_value.__enter__.return_value = client
            answer = generate_answer('냉각 원리?', [{'page': 2, 'text': '냉각수 순환'}])
        self.assertIn('[PDF p.2]', answer)
        payload = client.chat.completions.create.call_args.kwargs
        self.assertIn('냉각수 순환', payload['messages'][1]['content'])
        self.assertIn('"page": 2', payload['messages'][1]['content'])


if __name__ == '__main__':
    unittest.main()

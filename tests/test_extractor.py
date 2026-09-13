import unittest

from claim_extractor import extract_specification


class ExtractorTests(unittest.TestCase):
    def test_abstract_keeps_text_and_stops_at_drawing(self):
        pages = [{'page': 1, 'text': '(54) 발명의 명칭 장치\n(57) 요 약\n원문 첫 문장.\n두 번째 문장.\n대 표 도\n도1'},
                 {'page': 2, 'text': '청구범위\n청구항 1\n센서 장치.\n발명의 설명'}]
        result = extract_specification(pages)
        self.assertEqual(result['abstract'], '원문 첫 문장.\n두 번째 문장.')
        self.assertEqual(result['abstract_pages'], [1])
        self.assertEqual(result['title'], '장치')
        self.assertEqual(result['claims'][0]['text'], '센서 장치.')

    def test_missing_abstract_does_not_invent_text(self):
        self.assertEqual(extract_specification([{'page': 1, 'text': '다른 내용'}])['abstract'], '')

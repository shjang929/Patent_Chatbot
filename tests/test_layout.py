import unittest
from pdf_layout import paragraph_text


class LayoutTests(unittest.TestCase):
    def test_paragraph_gap_is_distinct_from_wrapped_line(self):
        lines = [{'text': '첫 구성 요소;', 'top': 100, 'bottom': 109},
                 {'text': '두 번째 구성', 'top': 120, 'bottom': 129},
                 {'text': '요소의 이어지는 줄.', 'top': 134, 'bottom': 143}]
        self.assertEqual(paragraph_text(lines), '첫 구성 요소;\n\n두 번째 구성\n요소의 이어지는 줄.')

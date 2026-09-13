import unittest
from text_display import reflow_text, original_text_html


class DisplayTests(unittest.TestCase):
    def test_wrapped_word_and_real_paragraph(self):
        text = '선택된 온디바이\n스에 적용하는 프로세서;\n\n두 번째 구성.'
        self.assertEqual(reflow_text(text, '온디바이스에'), '선택된 온디바이스에 적용하는 프로세서;\n\n두 번째 구성.')

    def test_unknown_boundary_uses_space_and_html_is_escaped(self):
        self.assertEqual(reflow_text('첫 번째\n구성', ''), '첫 번째 구성')
        self.assertNotIn('<script>', original_text_html('<script>', ''))

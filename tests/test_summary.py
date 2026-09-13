import unittest
from types import SimpleNamespace
from unittest.mock import patch

from summarizer import SummaryRateLimit, make_batches, summarize_document, summarize_batch, validate_summary


class SummaryTests(unittest.TestCase):
    def test_truncated_output_splits_and_keeps_page(self):
        def response(reason, content):
            return SimpleNamespace(choices=[SimpleNamespace(finish_reason=reason, message=SimpleNamespace(content=content))])
        with patch('summarizer.create_client') as factory:
            request = factory.return_value.__enter__.return_value.chat.completions.create
            request.side_effect = [response('length', ''), response('stop', '{"sections":[],"claims":[]}'), response('stop', '{"sections":[],"claims":[]}')]
            result = summarize_batch([{'page': 7, 'text': '가' * 800}])
            self.assertEqual(request.call_count, 3)
            self.assertEqual(result, {'sections': [], 'claims': []})
            for call in request.call_args_list:
                refs = call.kwargs['response_format']['json_schema']['schema']['properties']['sections']['items']['properties']['pages']
                self.assertEqual(refs['items']['enum'], [7])

    def test_short_rate_limit_automatically_resumes(self):
        partial = {'sections': [], 'claims': []}
        completed = []
        with patch('summarizer.summarize_batch', side_effect=[SummaryRateLimit(2), partial]) as request, patch('summarizer.time.sleep') as sleep:
            summarize_document([{'page': 1, 'text': '발명'}], completed)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(completed, [partial])

    def test_long_or_repeated_limits_stop(self):
        for seconds, calls in [(120, 1), (None, 1), (1, 3)]:
            with patch('summarizer.summarize_batch', side_effect=SummaryRateLimit(seconds)) as request, patch('summarizer.time.sleep'):
                with self.assertRaises(SummaryRateLimit):
                    summarize_document([{'page': 1, 'text': '발명'}], [])
            self.assertEqual(request.call_count, calls)

    def test_batches_cover_entire_document(self):
        pages = [{'page': 1, 'text': '가나다라마바사' * 10}, {'page': 2, 'text': '마지막 청구항'}]
        batches = make_batches(pages, limit=20)
        for page in pages:
            rebuilt = ''.join(part['text'] for batch in batches for part in batch if part['page'] == page['page'])
            self.assertEqual(rebuilt, page['text'])
        self.assertTrue(all(sum(len(p['text']) for p in b) <= 20 for b in batches))

    def test_invalid_citation_rejected(self):
        value = {'sections': [{'name': '발명의 명칭', 'text': '제목', 'pages': [99]}], 'claims': []}
        with self.assertRaises(ValueError):
            validate_summary(value, {1})

    def test_resume_does_not_repeat_completed_requests(self):
        pages = [{'page': 1, 'text': '가' * 3600}]
        partial = {'sections': [], 'claims': [{'number': 2, 'text': '제1항 인용', 'pages': [1]}]}
        completed = []
        with patch('summarizer.summarize_batch', side_effect=[partial, ValueError('한도')]):
            with self.assertRaises(ValueError):
                summarize_document(pages, completed)
        self.assertEqual(len(completed), 1)
        with patch('summarizer.summarize_batch', return_value={'sections': [], 'claims': []}) as request:
            result = summarize_document(pages, completed)
            request.assert_called_once()
        self.assertEqual(result['claims'][0]['number'], 2)


if __name__ == '__main__':
    unittest.main()

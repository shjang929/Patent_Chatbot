"""외부 API 없이 TF-IDF로 관련 원문을 검색합니다."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import CHUNK_OVERLAP, CHUNK_SIZE, TOP_K


def split_pages(pages, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if not 0 <= overlap < chunk_size:
        raise ValueError('overlap은 0 이상, chunk_size 미만이어야 합니다.')
    chunks = []
    for page in pages:
        text = ' '.join(page['text'].split())
        for start in range(0, len(text), chunk_size - overlap):
            chunks.append({
                'chunk_id': f"p{page['page']}_{start}",
                'page': page['page'],
                'text': text[start:start + chunk_size],
            })
            if start + chunk_size >= len(text):
                break
    return chunks


def build_index(chunks):
    if not chunks:
        raise ValueError('검색할 텍스트가 없습니다.')
    # 문자 조각을 비교하면 한국어 조사 차이에도 일부 대응할 수 있습니다.
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), max_features=50000)
    try:
        matrix = vectorizer.fit_transform([chunk['text'] for chunk in chunks])
    except ValueError as error:
        raise ValueError('검색 인덱스를 만들 만큼 충분한 텍스트가 없습니다.') from error
    return {'chunks': chunks, 'vectorizer': vectorizer, 'matrix': matrix}


def search(question, index, top_k=TOP_K):
    if not question.strip() or top_k <= 0:
        return []
    query = index['vectorizer'].transform([question])
    scores = cosine_similarity(query, index['matrix']).ravel()
    results = []
    for position in scores.argsort()[::-1][:top_k]:
        if scores[position] > 0:
            results.append({**index['chunks'][position], 'score': float(scores[position])})
    return results


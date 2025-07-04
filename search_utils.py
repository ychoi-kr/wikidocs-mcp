import json
import os
import re
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

class BookCache:
    """책 데이터 캐시 관리 클래스"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # 사용자 홈 디렉터리에 캐시 폴더 생성
            home_dir = os.path.expanduser("~")
            cache_dir = os.path.join(home_dir, ".wikidocs_mcp_cache")
        
        self.cache_dir = cache_dir
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except OSError as e:
            # 캐시 디렉터리 생성 실패 시 임시 디렉터리 사용
            import tempfile
            self.cache_dir = tempfile.mkdtemp(prefix="wikidocs_mcp_")
            print(f"Warning: Could not create cache directory at {cache_dir}. Using temporary directory: {self.cache_dir}", file=sys.stderr)
    
    def _get_cache_path(self, book_id: int) -> str:
        """캐시 파일 경로 생성"""
        return os.path.join(self.cache_dir, f"book_{book_id}.json")
    
    def _get_cache_meta_path(self, book_id: int) -> str:
        """캐시 메타데이터 파일 경로 생성"""
        return os.path.join(self.cache_dir, f"book_{book_id}_meta.json")
    
    def is_cache_valid(self, book_id: int, max_age_hours: int = 24) -> bool:
        """캐시가 유효한지 확인"""
        try:
            meta_path = self._get_cache_meta_path(book_id)
            if not os.path.exists(meta_path):
                return False
            
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            cache_time = datetime.fromisoformat(meta.get('cached_at', ''))
            return datetime.now() - cache_time < timedelta(hours=max_age_hours)
        except Exception as e:
            print(f"Warning: Failed to check cache validity for book {book_id}: {e}", file=sys.stderr)
            return False
    
    def save_book_data(self, book_id: int, book_data: Dict[str, Any]) -> None:
        """책 데이터를 캐시에 저장"""
        try:
            cache_path = self._get_cache_path(book_id)
            meta_path = self._get_cache_meta_path(book_id)
            
            # 데이터 저장
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(book_data, f, ensure_ascii=False, indent=2)
            
            # 메타데이터 저장
            meta = {
                'cached_at': datetime.now().isoformat(),
                'total_pages': len(book_data.get('pages', [])),
                'book_subject': book_data.get('subject', ''),
                'checksum': hashlib.md5(json.dumps(book_data, sort_keys=True).encode()).hexdigest()
            }
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to save cache for book {book_id}: {e}", file=sys.stderr)
    
    def load_book_data(self, book_id: int) -> Optional[Dict[str, Any]]:
        """캐시에서 책 데이터 로드"""
        try:
            cache_path = self._get_cache_path(book_id)
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache for book {book_id}: {e}", file=sys.stderr)
            return None


class PageSearcher:
    """페이지 검색 기능 클래스"""
    
    def __init__(self, cache: BookCache):
        self.cache = cache
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화 (검색 최적화)"""
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 특수문자 제거 (일부만)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        # 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower()
    
    def search_pages(self, book_id: int, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """페이지에서 키워드 검색"""
        book_data = self.cache.load_book_data(book_id)
        if not book_data:
            return []
        
        query_normalized = self._normalize_text(query)
        if not query_normalized:
            return []
        
        results = []
        pages = book_data.get('pages', [])
        
        for page in pages:
            score = self._calculate_relevance_score(page, query_normalized)
            if score > 0:
                result = {
                    'id': page.get('id'),
                    'subject': page.get('subject', ''),
                    'content_preview': self._get_content_preview(page.get('content', ''), query),
                    'depth': page.get('depth', 0),
                    'parent_id': page.get('parent_id'),
                    'seq': page.get('seq', 0),
                    'relevance_score': score,
                    'match_type': self._get_match_type(page, query_normalized)
                }
                results.append(result)
        
        # 관련도 순으로 정렬
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:max_results]
    
    def _calculate_relevance_score(self, page: Dict[str, Any], query: str) -> float:
        """관련도 점수 계산"""
        subject = self._normalize_text(page.get('subject', ''))
        content = self._normalize_text(page.get('content', ''))
        
        score = 0.0
        
        # 제목에서 매칭 (가중치 높음)
        if query in subject:
            score += 10.0
            # 완전 일치
            if query == subject:
                score += 5.0
        
        # 내용에서 매칭
        content_matches = content.count(query)
        if content_matches > 0:
            score += content_matches * 2.0
        
        # 키워드 부분 매칭
        query_words = query.split()
        for word in query_words:
            if len(word) > 1:  # 한글자 키워드 제외
                if word in subject:
                    score += 3.0
                score += content.count(word) * 0.5
        
        return score
    
    def _get_match_type(self, page: Dict[str, Any], query: str) -> str:
        """매칭 타입 결정"""
        subject = self._normalize_text(page.get('subject', ''))
        content = self._normalize_text(page.get('content', ''))
        
        if query in subject:
            return "title_match"
        elif query in content:
            return "content_match"
        else:
            return "partial_match"
    
    def _get_content_preview(self, content: str, query: str, context_length: int = 100) -> str:
        """검색어 주변 내용 미리보기 생성"""
        if not content or not query:
            return content[:context_length] + "..." if len(content) > context_length else content
        
        content_clean = self._normalize_text(content)
        query_clean = self._normalize_text(query)
        
        # 검색어 위치 찾기
        index = content_clean.find(query_clean)
        if index == -1:
            return content[:context_length] + "..." if len(content) > context_length else content
        
        # 앞뒤 context_length//2 만큼 추출
        start = max(0, index - context_length // 2)
        end = min(len(content), index + len(query) + context_length // 2)
        
        preview = content[start:end]
        
        # 앞뒤에 ... 추가
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
        
        return preview
    
    def get_book_structure(self, book_id: int, max_depth: int = 2) -> List[Dict[str, Any]]:
        """책 구조 요약 (목차 형태)"""
        book_data = self.cache.load_book_data(book_id)
        if not book_data:
            return []
        
        pages = book_data.get('pages', [])
        structure = []
        
        for page in pages:
            depth = page.get('depth', 0)
            if depth <= max_depth:
                structure.append({
                    'id': page.get('id'),
                    'subject': page.get('subject', ''),
                    'depth': depth,
                    'parent_id': page.get('parent_id'),
                    'seq': page.get('seq', 0),
                    'has_content': bool(page.get('content', '').strip())
                })
        
        return structure
    
    def get_cache_info(self, book_id: int) -> Dict[str, Any]:
        """캐시 정보 반환"""
        try:
            meta_path = self.cache._get_cache_meta_path(book_id)
            if not os.path.exists(meta_path):
                return {"cached": False}
            
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            return {
                "cached": True,
                "cached_at": meta.get('cached_at'),
                "total_pages": meta.get('total_pages', 0),
                "book_subject": meta.get('book_subject', ''),
                "is_valid": self.cache.is_cache_valid(book_id)
            }
        except Exception as e:
            print(f"Warning: Failed to get cache info for book {book_id}: {e}", file=sys.stderr)
            return {"cached": False}


# 전역 인스턴스 (지연 초기화)
_book_cache = None
_page_searcher = None

def get_book_cache() -> BookCache:
    """북 캐시 인스턴스 반환"""
    global _book_cache
    if _book_cache is None:
        _book_cache = BookCache()
    return _book_cache

def get_page_searcher() -> PageSearcher:
    """페이지 검색기 인스턴스 반환"""
    global _page_searcher
    if _page_searcher is None:
        _page_searcher = PageSearcher(get_book_cache())
    return _page_searcher
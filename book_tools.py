from typing import Dict, Any, List
from utils import make_api_request, put_page, upload_image, flatten_pages
from search_utils import get_book_cache, get_page_searcher

def register_book_tools(mcp_server):
    """책 관련 도구들을 MCP 서버에 등록"""
    
    @mcp_server.tool(
        name="list_my_books",
        description="사용자 본인이 작성한 모든 위키독스 책 목록을 조회합니다."
    )
    async def list_my_books() -> Dict[str, Any]:
        """/napi/books : 본인이 작성한 책을 조회합니다."""
        result = await make_api_request("GET", "/books/")
        if "error" in result:
            return result
        return {"books": result, "total_count": len(result)}

        
    @mcp_server.tool(
        name="get_book_info",
        description="특정 책의 기본 정보(제목, 요약, 페이지 수)와 모든 페이지 데이터를 조회합니다. 항상 최신 데이터를 가져오려고 시도하며, API 요청이 실패할 경우에만 캐시를 사용합니다. 이후 검색이나 구조 분석 도구를 사용하기 위해 필요한 첫 번째 단계입니다."
    )
    async def get_book_info(book_id: int) -> Dict[str, Any]:
        """/napi/books/{book_id} : 책을 조회하고 캐시에 저장합니다."""
        cache = get_book_cache()
        
        # 먼저 API에서 최신 데이터 가져오기 시도
        book_data = await make_api_request("GET", f"/books/{book_id}/")
        
        if "error" not in book_data:
            # API 요청 성공 시 캐시에 저장
            cache.save_book_data(book_id, book_data)
            flat_pages = flatten_pages(book_data.get("pages", []))
            
            return {
                "book_id": book_id,
                "subject": book_data.get("subject", ""),
                "summary": book_data.get("summary", ""),
                "total_pages": len(flat_pages),
                "status": "ready",
                "data_source": "api"
            }
        
        # API 요청 실패 시 캐시 사용 시도
        cached_data = cache.load_book_data(book_id)
        if cached_data:
            flat_pages = flatten_pages(cached_data.get("pages", []))
            cache_info = get_page_searcher().get_cache_info(book_id)
            
            return {
                "book_id": book_id,
                "subject": cached_data.get("subject", ""),
                "summary": cached_data.get("summary", ""),
                "total_pages": len(flat_pages),
                "status": "ready",
                "data_source": "cache",
                "cached_at": cache_info.get("cached_at"),
                "warning": "API 요청이 실패하여 캐시된 데이터를 사용했습니다."
            }
        
        # API 실패 + 캐시 없음 = 완전 실패
        return {
            "error": book_data.get("error", "Unknown error"),
            "message": book_data.get("message", "API 요청이 실패했고 캐시된 데이터도 없습니다."),
            "book_id": book_id
        }


    @mcp_server.tool(
        name="search_book_pages",
        description="책의 페이지에서 키워드를 검색합니다. 제목과 내용을 모두 검색하며, 관련도가 높은 순으로 결과를 반환합니다."
    )
    async def search_book_pages(
        book_id: int, 
        query: str, 
        max_results: int = 20
    ) -> Dict[str, Any]:
        """책 페이지에서 키워드 검색"""
        if not query.strip():
            return {"error": "검색어를 입력해주세요."}
        
        searcher = get_page_searcher()
        cache = get_book_cache()
        
        # 캐시 확인, 없으면 API에서 가져오기
        cache_info = searcher.get_cache_info(book_id)
        if not cache_info.get("cached"):
            # API에서 책 데이터 가져오기
            book_data = await make_api_request("GET", f"/books/{book_id}/")
            if "error" in book_data:
                return book_data
            
            # 캐시에 저장
            cache.save_book_data(book_id, book_data)
        
        # 검색 실행
        results = searcher.search_pages(book_id, query, max_results)
        
        # 최신 캐시 정보 가져오기
        cache_info = searcher.get_cache_info(book_id)
        
        return {
            "query": query,
            "book_id": book_id,
            "book_subject": cache_info.get("book_subject", ""),
            "total_matches": len(results),
            "results": results
        }


    @mcp_server.tool(
        name="get_book_structure",
        description="책의 목차 구조를 간단히 요약합니다. 대량의 페이지가 있는 책에서 전체 구조를 파악할 때 유용합니다."
    )
    async def get_book_structure(book_id: int, max_depth: int = 2) -> Dict[str, Any]:
        """책의 구조 요약"""
        searcher = get_page_searcher()
        cache = get_book_cache()
        
        # 캐시 확인, 없으면 API에서 가져오기
        cache_info = searcher.get_cache_info(book_id)
        if not cache_info.get("cached"):
            # API에서 책 데이터 가져오기
            book_data = await make_api_request("GET", f"/books/{book_id}/")
            if "error" in book_data:
                return book_data
            
            # 캐시에 저장
            cache.save_book_data(book_id, book_data)
        
        # 구조 추출
        structure = searcher.get_book_structure(book_id, max_depth)
        
        # 최신 캐시 정보 가져오기
        cache_info = searcher.get_cache_info(book_id)
        
        return {
            "book_id": book_id,
            "book_subject": cache_info.get("book_subject", ""),
            "total_pages": cache_info.get("total_pages", 0),
            "max_depth": max_depth,
            "structure": structure
        }


    @mcp_server.tool(
        name="get_cache_status",
        description="책 캐시 상태를 확인합니다. 어떤 책이 캐시되어 있는지, 언제 캐시되었는지 확인할 수 있습니다."
    )
    async def get_cache_status(book_id: int) -> Dict[str, Any]:
        """캐시 상태 확인"""
        searcher = get_page_searcher()
        cache_info = searcher.get_cache_info(book_id)
        
        return {
            "book_id": book_id,
            "cache_info": cache_info
        }


    @mcp_server.tool(
        name="get_page",
        description="주어진 페이지 ID로 페이지를 조회합니다."
    )
    async def get_page(page_id: int) -> Dict[str, Any]:
        """/napi/pages/{page_id} : 페이지를 조회합니다."""
        return await make_api_request("GET", f"/pages/{page_id}/")


    @mcp_server.tool(
        name="create_page",
        description="책(book_id)에 속하는 새 페이지를 생성합니다. 제목(subject), 내용(content)은 필수이며, 상위 페이지 ID(parent_id)와 공개 여부(open_yn)는 옵션입니다."
    )
    async def create_page(
        book_id: int, 
        subject: str, 
        content: str, 
        parent_id: int = 0,
        open_yn: str = "Y"
    ) -> Dict[str, Any]:
        """새 페이지를 생성"""
        new_page_data = {
            "id": 0,  # 없으면 오류 발생하므로 생략하지 말 것
            "subject": subject,
            "content": content,
            "parent_id": parent_id,
            "depth": 0,
            "seq": 0,
            "book_id": book_id,
            "open_yn": open_yn
        }
        result = await put_page(page_id=-1, data=new_page_data)
        
        # 성공 시 캐시 무효화 (다음 조회 시 새로 로드)
        if not result.get("error"):
            get_book_cache().invalidate_book(book_id)
        
        return result


    @mcp_server.tool(
        name="update_page",
        description=(
            "위키독스 페이지를 수정합니다. "
            "`page_id`는 필수입니다. "
            "제목(`subject`), 내용(`content`), 부모 페이지 ID(`parent_id`), 또는 공개 여부(`open_yn`, Y 또는 N) 중 하나 이상을 반드시 전달해야 합니다. "
            "`old_str`/`new_str` 매개변수는 지원되지 않습니다. 전체 `content`를 전달하세요. "
            "생략된 필드는 서버에 저장된 기존 값을 그대로 사용하게 됩니다."
        )
    )

    async def update_page(
        page_id:   int,
        subject:   str | None = None,
        content:   str | None = None,
        parent_id: int | None = None,
        open_yn:   str | None = None,
    ) -> dict[str, Any]:
        """
        PUT /napi/pages/{page_id}/
    
        Workflow
        --------
        1. GET 현재 페이지 → diff 계산
        2. current 복사 후 전달된 파라미터만 덮어써 updated 생성
           (→ 결과적으로 **모든 필드**가 포함된 완전한 페이로드)
        3. 변경 사항 없으면 {"error": "NO_CHANGES"} 반환
        4. 성공 시 캐시 무효화 + updated_fields 리스트 반환
    
    
        Notes
        -----
        - 미전달 필드는 **기존 값으로 채워져** 서버에 그대로 남습니다.
        - 파라미터를 하나도 바꾸지 않으면 PUT 호출을 생략해 네트워크 트래픽을 절약합니다.
        """

        # 1) 현재 상태 조회
        current = await make_api_request("GET", f"/pages/{page_id}/")
        if "error" in current:
            return current        # 404·권한 오류 등 그대로 반환
    
       # 2) diff → payload 만들기
        payload = {
            "id":        page_id,                 # 필수
            "subject":   subject   if subject   is not None else current["subject"],
            "content":   content   if content   is not None else current["content"],
            "parent_id": parent_id if parent_id is not None else current["parent_id"],
            "open_yn":   open_yn   if open_yn   is not None else current["open_yn"],
            "book_id":   current["book_id"],      # 명세상 필요 (0 으로 줘도 되지만 안전하게)
        }
     
        delta_fields = [
            k for k in ("subject", "content", "parent_id", "open_yn")
            if payload[k] != current[k]
        ]

        if not delta_fields:
            return {
                "error": "NO_CHANGES",
                "message": "변경된 값이 없습니다. 수정할 항목을 하나 이상 넣어 주세요."
            }
    
        # 3) PUT
        result = await put_page(page_id, payload)
    
        # 4) 캐시 무효화
        if "error" not in result:
            get_book_cache().invalidate_book(current["book_id"])
    
        # 5) 바뀐 필드 정보 반환 (UX 용)
        result["updated_fields"] = delta_fields
        return result


    @mcp_server.tool(
        name="upload_page_image",
        description="페이지용 이미지를 업로드합니다. page_id와 이미지 파일 경로(file_path)가 필요합니다."
    )
    async def upload_page_image(page_id: int, file_path: str) -> Dict[str, Any]:
        """페이지용 이미지를 업로드"""
        data = {'page_id': page_id}
        return await upload_image("/images/upload/", file_path, data)


    @mcp_server.tool(
        name="get_wikidocs_formatting_guide",
        description="위키독스 책 페이지 작성을 위한 마크다운 포매팅 가이드를 조회합니다. 책 페이지를 생성하거나 수정하기 전에 이 가이드를 참조하세요."
    )
    async def get_wikidocs_formatting_guide() -> str:
        """위키독스 책 페이지 포매팅 가이드를 반환"""
        return """# 위키독스 책 페이지 포매팅 가이드

## 🚨 핵심 주의사항

### 1. 헤딩 규칙 (매우 중요!)
- 내용 작성 시 **H1 태그 사용 금지!** → H2(##) 또는 H3(###)부터 시작
- 이유: H1은 전자책 변환 시 자동으로 챕터로 인식됨
- H2에는 자동으로 밑줄이 적용됨
- 계층 구조: `## → ### → ####` 순서로 사용
- 페이지 제목을 첫 번째 줄에 작성할 경우 제목이 중복으로 표시되므로, 페이지 제목 없이 페이지 도입부 또는 섹션 제목으로 내용을 시작하는 것이 좋습니다.

### 2. 리스트 작성 규칙
- **본문 뒤 리스트 작성 시 반드시 공백 한 줄 삽입**
```
본문 내용입니다.

- 리스트 항목 1
- 리스트 항목 2
```

- **중첩 리스트**: 하위 항목은 4칸 들여쓰기
```
- 상위 항목
    - 하위 항목 (4칸 들여쓰기)
    - 하위 항목 2
```

### 3. 코드 블록 규칙
**본문 뒤 코드 블록 작성 시 반드시 공백 한 줄 삽입**

**일반 코드**: 백쿼트 3개 또는 4칸 들여쓰기

```python
# 일반 코드 블록
def example():
    return "hello"
```

**⚠️ 리스트 내 코드**: 백쿼트 불가! 반드시 8칸 들여쓰기

```
- 설명
        # 리스트 내 코드는 8칸 들여쓰기만 가능
        def list_code():
            return "example"
```

### 4. 그 밖의 특이 사항
- 물결표(tilde)가 일반 문자열로 인식되므로 앞에 백슬래시를 넣지 마세요.
- 특수 기호(볼드체를 위한 asterisk, 이스케이프를 뜻하는 백슬래시 등)를 실수로 이스케이프하여 렌더링 결과에 그대로 노출하지 않게 유의하세요.


## 🎨 위키독스 전용 특수 기능

**팁 블록**

[[TIP]]
**팁 블록에 대하여**

도움말이나 팁을 설명하는 블록을 작성할 수 있습니다.  
팁 블록 위의 섹션 제목과 팁 블록 사이에 적절한 맥락을 제공해야 구조적으로 어색하지 않습니다.
팁 블록 내에서는 일부 마크다운 렌더링이 작동하지 않습니다. 예를 들어, 팁 블록 제목은 **굵은 글씨**로 표시하세요.
[[/TIP]]

**사용자 정의 팁 블록**

[[TIP("알아두기")]]
**팁 블록에 대하여**

도움말이나 팁을 설명하는 블록을 작성할 수 있습니다.
[[/TIP]]

**목차 자동생성 (해당 위치에 목차가 생성됨. 가급적 처음 제목이 나오기 전에 넣는 것이 구조상 논리적임)**

[TOC]

**코드 블록 내 강조**

```python
def sum(a, b):
    [[MARK]]return a+b[[/MARK]]
```

**코드 블록 내 삭제 표시**

```python
def sum(a, b):
    [[SMARK]]return a+b[[/SMARK]]
```

**용어 링크**

[["용어명"]]


## 🖼️ 이미지 처리
- **기본**: `![alt텍스트](이미지URL)`
- **가운데 정렬**:
```html
<p align="center">
<img src="이미지URL" alt="설명">
</p>
```
- **⚠️ 전자책 판매용**: img 태그 사용 금지 (PDF 호환성 문제)

## 🧮 수식 표현 (MathJax)
- **블록 수식**: `$$수식$$`
- **인라인 수식**: `$수식$` (⚠️ 공백 없이! 매우 중요)
- **줄바꿈**: `\\\\` 사용
- **정렬**: `\\begin{aligned}` 환경 활용

### 수식 예시
```
$$
\\begin{aligned}
f(x) &= ax^2 + bx + c \\\\
&= a(x + \\frac{b}{2a})^2 + c - \\frac{b^2}{4a}
\\end{aligned}
$$
```

## 📺 미디어 삽입
### 유튜브 동영상
```html
<style>.embed-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; } .embed-container iframe, .embed-container object, .embed-container embed { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }</style><div class='embed-container'><iframe src='https://www.youtube.com/embed/동영상ID' frameborder='0' allowfullscreen></iframe></div>
```

## ✅ 체크리스트

책 페이지 작성 전 반드시 확인:
- [ ] H1 태그 사용하지 않았는가?
- [ ] 본문 뒤 리스트에 공백 한 줄 넣었는가?
- [ ] 리스트 내 코드를 8칸 들여쓰기로 작성했는가?
- [ ] 수식에서 $ 기호 앞뒤에 공백을 넣지 않았는가?
- [ ] 전자책용이면 HTML 태그를 피했는가?

이 가이드를 따라야 위키독스에서 올바르게 렌더링됩니다!"""



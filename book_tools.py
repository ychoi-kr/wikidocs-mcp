from typing import Dict, Any, List
from utils import make_api_request, put_page, upload_image
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
        description="책을 조회하고 로컬 캐시에 저장합니다. 대량의 페이지 데이터를 효율적으로 처리하기 위해 캐시를 사용합니다."
    )
    async def get_book_info(book_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """/napi/books/{book_id} : 책을 조회하고 캐시에 저장합니다."""
        cache = get_book_cache()
        
        # 캐시 확인
        if not force_refresh and cache.is_cache_valid(book_id):
            cached_data = cache.load_book_data(book_id)
            if cached_data:
                return {
                    "message": "캐시에서 로드됨",
                    "book_id": book_id,
                    "subject": cached_data.get("subject", ""),
                    "total_pages": len(cached_data.get("pages", [])),
                    "cached": True,
                    "tip": "페이지 검색을 위해 search_book_pages 도구를 사용하세요."
                }
        
        # API에서 데이터 가져오기
        book_data = await make_api_request("GET", f"/books/{book_id}/")
        if "error" in book_data:
            return book_data
        
        # 캐시에 저장
        cache.save_book_data(book_id, book_data)
        
        return {
            "message": "책 정보를 성공적으로 가져와서 캐시에 저장했습니다.",
            "book_id": book_id,
            "subject": book_data.get("subject", ""),
            "total_pages": len(book_data.get("pages", [])),
            "cached": True,
            "tip": "이제 search_book_pages 도구로 특정 키워드를 검색할 수 있습니다."
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
        
        # 캐시 확인
        cache_info = searcher.get_cache_info(book_id)
        if not cache_info.get("cached"):
            return {
                "error": "책 데이터가 캐시되지 않았습니다. 먼저 get_book_info 도구를 사용하여 책 정보를 로드해주세요."
            }
        
        # 검색 실행
        results = searcher.search_pages(book_id, query, max_results)
        
        return {
            "query": query,
            "book_id": book_id,
            "book_subject": cache_info.get("book_subject", ""),
            "total_matches": len(results),
            "results": results,
            "tip": "특정 페이지의 전체 내용을 보려면 get_page 도구를 사용하세요."
        }

    @mcp_server.tool(
        name="get_book_structure",
        description="책의 목차 구조를 간단히 요약합니다. 대량의 페이지가 있는 책에서 전체 구조를 파악할 때 유용합니다."
    )
    async def get_book_structure(book_id: int, max_depth: int = 2) -> Dict[str, Any]:
        """책의 구조 요약"""
        searcher = get_page_searcher()
        
        # 캐시 확인
        cache_info = searcher.get_cache_info(book_id)
        if not cache_info.get("cached"):
            return {
                "error": "책 데이터가 캐시되지 않았습니다. 먼저 get_book_info 도구를 사용하여 책 정보를 로드해주세요."
            }
        
        structure = searcher.get_book_structure(book_id, max_depth)
        
        return {
            "book_id": book_id,
            "book_subject": cache_info.get("book_subject", ""),
            "total_pages": cache_info.get("total_pages", 0),
            "max_depth": max_depth,
            "structure": structure,
            "tip": "더 자세한 내용은 search_book_pages나 get_page 도구를 사용하세요."
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
            "위키독스 page_id 페이지의 제목(subject), 내용(content), 부모 페이지 ID(parent_id), 또는 공개 여부(open_yn, Y 또는 N)를 수정합니다. "
            "수정하고 싶은 필드들만 전달해 호출하면 되며, 생략된 필드는 서버에 저장된 기존 값을 그대로 사용합니다."
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

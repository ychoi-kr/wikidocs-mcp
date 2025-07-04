import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()

# --- API 설정 ---
WIKIDOCS_API_URL = "https://wikidocs.net/napi"
API_TOKEN = os.getenv("WIKIDOCS_API_TOKEN")

# --- MCP 서버 인스턴스 생성 ---
mcp_server = FastMCP(
    name="Wikidocs Enhanced Server",
    instructions="""이 서버는 위키독스 책과 블로그 콘텐츠를 조회하고 수정하는 기능을 제공합니다.

중요 사용 가이드:
- 책에 새 페이지를 추가할 때는 `create_page`를 사용하고, `update_page`는 기존 페이지를 수정할 때만 사용하세요.
- `create_page` 사용 도중에 출력이 중단되는 경우, 임의의 페이지 ID로 `update_page`를 시도해서는 안 됩니다.
- 존재하지 않거나 알지 못하는 페이지 ID에 대해 `update_page`를 절대 사용하지 마세요.

참고:
- 책의 페이지 ID는 책 내에서뿐 아니라 위키독스에서 글로벌하게 고유합니다."""
)

# --- 유틸리티 함수 ---
async def _make_api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """위키독스 API 요청을 처리하는 공통 함수"""
    if not API_TOKEN:
        return {"error": "API 토큰이 설정되지 않았습니다."}
    
    headers = {"Authorization": f"Token {API_TOKEN}"}
    
    try:
        async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
            if method.upper() == "GET":
                response = await client.get(endpoint)
            elif method.upper() == "PUT":
                response = await client.put(endpoint, json=data)
            elif method.upper() == "POST":
                response = await client.post(endpoint, json=data)
            else:
                return {"error": f"지원되지 않는 HTTP 메소드: {method}"}
            
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": "Not Found", "message": f"요청한 리소스를 찾을 수 없습니다."}
        elif e.response.status_code == 422:
            return {"error": "Unprocessable Content", "message": "요청 데이터가 잘못되었습니다."}
        else:
            return {"error": f"HTTP Error {e.response.status_code}", "message": str(e)}
    except Exception as e:
        return {"error": "Request Failed", "message": str(e)}

async def _put_page(page_id: int, data: Dict[str, Any]) -> dict:
    """/napi/pages/{page_id} : 페이지를 수정합니다. (신규 페이지 등록인 경우에는 page_id 에 -1 설정)"""
    data['depth'] = 0
    data['seq'] = 0
    return await _make_api_request("PUT", f"/pages/{page_id}/", data)

# === 기본 도구들 (책 목록을 도구로도 제공) ===

@mcp_server.tool(
    name="list_my_books",
    description="사용자 본인이 작성한 모든 위키독스 책 목록을 조회합니다."
)
async def list_my_books() -> Dict[str, Any]:
    """/napi/books : 본인이 작성한 책을 조회합니다."""
    result = await _make_api_request("GET", "/books/")
    if "error" in result:
        return result
    return {"books": result, "total_count": len(result)}


@mcp_server.tool(
    name="get_book_info",
    description="책을 조회합니다. 책에 속한 페이지 목록이 함께 조회됩니다. 단, 페이지가 많을 경우 완전한 목록을 제공하지 못할 수 있습니다."
)
async def get_book_info(book_id: int) -> Dict[str, Any]:
    """/napi/books/{book_id} : 책을 조회합니다. 책에 속해 있는 모든 페이지가 함께 조회됩니다."""
    return await _make_api_request("GET", f"/books/{book_id}/")


@mcp_server.tool(
    name="get_page",
    description="주어진 페이지 ID로 페이지를 조회합니다. "
)
async def get_page(page_id: int) -> Dict[str, Any]:
    """/napi/pages/{page_id} : 페이지를 조회합니다."""
    return await _make_api_request("GET", f"/pages/{page_id}/")


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
        "id": 0,
        "subject": subject,
        "content": content,
        "parent_id": parent_id,
        "depth": 0,
        "seq": 0,
        "book_id": book_id,
        "open_yn": open_yn
    }
    return await _put_page(page_id=-1, data=new_page_data)


@mcp_server.tool(
    name="update_page",
    description="페이지(page_id)의 제목(subject), 내용(content), 상위 페이지(parent_id), 공개 여부(open_yn)를 수정합니다."
)
async def update_page(
    page_id: int, 
    subject: str, 
    content: str, 
    parent_id: int, 
    open_yn: str
) -> Dict[str, Any]:
    """페이지 내용을 수정"""
    update_data = {
        "id": page_id,
        "subject": subject,
        "content": content,
        "parent_id": parent_id,
        "book_id": 0,
        "open_yn": open_yn
    }
    return await _put_page(page_id=page_id, data=update_data)

# === 블로그 도구들 ===

@mcp_server.tool(
    name="get_blog_profile",
    description="블로그 프로필 정보를 조회합니다."
)
async def get_blog_profile() -> Dict[str, Any]:
    """블로그 프로필 정보를 반환"""
    return await _make_api_request("GET", "/blog/profile/")

@mcp_server.tool(
    name="get_blog_list",
    description="블로그 포스트 목록을 페이지별로 조회합니다. page 번호를 지정할 수 있습니다 (기본값: 1)."
)
async def get_blog_list(page: int = 1) -> Dict[str, Any]:
    """블로그 포스트 목록을 반환"""
    return await _make_api_request("GET", f"/blog/list/{page}")

@mcp_server.tool(
    name="get_blog_post",
    description="특정 블로그 포스트 ID의 내용을 조회합니다."
)
async def get_blog_post(blog_id: int) -> Dict[str, Any]:
    """특정 블로그 포스트 내용을 반환"""
    return await _make_api_request("GET", f"/blog/{blog_id}")

@mcp_server.tool(
    name="create_blog_post",
    description="새 블로그 포스트를 생성합니다. 제목(title), 내용(content)은 필수이며, 공개 여부(is_public)와 태그(tags)는 옵션입니다."
)
async def create_blog_post(
    title: str,
    content: str,
    is_public: bool = True,
    tags: str = ""
) -> Dict[str, Any]:
    """새 블로그 포스트를 생성"""
    blog_data = {
        "title": title,
        "content": content,
        "is_public": is_public,
        "tags": tags
    }
    return await _make_api_request("POST", "/blog/create/", blog_data)

@mcp_server.tool(
    name="update_blog_post",
    description="기존 블로그 포스트를 수정합니다. 블로그 ID(blog_id), 제목(title), 내용(content), 공개 여부(is_public), 태그(tags)를 지정할 수 있습니다."
)
async def update_blog_post(
    blog_id: int,
    title: str,
    content: str,
    is_public: bool = True,
    tags: str = ""
) -> Dict[str, Any]:
    """블로그 포스트를 수정"""
    blog_data = {
        "title": title,
        "content": content,
        "is_public": is_public,
        "tags": tags
    }
    return await _make_api_request("PUT", f"/blog/{blog_id}/", blog_data)

# === 이미지 업로드 도구 ===

@mcp_server.tool(
    name="upload_page_image",
    description="페이지용 이미지를 업로드합니다. page_id와 이미지 파일 경로(file_path)가 필요합니다."
)
async def upload_page_image(page_id: int, file_path: str) -> Dict[str, Any]:
    """페이지용 이미지를 업로드"""
    if not API_TOKEN:
        return {"error": "API 토큰이 설정되지 않았습니다."}
    
    if not os.path.exists(file_path):
        return {"error": f"파일을 찾을 수 없습니다: {file_path}"}
    
    headers = {"Authorization": f"Token {API_TOKEN}"}
    
    try:
        async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'page_id': page_id}
                response = await client.post("/images/upload/", files=files, data=data)
                response.raise_for_status()
                return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Error {e.response.status_code}", "message": str(e)}
    except Exception as e:
        return {"error": "Upload Failed", "message": str(e)}

@mcp_server.tool(
    name="upload_blog_image",
    description="블로그용 이미지를 업로드합니다. blog_id와 이미지 파일 경로(file_path)가 필요합니다."
)
async def upload_blog_image(blog_id: int, file_path: str) -> Dict[str, Any]:
    """블로그용 이미지를 업로드"""
    if not API_TOKEN:
        return {"error": "API 토큰이 설정되지 않았습니다."}
    
    if not os.path.exists(file_path):
        return {"error": f"파일을 찾을 수 없습니다: {file_path}"}
    
    headers = {"Authorization": f"Token {API_TOKEN}"}
    
    try:
        async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'blog_id': blog_id}
                response = await client.post("/blog/images/upload/", files=files, data=data)
                response.raise_for_status()
                return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Error {e.response.status_code}", "message": str(e)}
    except Exception as e:
        return {"error": "Upload Failed", "message": str(e)}

# === 리소스들 (나중에 활성화할 예정) ===
# 현재는 도구로만 기능을 제공하고, 리소스는 추후 테스트 후 활성화

# @mcp_server.resource(
#     "wikidocs://books",
#     description="내가 작성한 모든 위키독스 책 목록을 조회합니다."
# )
# async def list_my_books_resource() -> List[Dict[str, Any]]:
#     """사용자의 책 목록을 리소스로 제공"""
#     result = await _make_api_request("GET", "/books/")
#     if "error" in result:
#         return [result]
#     return result

# --- 서버 실행 ---
if __name__ == "__main__":
    # transport 인자 없이 run()을 호출하여 기본값인 'stdio'로 실행합니다.
    mcp_server.run()

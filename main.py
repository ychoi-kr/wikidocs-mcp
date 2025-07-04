import os
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv
from fastmcp import FastMCP

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()

# --- API 설정 ---
WIKIDOCS_API_URL = "https://wikidocs.net/napi"
API_TOKEN = os.getenv("WIKIDOCS_API_TOKEN")

# --- MCP 서버 인스턴스 생성 ---
mcp_server = FastMCP(
    name="Wikidocs Server",
    instructions="이 서버는 위키독스의 책과 페이지 콘텐츠를 조회하고 수정하는 기능을 제공합니다."
)

async def _upsert_page(page_id: int, data: Dict[str, Any]) -> dict:
    """
    위키독스 페이지를 생성하거나 수정하는 PUT 요청을 처리하는 비공개 함수.
    page_id가 -1이면 생성, 그렇지 않으면 수정을 처리한다.
    """
    if not API_TOKEN:
        raise ValueError("WIKIDOCS_API_TOKEN이 .env 파일에 설정되지 않았습니다.")

    data['depth'] = 0
    data['seq'] = 0
    
    headers = {"Authorization": f"Token {API_TOKEN}"}
    async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
        try:
            response = await client.put(f"/pages/{page_id}/", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"error": "Not Found", "message": f"ID {page_id if page_id != -1 else '(new page)'}에 해당하는 리소스를 찾을 수 없습니다."}
            elif e.response.status_code == 422:
                 return {"error": "Unprocessable Content", "message": f"요청 데이터가 잘못되었습니다. 필수 필드(book_id 등)를 확인하세요: {data}"}
            else:
                return {"error": f"HTTP Error {e.response.status_code}", "message": f"API 요청 중 오류가 발생했습니다: {e}"}


# --- MCP 기능(도구, 리소스) 정의 ---
@mcp_server.resource(
    "wikidocs:///books",
    description="내가 작성한 모든 위키독스 책 목록을 조회합니다."
)
async def list_my_books() -> List[Dict[str, Any]]:
    if not API_TOKEN:
        raise ValueError("WIKIDOCS_API_TOKEN 환경 변수가 설정되지 않았습니다.")
    headers = {"Authorization": f"Token {API_TOKEN}"}
    async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
        response = await client.get("/books/")
        response.raise_for_status()
        return response.json()

@mcp_server.tool(
    name="get_book_pages",
    description="특정 책 ID에 포함된 모든 페이지(목차) 목록을 조회합니다."
)
async def get_book_pages(book_id: int) -> Dict[str, Any]:
    """/napi/books/{book_id}/ API를 호출하고, 404 오류를 처리합니다."""
    if not API_TOKEN:
        raise ValueError("WIKIDOCS_API_TOKEN 환경 변수가 설정되지 않았습니다.")
    
    headers = {"Authorization": f"Token {API_TOKEN}"}
    try:
        async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
            response = await client.get(f"/books/{book_id}/")
            # raise_for_status()는 200번대 성공 코드가 아니면 예외를 발생시킵니다.
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        # 발생한 예외가 HTTP 오류일 경우, 여기서 잡아냅니다.
        if e.response.status_code == 404:
            # 404 오류일 때 사용자 친화적인 JSON 응답을 반환합니다.
            return {
                "error": "Not Found",
                "message": f"ID {book_id}에 해당하는 책을 찾을 수 없습니다. 책 ID가 올바른지, 또는 해당 계정의 API 토큰이 맞는지 확인해 주세요."
            }
        else:
            # 그 외 다른 HTTP 오류일 경우
            return {
                "error": f"HTTP Error {e.response.status_code}",
                "message": f"API 요청 중 오류가 발생했습니다: {e}"
            }

@mcp_server.tool(
    name="get_page_content",
    description="주어진 페이지 ID의 내용을 조회합니다."
)
async def get_page_content(page_id: int) -> dict:
    """/napi/pages/{page_id}/ API를 호출하고, 404 오류를 처리합니다."""
    if not API_TOKEN:
        raise ValueError("WIKIDOCS_API_TOKEN 환경 변수가 설정되지 않았습니다.")
    
    headers = {"Authorization": f"Token {API_TOKEN}"}
    try:
        async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
            response = await client.get(f"/pages/{page_id}/")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Not Found",
                "message": f"ID {page_id}에 해당하는 페이지를 찾을 수 없습니다. 페이지 ID를 다시 확인해 주세요."
            }
        else:
            return {
                "error": f"HTTP Error {e.response.status_code}",
                "message": f"API 요청 중 오류가 발생했습니다: {e}"
            }


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
) -> dict:
    new_page_data = {
        "id": 0,  # 신규 생성 시 의미 없는 값이지만 형식상 포함
        "subject": subject,
        "content": content,
        "parent_id": parent_id,
        "depth": 0, # 서버에서 계산해 주기를 기대하며 기본값 0으로 설정
        "seq": 0,   # 서버에서 계산해 주기를 기대하며 기본값 0으로 설정
        "book_id": book_id,
        "open_yn": open_yn
    }
    
    return await _upsert_page(page_id=-1, data=new_page_data)



@mcp_server.tool(
    name="update_page",
    description="페이지(page_id)의 제목(subject), 내용(content), 상위 페이지(parent_id), 공개 여부(open_yn)를 수정합니다. 페이지는 책에 속하지만, page_id는 위키독스 전체에서 고유하므로 어느 책에 속한 페이지를 수정하는지를 지정할 필요가 없습니다. 단, 사용자가 소유하지 않은 책의 페이지에 접근하려 하거나, 사용자가 현재 수정하고자 하는 책이 아닌 다른 책을 수정해서는 안 되므로, page_id를 정확하게 입력하도록 주의해야 합니다. 또한 공개 여부는 해당 페이지의 현재 설정값을 따르되, 사용자가 특별히 요구할 경우 토글합니다."
)
async def update_page(
    page_id: int, 
    subject: str, 
    content: str, 
    parent_id: int, 
    open_yn: str
) -> dict:
    update_data = {
        "id": page_id,
        "subject": subject,
        "content": content,
        "parent_id": parent_id,
        "book_id": 0,
        "open_yn": open_yn
    }
    return await _upsert_page(page_id=page_id, data=update_data)

# --- 서버 실행 ---
if __name__ == "__main__":
    # transport 인자 없이 run()을 호출하여 기본값인 'stdio'로 실행합니다.
    mcp_server.run()

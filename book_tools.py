from typing import Dict, Any
from utils import make_api_request, put_page, upload_image

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
        description="책을 조회합니다. 책에 속한 페이지 목록이 함께 조회됩니다. 단, 페이지가 많을 경우 완전한 목록을 제공하지 못할 수 있습니다."
    )
    async def get_book_info(book_id: int) -> Dict[str, Any]:
        """/napi/books/{book_id} : 책을 조회합니다. 책에 속해 있는 모든 페이지가 함께 조회됩니다."""
        return await make_api_request("GET", f"/books/{book_id}/")

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
            "id": 0,
            "subject": subject,
            "content": content,
            "parent_id": parent_id,
            "depth": 0,
            "seq": 0,
            "book_id": book_id,
            "open_yn": open_yn
        }
        return await put_page(page_id=-1, data=new_page_data)

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
        return await put_page(page_id=page_id, data=update_data)

    @mcp_server.tool(
        name="upload_page_image",
        description="페이지용 이미지를 업로드합니다. page_id와 이미지 파일 경로(file_path)가 필요합니다."
    )
    async def upload_page_image(page_id: int, file_path: str) -> Dict[str, Any]:
        """페이지용 이미지를 업로드"""
        data = {'page_id': page_id}
        return await upload_image("/images/upload/", file_path, data)
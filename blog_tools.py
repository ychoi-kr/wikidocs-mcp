from typing import Dict, Any
from utils import make_api_request, upload_image

def register_blog_tools(mcp_server):
    """블로그 관련 도구들을 MCP 서버에 등록"""
    
    @mcp_server.tool(
        name="get_blog_profile",
        description="블로그 프로필 정보를 조회합니다."
    )
    async def get_blog_profile() -> Dict[str, Any]:
        """블로그 프로필 정보를 반환"""
        return await make_api_request("GET", "/blog/profile/")

    @mcp_server.tool(
        name="get_blog_list",
        description="블로그 포스트 목록을 페이지별로 조회합니다. page 번호를 지정할 수 있습니다 (기본값: 1)."
    )
    async def get_blog_list(page: int = 1) -> Dict[str, Any]:
        """블로그 포스트 목록을 반환"""
        return await make_api_request("GET", f"/blog/list/{page}")

    @mcp_server.tool(
        name="get_blog_post",
        description="특정 블로그 포스트 ID의 내용을 조회합니다."
    )
    async def get_blog_post(blog_id: int) -> Dict[str, Any]:
        """특정 블로그 포스트 내용을 반환"""
        return await make_api_request("GET", f"/blog/{blog_id}")

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
        return await make_api_request("POST", "/blog/create/", blog_data)

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
        return await make_api_request("PUT", f"/blog/{blog_id}/", blog_data)

    @mcp_server.tool(
        name="upload_blog_image",
        description="블로그용 이미지를 업로드합니다. blog_id와 이미지 파일 경로(file_path)가 필요합니다."
    )
    async def upload_blog_image(blog_id: int, file_path: str) -> Dict[str, Any]:
        """블로그용 이미지를 업로드"""
        data = {'blog_id': blog_id}
        return await upload_image("/blog/images/upload/", file_path, data)
from fastmcp import FastMCP
from book_tools import register_book_tools
from blog_tools import register_blog_tools

# --- MCP 서버 인스턴스 생성 ---
mcp_server = FastMCP(
    name="Wikidocs MCP Server",
    instructions="""이 서버는 위키독스 책과 블로그 콘텐츠를 조회하고 수정하는 기능을 제공합니다.

중요 사용 가이드:
- 책에 새 페이지를 추가할 때는 `create_page`를 사용하고, `update_page`는 기존 페이지를 수정할 때만 사용하세요.
- `create_page` 사용 도중에 출력이 중단되는 경우, 임의의 페이지 ID로 `update_page`를 시도해서는 안 됩니다.
- 존재하지 않거나 알지 못하는 페이지 ID에 대해 `update_page`를 절대 사용하지 마세요.
- `update_page` 도구는 `old_str`, `new_str` 매개변수를 지원하지 않습니다. 전체 `content`를 전달하세요.
- 책 페이지 작성 시 `get_wikidocs_formatting_guide` 도구로 포매팅 가이드를 확인하세요.
- 작성한 콘텐츠는 `validate_wikidocs_content` 도구로 검증할 수 있습니다.

참고:
- 책의 페이지 ID는 책 내에서뿐 아니라 위키독스에서 글로벌하게 고유합니다.
- 블로그와 책은 렌더링 방식이 다르므로 포매팅 가이드는 책에만 적용합니다."""
)

# --- 도구 등록 ---
def register_all_tools():
    """모든 도구를 MCP 서버에 등록"""
    register_book_tools(mcp_server)
    register_blog_tools(mcp_server)

# --- 메인 실행 ---
if __name__ == "__main__":
    # 모든 도구 등록
    register_all_tools()
    
    # 서버 실행 (transport 인자 없이 run()을 호출하여 기본값인 'stdio'로 실행)
    mcp_server.run()

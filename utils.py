import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()

# --- API 설정 ---
WIKIDOCS_API_URL = "https://wikidocs.net/napi"
API_TOKEN = os.getenv("WIKIDOCS_API_TOKEN")

def flatten_pages(pages: List[Dict]) -> List[Dict]:
    """
    중첩된 페이지 구조를 평면화합니다.
    
    Args:
        pages: 중첩된 페이지 리스트 (children 필드 포함)
    
    Returns:
        평면화된 페이지 리스트
    """
    flat: List[Dict] = []
    stack = pages[:]  # 복사해서 스택으로 사용
    
    while stack:
        node = stack.pop()
        flat.append(node)
        # children이 있을 때 스택에 push (깊이 우선 탐색)
        for child in reversed(node.get("children", [])):
            stack.append(child)
    
    return flat

async def make_api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
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

async def put_page(page_id: int, data: Dict[str, Any]) -> dict:
    """/napi/pages/{page_id} : 페이지를 수정합니다. (신규 페이지 등록인 경우에는 page_id 에 -1 설정)"""
    data['depth'] = 0
    data['seq'] = 0
    return await make_api_request("PUT", f"/pages/{page_id}/", data)

async def upload_image(endpoint: str, file_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """이미지 업로드 공통 함수"""
    if not API_TOKEN:
        return {"error": "API 토큰이 설정되지 않았습니다."}
    
    if not os.path.exists(file_path):
        return {"error": f"파일을 찾을 수 없습니다: {file_path}"}
    
    headers = {"Authorization": f"Token {API_TOKEN}"}
    
    try:
        async with httpx.AsyncClient(base_url=WIKIDOCS_API_URL, headers=headers) as client:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = await client.post(endpoint, files=files, data=data)
                response.raise_for_status()
                return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Error {e.response.status_code}", "message": str(e)}
    except Exception as e:
        return {"error": "Upload Failed", "message": str(e)}

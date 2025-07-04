# 위키독스 MCP 서버

AI 에이전트가 위키독스(Wikidocs) 책과 블로그를 읽고, 편집하고, 관리할 수 있도록 하는 **Model Context Protocol (MCP)** 서버입니다.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 주요 기능

### 📚 책 관리
- **스마트 캐싱**: 대량 페이지 데이터를 로컬에 캐시하여 성능 최적화
- **키워드 검색**: 책 내용에서 관련도 기반 페이지 검색
- **구조 탐색**: 책의 목차 구조를 요약하여 전체 구조 파악
- **페이지 CRUD**: 페이지 읽기, 생성, 수정 기능

### 📝 블로그 관리
- 블로그 포스트 목록 조회 및 내용 읽기
- 새 포스트 생성 및 기존 포스트 수정
- 태그 관리 및 공개/비공개 설정

### 🖼️ 이미지 업로드
- 페이지 및 블로그용 이미지 업로드 지원

## 🚀 빠른 시작

### 1. 설치

```bash
git clone https://github.com/your-username/wikidocs-mcp.git
cd wikidocs-mcp
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일을 생성하고 위키독스 API 토큰을 설정합니다.

```bash
WIKIDOCS_API_TOKEN="여기에_발급받은_API_토큰을_입력하세요"
```

> 💡 **API 토큰 발급**: [위키독스 로그인 > 계정설정 > API 토큰](https://wikidocs.net/profile/api/)에서 토큰을 확인할 수 있습니다.

### 3. Claude Desktop 연결

Claude Desktop 설정 파일(`claude_desktop_config.json`)에 서버를 등록합니다:

```json
{
  "mcpServers": {
    "wikidocs": {
      "command": "/opt/anaconda3/bin/python3",
      "args": ["/Users/your-username/wikidocs-mcp/main.py"]
    }
  }
}
```

> ⚠️ **중요**: 경로를 본인 환경에 맞게 수정하세요.
> - Python 경로 확인: `which python3`
> - 프로젝트 경로 확인: `pwd`

### 4. 테스트 실행

Claude Desktop을 재시작하고 다음과 같이 테스트해 보세요.

```
내 책 목록을 보여줘
```

## 🛠️ 도구 목록

### 📖 책 관리 도구

| 도구명 | 설명 | 사용 예시 |
|--------|------|-----------|
| `list_my_books` | 내가 작성한 책 목록 조회 | "내 책 목록을 보여줘" |
| `get_book_info` | 책 정보 조회 및 캐시 저장 | "책 ID 123의 정보를 가져와줘" |
| `search_book_pages` | 키워드로 페이지 검색 | "MCP 관련 내용을 찾아줘" |
| `get_book_structure` | 책 목차 구조 요약 | "이 책의 구조를 보여줘" |
| `get_page` | 특정 페이지 내용 조회 | "페이지 456의 내용을 보여줘" |
| `create_page` | 새 페이지 생성 | "새로운 챕터를 추가해줘" |
| `update_page` | 페이지 내용 수정 | "이 페이지를 수정해줘" |
| `upload_page_image` | 페이지용 이미지 업로드 | "이미지를 업로드해줘" |
| `get_cache_status` | 캐시 상태 확인 | "캐시 상태를 확인해줘" |

### 📝 블로그 관리 도구

| 도구명 | 설명 | 사용 예시 |
|--------|------|-----------|
| `get_blog_profile` | 블로그 프로필 정보 조회 | "내 블로그 정보를 보여줘" |
| `get_blog_list` | 블로그 포스트 목록 조회 | "최근 블로그 포스트를 보여줘" |
| `get_blog_post` | 특정 포스트 내용 조회 | "포스트 789의 내용을 보여줘" |
| `create_blog_post` | 새 포스트 생성 | "새 블로그 포스트를 작성해줘" |
| `update_blog_post` | 포스트 내용 수정 | "이 포스트를 수정해줘" |
| `upload_blog_image` | 블로그용 이미지 업로드 | "블로그 이미지를 업로드해줘" |

## 💡 사용법 예시

### 기본 워크플로

```
1. 책 목록 확인
   → "내 위키독스 책 목록을 보여줘"

2. 특정 책 로드
   → "책 ID 99999의 정보를 가져와줘"
   (대량 페이지 데이터가 로컬 캐시에 저장됨)

3. 키워드 검색
   → "MCP 관련 내용을 검색해줘"
   (관련도 높은 페이지들만 반환)

4. 상세 내용 조회
   → "페이지 99999999의 전체 내용을 보여줘"

5. 내용 수정
   → "이 페이지에 새로운 예제를 추가해줘"
```

### 고급 활용 예시

```
# 책 전체 분석
"MCP 가이드 책의 구조를 분석하고, 부족한 부분이 있으면 알려줘"

# 콘텐츠 최적화
"이 책에서 'MCP'라는 키워드가 나오는 모든 페이지를 찾아서 설명의 일관성을 확인해줘"

# 자동 블로그 포스팅
"책의 3장 내용을 요약해서 블로그 포스트로 작성해줘"
```

## 🏗️ 아키텍처

### 프로젝트 구조

```
wikidocs-mcp/
├── main.py              # 메인 서버 진입점
├── book_tools.py        # 책 관련 도구들
├── blog_tools.py        # 블로그 관련 도구들
├── utils.py             # 공통 유틸리티 함수
├── search_utils.py      # 캐시 및 검색 기능
├── .env                 # 환경 변수 (API 토큰)
└── requirements.txt     # 패키지 의존성
```

### 캐시 시스템

- **위치**: `~/.wikidocs_mcp_cache/`
- **구조**: 
  - `book_{id}.json`: 책 데이터
  - `book_{id}_meta.json`: 캐시 메타데이터
- **유효기간**: 24시간 (설정 가능)
- **자동 무효화**: 페이지 생성/수정 시

### 검색 알고리듬

1. **텍스트 정규화**: HTML 태그 제거, 특수문자 처리
2. **관련도 점수 계산**:
   - 제목 매칭: 10.0점 (완전 일치 시 +5.0점)
   - 내용 매칭: 매칭 수 × 2.0점
   - 부분 매칭: 단어별 0.5-3.0점
3. **결과 정렬**: 관련도 점수 기준 내림차순

## 📚 참고 자료

- [위키독스 API 문서](https://wikidocs.net/napi/docs)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP: AI 에이전트 시대의 통합 가이드](https://wikidocs.net/book/17996) (이 프로젝트의 기반이 된 책)

## 🛡️ 보안 및 주의사항

- **API 토큰 보안**: `.env` 파일을 절대 git에 커밋하지 마세요
- **권한 확인**: MCP 도구 실행 시 Claude가 권한을 요청합니다
- **캐시 관리**: 민감한 정보가 포함된 경우 캐시 디렉터리를 주기적으로 정리하세요

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 지원 및 문의

- **Issues**: [GitHub Issues](https://github.com/ychoi-kr/wikidocs-mcp/issues)

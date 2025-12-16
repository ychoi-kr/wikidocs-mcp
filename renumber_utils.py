import re
import difflib
from typing import List, Dict, Any, Tuple, Optional

def get_page_number(subject: str) -> Optional[str]:
    """
    페이지 제목에서 섹션 번호를 추출합니다.
    예: "5.2. 설치하기" -> "5.2"
    """
    match = re.match(r'^(\d+(?:\.\d+)*)', subject.strip())
    if match:
        return match.group(1)
    return None

def calculate_new_number(old_number: str, offset: int = 1) -> str:
    """
    섹션 번호를 offset만큼 증가시킵니다.
    마지막 숫자만 증가시킵니다.
    예: "5.2" + 1 -> "5.3"
    예: "5.2.1" + 1 -> "5.2.2" (X) - 주의: 이 함수는 형제 노드 이동용입니다.
    """
    parts = old_number.split('.')
    if not parts:
        return old_number
    
    try:
        last_num = int(parts[-1])
        new_last_num = last_num + offset
        parts[-1] = str(new_last_num)
        return '.'.join(parts)
    except ValueError:
        return old_number

def replace_prefix(number: str, old_prefix: str, new_prefix: str) -> str:
    """
    번호의 접두사를 교체합니다 (자식 노드용).
    예: number="5.2.1", old="5.2", new="5.3" -> "5.3.1"
    """
    if number.startswith(old_prefix):
        return new_prefix + number[len(old_prefix):]
    return number

def find_target_pages(book_data: Dict[str, Any], start_page_id: int) -> List[Dict[str, Any]]:
    """
    재귀적으로 책 구조를 탐색하여
    1. start_page_id와 같은 레벨의 이후 형제 페이지들 (siblings)
    2. 그 형제 페이지들의 모든 자손 페이지들 (descendants)
    을 순서대로 찾아서 반환합니다.
    """
    targets = []
    found_start = False
    
    # 재귀 함수 정의
    def traverse(pages: List[Dict[str, Any]]):
        nonlocal found_start
        
        for page in pages:
            # 시작 페이지를 찾으면 플래그 설정 (이 페이지 자체는 포함하지 않음 - 이미 존재하는 페이지를 미는 것이므로)
            # 사용자 요구사항: "5.2절을 추가하고 싶어서 기존 5.2를 5.3으로 밀고 싶다"
            # 즉, start_page_id로 지정된 페이지부터 밀어야 함.
            if page['id'] == start_page_id:
                found_start = True
            
            if found_start:
                targets.append(page)
            
            # 자식 노드 탐색
            if 'children' in page and page['children']:
                traverse(page['children'])

    # 최상위 페이지 목록부터 탐색 시작
    # book_data가 'pages' 키를 가지고 있다고 가정
    if 'pages' in book_data:
        # 주의: traverse는 전체 트리를 순회하면서 start_page_id 이후의 모든 노드를 수집함.
        # 하지만 우리는 "같은 레벨의 형제"와 "그 자손"만 필요함.
        # 단순히 DFS로 순회하면 start_page_id의 "다음 챕터(상위 레벨의 다음 형제)"까지 포함될 수 있음.
        # 따라서 로직을 수정해야 함.
        pass

    # 수정된 로직:
    # 1. start_page_id의 부모를 찾는다.
    # 2. 부모의 children 목록에서 start_page_id의 인덱스를 찾는다.
    # 3. 그 인덱스부터 끝까지가 "밀어야 할 형제들"이다.
    # 4. 각 형제와 그 자손들을 모두 수집한다.
    
    parent = find_parent(book_data['pages'], start_page_id)
    siblings = []
    
    if parent:
        # 부모가 있는 경우
        siblings_list = parent.get('children', [])
    else:
        # 최상위 레벨인 경우
        siblings_list = book_data.get('pages', [])
        
    # start_page_id의 인덱스 찾기
    start_index = -1
    for i, page in enumerate(siblings_list):
        if page['id'] == start_page_id:
            start_index = i
            break
            
    if start_index != -1:
        # start_page_id 포함하여 그 뒤의 모든 형제들
        siblings = siblings_list[start_index:]
        
    # 수집된 형제들과 그 자손들을 평탄화하여 리스트로 반환
    final_targets = []
    for sibling in siblings:
        add_page_and_descendants(sibling, final_targets)
        
    return final_targets

def find_parent(pages: List[Dict], target_id: int) -> Optional[Dict]:
    """재귀적으로 부모 페이지를 찾습니다."""
    for page in pages:
        for child in page.get('children', []):
            if child['id'] == target_id:
                return page
            # 깊이 우선 탐색
            found = find_parent([child], target_id)
            if found:
                return found
    return None

def add_page_and_descendants(page: Dict, result_list: List[Dict]):
    """페이지와 그 자손들을 리스트에 추가합니다."""
    result_list.append(page)
    for child in page.get('children', []):
        add_page_and_descendants(child, result_list)

def apply_renumbering(
    subject: str, 
    content: str, 
    old_number: str, 
    new_number: str
) -> Tuple[str, str, bool]:
    """
    제목과 내용에서 번호를 치환합니다.
    Returns: (new_subject, new_content, changed)
    """
    changed = False
    new_subject = subject
    new_content = content
    
    # 1. 제목 치환
    # 예: "5.2. 설치" -> "5.3. 설치"
    # 주의: 단순 replace가 아니라 맨 앞부분만 교체해야 함
    if subject.strip().startswith(old_number):
        # 정확히 old_number 뒤에 점이나 공백이 오는지 확인하여 오탐 방지 (예: 5.2가 5.21을 매칭하지 않도록)
        # 하지만 보통 "5.2." 또는 "5.2 " 형태임.
        # 정규식 사용: ^(old_number)(?=\D|$)
        pattern = re.compile(r'^' + re.escape(old_number) + r'(?=\D|$)')
        if pattern.match(subject.strip()):
            new_subject = pattern.sub(new_number, subject.strip(), count=1)
            changed = True

    # 2. 본문 헤더 치환
    # 마크다운 헤더 (#, ##, ### 등) 뒤에 오는 번호 치환
    # 예: "## 5.2. 설치" -> "## 5.3. 설치"
    # 멀티라인 모드 사용
    header_pattern = re.compile(
        r'^(#+\s+)' + re.escape(old_number) + r'(?=\D|$)', 
        re.MULTILINE
    )
    
    if header_pattern.search(content):
        new_content = header_pattern.sub(r'\g<1>' + new_number, content)
        changed = True
        
    return new_subject, new_content, changed

def generate_diff(original: str, modified: str, filename: str = "text") -> str:
    """diff 문자열을 생성합니다."""
    diff = difflib.unified_diff(
        original.splitlines(), 
        modified.splitlines(), 
        fromfile=f"Original {filename}", 
        tofile=f"Modified {filename}",
        lineterm=""
    )
    return "\n".join(diff)

def create_renumbering_plan(
    book_data: Dict[str, Any], 
    start_page_id: int, 
    offset: int = 1
) -> List[Dict[str, Any]]:
    """
    변경 계획을 수립하여 반환합니다.
    형제 노드들을 순차적으로 재번호화하여 중복을 해결합니다.
    """
    # 1. 대상 페이지 찾기 (start_page_id와 그 이후의 형제들, 그리고 그 자손들)
    # 주의: find_target_pages는 "start_page_id"를 포함하여 그 뒤의 모든 형제들을 찾음.
    # 하지만 "중복된 번호"가 있을 때, start_page_id가 "첫 번째 5.2"인지 "두 번째 5.2"인지에 따라
    # targets 리스트가 달라짐. find_target_pages는 ID 기반이므로 정확함.
    targets = find_target_pages(book_data, start_page_id)
    
    if not targets:
        return []
        
    # 2. 형제 노드 식별 및 순서 파악
    parent = find_parent(book_data['pages'], start_page_id)
    all_siblings = []
    if parent:
        all_siblings = parent.get('children', [])
    else:
        all_siblings = book_data.get('pages', [])
        
    # targets에 포함된 페이지들 중 "형제 노드"만 골라내기 (순서 유지)
    # find_target_pages는 형제+자손을 섞어서 반환할 수 있으므로(구현에 따라 다름),
    # all_siblings에서 targets에 있는 것들을 순서대로 추출하는 것이 안전함.
    
    target_ids = {p['id'] for p in targets}
    target_siblings = [p for p in all_siblings if p['id'] in target_ids]
    
    # 3. 시작 번호 결정
    # start_page_id의 바로 앞 형제의 번호를 확인하여 기준점 설정
    start_index = -1
    for i, p in enumerate(all_siblings):
        if p['id'] == start_page_id:
            start_index = i
            break
            
    base_number_parts = []
    
    if start_index > 0:
        # 바로 앞 형제가 있음 -> 그 형제의 번호를 기준으로 +1
        prev_sibling = all_siblings[start_index - 1]
        prev_num = get_page_number(prev_sibling['subject'])
        if prev_num:
            # 예: 앞이 5.1이면 -> 5.2부터 시작?
            # 아니면 앞이 5.1이고 offset=1이면 -> 5.2?
            # 사용자의 의도: "중간에 삽입" -> 기존 5.2를 5.3으로 밀고 싶음.
            # 즉, 앞이 5.1이면, 현재(5.2)는 5.3이 되어야 함 (5.1 + 1 + offset? 아니면 5.1 + 1?)
            # 헷갈림 방지를 위해:
            # "현재 페이지의 원래 번호"를 기준으로 하는 것이 아니라
            # "앞 페이지 번호의 다음 번호"를 "현재 페이지의 새로운 번호"로 잡는 것이 '순차적 정리'임.
            # 하지만 offset이 있음.
            # 보통 offset=1은 "한 칸 띄우기"임.
            # 앞이 5.1이면, 순차적으로는 5.2가 맞음.
            # 근데 5.2 자리에 새 글을 쓸 거니까, 기존 5.2는 5.3이 되어야 함.
            # 즉, (앞 페이지 번호) + 1 + (삽입할 개수=1) ?
            # 아니면 그냥 (앞 페이지 번호) + 1 로 하면 "빈 자리"가 없어짐.
            
            # 사용 시나리오:
            # 5.1, 5.2(기존), 5.3
            # 5.2(기존)을 5.3으로 만들고 싶음. (그래야 5.2(신규)를 넣으니까)
            # 그러면 앞 페이지(5.1) + 1 = 5.2. 여기에 offset(1) 더하면 5.3.
            # 맞음.
            
            # 예외: 앞 페이지가 없을 때 (첫 번째 자식일 때)
            # 원래 번호가 5.1이었다면 -> 5.2가 되어야 함.
            # 원래 번호가 1.1이었다면 -> 1.2가 되어야 함.
            pass
            
            parts = prev_num.split('.')
            try:
                last = int(parts[-1])
                # 앞 페이지가 5.1이면 last=1.
                # 우리는 5.3을 원함 (offset=1 가정).
                # 1 + 1 + 1? No.
                # 순차적으로는 5.2가 되어야 하는데, offset만큼 밀리니까 5.2 + offset?
                # 아니, offset은 "밀어내는 칸 수"임.
                # 즉, (prev_last + 1) + (offset - 1)? 
                # 만약 offset=1이면, (prev_last + 1) = 5.2. 이게 "원래 있어야 할 번호".
                # 근데 5.2 자리를 비워야 하니까 5.3이 됨?
                # 아니요, renumber_pages는 "기존 페이지들을 뒤로 미는" 도구임.
                # 즉, 5.2(기존) -> 5.3이 되어야 함.
                # 앞 페이지(5.1) 기준으로는 +2가 됨.
                
                # 공식: new_last = prev_last + 1 + (offset if we are shifting away from prev else 0?)
                # 아니, 그냥 심플하게:
                # target_siblings[0]의 new_number = (prev_num + 1) + (offset - 1)?
                # 헷갈림.
                
                # 다시:
                # 5.1 (고정)
                # 5.2 (타겟) -> 5.3 (목표)
                # 5.1의 끝자리 1.
                # 1 + 1 = 2 (원래 순서).
                # 2 + offset(1) = 3.
                # OK.
                
                new_start_last = last + 1 + (offset - 1) if offset > 0 else last + 1
                # offset이 1이면 +1. offset이 0이면(정리만) +1.
                # offset이 1(밀기) -> 5.1 뒤에 5.2(신규)가 옴. 기존 5.2는 5.3이 됨.
                # 즉 5.1(1) -> 5.3(3). 차이는 2.
                # 1 + 2 = 3.
                # 즉 prev_last + offset + 1 ?
                # offset=1 -> +2.
                # offset=2 -> +3.
                # OK.
                
                # 만약 offset=0 (단순 정리) 이면?
                # 5.1, 5.2, 5.2 -> 5.1, 5.2, 5.3
                # 타겟은 첫번째 5.2.
                # prev(5.1) + 0 + 1 = 5.2.
                # OK.
                
                start_last_num = last + offset + 1
                base_number_parts = parts[:-1]
                
            except ValueError:
                # 번호 파싱 실패 시 fallback: 현재 페이지의 old_number 사용
                pass

    if not base_number_parts:
        # 앞 형제가 없거나 파싱 실패 시
        # 타겟의 첫 페이지의 old_number를 기준으로 함
        first_target = target_siblings[0]
        old_num = get_page_number(first_target['subject'])
        if old_num:
            parts = old_num.split('.')
            try:
                last = int(parts[-1])
                start_last_num = last + offset
                base_number_parts = parts[:-1]
            except ValueError:
                return [] # 번호 없으면 포기
        else:
            return []

    # 4. 변경 계획 수립
    plan = []
    prefix_map = {} # old_number -> new_number (X) -> page_id -> new_number (O)
    # 자손 처리를 위해 page_id 기반 매핑이 필요함 (중복 번호 때문)
    
    # 4-1. 형제 노드 처리 (순차 할당)
    current_last_num = start_last_num
    
    for page in target_siblings:
        page_id = page['id']
        subject = page['subject']
        old_number = get_page_number(subject)
        
        if not old_number:
            continue
            
        # 새 번호 생성
        new_parts = base_number_parts + [str(current_last_num)]
        new_number = '.'.join(new_parts)
        
        # 맵에 저장 (자손 처리를 위해)
        # 형제 노드의 자손들은 "자신의 old_number prefix"가 "부모의 old_number"와 일치함을 이용해야 함.
        # 하지만 부모의 old_number가 중복이면?
        # 예: 5.2(A), 5.2(B).
        # A의 자식 5.2.1 -> A가 5.3이 되면 5.3.1이 되어야 함.
        # B의 자식 5.2.1 -> B가 5.4가 되면 5.4.1이 되어야 함.
        # 따라서 "어떤 자식이 어떤 부모 소속인지"를 알아야 함.
        # targets 리스트는 평탄화되어 있지만, 우리는 book_data 트리 구조를 가지고 있음.
        # 따라서 targets를 순회하는 대신, target_siblings의 자손을 재귀적으로 탐색하는 것이 나음.
        
        # 계획 추가
        if new_number != old_number:
            plan.append({
                "page_id": page_id,
                "subject": subject,
                "old_number": old_number,
                "new_number": new_number
            })
            
        # 이 형제의 자손들 처리
        if 'children' in page:
            # 재귀적으로 자손들의 번호 변경 계획 수립
            # 자손들은 offset 개념이 아니라 "부모의 번호가 바뀜에 따른 prefix 교체"임.
            descendant_plan = create_descendant_plan(page['children'], old_number, new_number)
            plan.extend(descendant_plan)
            
        current_last_num += 1
            
    return plan

def create_descendant_plan(
    pages: List[Dict[str, Any]], 
    parent_old_number: str, 
    parent_new_number: str
) -> List[Dict[str, Any]]:
    """
    자손 페이지들의 번호를 부모의 변경된 번호에 맞춰 업데이트합니다.
    """
    plan = []
    for page in pages:
        page_id = page['id']
        subject = page['subject']
        old_number = get_page_number(subject)
        
        if old_number and old_number.startswith(parent_old_number + "."):
            new_number = replace_prefix(old_number, parent_old_number, parent_new_number)
            
            if new_number != old_number:
                plan.append({
                    "page_id": page_id,
                    "subject": subject,
                    "old_number": old_number,
                    "new_number": new_number
                })
                
            # 재귀 호출 (자손의 자손)
            # 주의: 여기서 parent_old_number는 현재 페이지의 old_number가 되어야 함?
            # 아니요, replace_prefix는 "맨 앞의 prefix"만 바꿉니다.
            # 5.2.1.1 -> 5.2를 5.3으로 -> 5.3.1.1
            # 따라서 재귀적으로 내려갈 때도 "최상위 변경점"인 parent_old_number를 계속 써도 됨.
            # 하지만 안전하게 하려면, 현재 페이지의 바뀐 번호를 기준으로 하는 게 나을 수도?
            # replace_prefix 함수는 "5.2.1"에서 "5.2"를 "5.3"으로 바꿈.
            # 그 자식 "5.2.1.1"에서도 "5.2"를 "5.3"으로 바꾸면 됨.
            # 즉, parent_old/new를 그대로 전달해도 됨.
            
            if 'children' in page:
                plan.extend(create_descendant_plan(page['children'], parent_old_number, parent_new_number))
                
    return plan

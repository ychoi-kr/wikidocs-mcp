import unittest
from renumber_utils import (
    get_page_number, 
    calculate_new_number, 
    replace_prefix, 
    apply_renumbering
)

class TestRenumberUtils(unittest.TestCase):
    
    def test_get_page_number(self):
        self.assertEqual(get_page_number("5.2. 설치하기"), "5.2")
        self.assertEqual(get_page_number("5.2.1. 세부설정"), "5.2.1")
        self.assertEqual(get_page_number("서론"), None)
        self.assertEqual(get_page_number("10장. 결론"), "10")

    def test_calculate_new_number(self):
        self.assertEqual(calculate_new_number("5.2", 1), "5.3")
        self.assertEqual(calculate_new_number("5.9", 1), "5.10")
        self.assertEqual(calculate_new_number("1", 1), "2")
        
    def test_replace_prefix(self):
        self.assertEqual(replace_prefix("5.2.1", "5.2", "5.3"), "5.3.1")
        self.assertEqual(replace_prefix("5.2.1.1", "5.2", "5.3"), "5.3.1.1")
        self.assertEqual(replace_prefix("6.1.1", "5.2", "5.3"), "6.1.1") # No match

    # test_create_renumbering_plan removed as the function was deleted.

    def test_apply_renumbering(self):
        # 1. Subject only
        subj, cont, changed = apply_renumbering("5.2. 제목", "내용 없음", "5.2", "5.3")
        self.assertEqual(subj, "5.3. 제목")
        self.assertTrue(changed)
        
        # 2. Content Header with variable levels (#, ##, ###)
        # 사용자의 우려: "# 문자 개수가 단계수와 일치하지 않을 수도 있다" -> 모두 처리되어야 함
        content = """
# 5.2. 1단계 헤더
## 5.2. 2단계 헤더
### 5.2. 3단계 헤더
#### 5.2 4단계 (점 없음)
"""
        subj, new_cont, changed = apply_renumbering("제목", content, "5.2", "5.3")
        
        self.assertIn("# 5.3. 1단계 헤더", new_cont)
        self.assertIn("## 5.3. 2단계 헤더", new_cont)
        self.assertIn("### 5.3. 3단계 헤더", new_cont)
        self.assertIn("#### 5.3 4단계", new_cont)
        self.assertTrue(changed)

        # 3. Subject has NO number, but Content HAS number
        # 제목에 번호가 없어도 본문 치환은 동작해야 함 (execute 단계에서 old_number가 주어졌다면)
        subj, new_cont, changed = apply_renumbering("번호 없는 제목", "## 5.2. 본문 헤더", "5.2", "5.3")
        self.assertEqual(subj, "번호 없는 제목") # 제목은 안 바뀜
        self.assertEqual(new_cont, "## 5.3. 본문 헤더") # 본문은 바뀜
        self.assertTrue(changed)

        # 4. Mixed Content (Target vs Non-Target)
        # 5.2는 5.3으로 바뀌어야 하지만, 5.2.1은 (단순 텍스트라면) 안 바뀌어야 함.
        # 단, replace_prefix 로직이 아니라 apply_renumbering은 '정확한 매칭'을 의도함.
        # 현재 로직: 5.2(?=\D|$) -> 5.2 뒤에 숫자가 아니면 매칭.
        # "5.2.1" -> "5.2" 뒤에 "."(non-digit) -> 매칭됨! -> "5.3.1"이 됨.
        # 이는 자식 노드 번호도 같이 밀리는 효과가 있어 긍정적임.
        content = """
## 5.2. 타겟
본문 내용...
### 5.2.1. 자식 (같이 밀림)
참조: 5.2.2 (같이 밀림)
다른 번호: 5.20 (안 밀림)
"""
        subj, new_cont, changed = apply_renumbering("제목", content, "5.2", "5.3")
        self.assertIn("## 5.3. 타겟", new_cont)
        self.assertIn("### 5.3.1. 자식", new_cont)
        self.assertIn("참조: 5.2.2", new_cont) # 본문 내 참조는 헤더가 아니므로 바뀌지 않아야 함 (Safe!)
        self.assertIn("다른 번호: 5.20", new_cont) # 5.20은 5.2로 시작하지만 뒤에 숫자가 있어서 매칭 안 됨 (OK)

if __name__ == '__main__':
    unittest.main()

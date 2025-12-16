#!/usr/bin/env python3
"""
위키독스 MCP 캐시 디버깅 및 정리 도구
"""

import os
import json
import sys
from pathlib import Path

def find_cache_directory():
    """캐시 디렉터리 찾기"""
    home_dir = os.path.expanduser("~")
    cache_dir = os.path.join(home_dir, ".wikidocs_mcp_cache")
    return cache_dir

def analyze_cache_file(cache_file):
    """캐시 파일 분석"""
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📄 파일: {os.path.basename(cache_file)}")
        print(f"   크기: {os.path.getsize(cache_file)} bytes")
        
        if isinstance(data, dict):
            print(f"   키: {list(data.keys())}")
            if 'pages' in data:
                pages = data['pages']
                if isinstance(pages, list):
                    print(f"   페이지 수: {len(pages)}")
                    if pages:
                        first_page = pages[0]
                        if isinstance(first_page, dict):
                            print(f"   첫 페이지 키: {list(first_page.keys())}")
                        else:
                            print(f"   ❌ 첫 페이지가 dict가 아님: {type(first_page)}")
                else:
                    print(f"   ❌ pages가 list가 아님: {type(pages)}")
            else:
                print("   ❌ pages 키가 없음")
        else:
            print(f"   ❌ 데이터가 dict가 아님: {type(data)}")
            
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON 파싱 오류: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 파일 읽기 오류: {e}")
        return False

def clear_cache(cache_dir, book_id=None):
    """캐시 정리"""
    if not os.path.exists(cache_dir):
        print(f"캐시 디렉터리가 존재하지 않습니다: {cache_dir}")
        return
    
    files_to_remove = []
    
    if book_id:
        # 특정 책의 캐시만 삭제
        patterns = [f"book_{book_id}.json", f"book_{book_id}_meta.json"]
        for pattern in patterns:
            file_path = os.path.join(cache_dir, pattern)
            if os.path.exists(file_path):
                files_to_remove.append(file_path)
    else:
        # 모든 캐시 삭제
        for file in os.listdir(cache_dir):
            if file.startswith("book_") and file.endswith((".json")):
                files_to_remove.append(os.path.join(cache_dir, file))
    
    if not files_to_remove:
        print("삭제할 캐시 파일이 없습니다.")
        return
    
    print(f"다음 파일들을 삭제합니다:")
    for file_path in files_to_remove:
        print(f"  - {os.path.basename(file_path)}")
    
    confirm = input("계속하시겠습니까? (y/N): ")
    if confirm.lower() == 'y':
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"✅ 삭제됨: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"❌ 삭제 실패: {os.path.basename(file_path)} - {e}")
    else:
        print("취소되었습니다.")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        cache_dir = find_cache_directory()
        
        if command == "analyze":
            print(f"📂 캐시 디렉터리: {cache_dir}")
            
            if not os.path.exists(cache_dir):
                print("❌ 캐시 디렉터리가 존재하지 않습니다.")
                return
            
            cache_files = [f for f in os.listdir(cache_dir) if f.startswith("book_") and f.endswith(".json")]
            
            if not cache_files:
                print("📭 캐시 파일이 없습니다.")
                return
            
            print(f"🔍 {len(cache_files)}개의 캐시 파일 분석 중...")
            
            corrupted_files = []
            for cache_file in sorted(cache_files):
                file_path = os.path.join(cache_dir, cache_file)
                if not analyze_cache_file(file_path):
                    corrupted_files.append(cache_file)
            
            if corrupted_files:
                print(f"\n❌ 손상된 파일: {len(corrupted_files)}개")
                for f in corrupted_files:
                    print(f"  - {f}")
                print("\n이 파일들을 삭제하는 것을 권장합니다.")
            else:
                print("\n✅ 모든 캐시 파일이 정상입니다.")
        
        elif command == "clear":
            book_id = sys.argv[2] if len(sys.argv) > 2 else None
            if book_id:
                try:
                    book_id = int(book_id)
                    clear_cache(cache_dir, book_id)
                except ValueError:
                    print("❌ book_id는 숫자여야 합니다.")
            else:
                clear_cache(cache_dir)
        
        elif command == "info":
            print(f"📂 캐시 디렉터리: {cache_dir}")
            if os.path.exists(cache_dir):
                cache_files = [f for f in os.listdir(cache_dir) if f.startswith("book_")]
                print(f"📄 캐시 파일 수: {len(cache_files)}")
                
                total_size = 0
                for f in cache_files:
                    total_size += os.path.getsize(os.path.join(cache_dir, f))
                
                print(f"💾 총 크기: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
            else:
                print("❌ 캐시 디렉터리가 존재하지 않습니다.")
        
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print_usage()
    
    else:
        print_usage()

def print_usage():
    print("""
위키독스 MCP 캐시 디버깅 도구

사용법:
  python cache_debug.py analyze           # 모든 캐시 파일 분석
  python cache_debug.py clear             # 모든 캐시 삭제
  python cache_debug.py clear <book_id>   # 특정 책 캐시 삭제
  python cache_debug.py info              # 캐시 정보 출력
""")

if __name__ == "__main__":
    main()

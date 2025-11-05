"""
Gemma 3 VLM을 사용한 자동 이미지 태깅 스크립트

이 스크립트는 ready 폴더의 이미지를 분석하여 자동으로 태그를 추가합니다.
- 물건/오브젝트 (바이크, 자동차, 총, 무기 등)
- 머리 색상 (흰색, 분홍색, 금색 등)
- 복장 (바니걸, 메이드복, 메카물 등)
"""

import os
import sys
import time
from app import app, db
from models import Image, Tag

try:
    import ollama
except ImportError:
    print("Error: ollama 라이브러리가 설치되지 않았습니다.")
    print("설치 명령어: pip install ollama")
    sys.exit(1)


# 설정
OLLAMA_MODEL = "gemma3:27b-it-q8_0"
READY_FOLDER = 'static/ready'  # 이미지 폴더 (상대 경로)
BATCH_DELAY = 0.5  # 배치 간 대기 시간 (초)
DRY_RUN = False  # True로 설정하면 DB에 저장하지 않고 출력만 함


def get_tagging_prompt():
    """이미지 태깅을 위한 최적화된 프롬프트"""
    return """Analyze this anime/illustration image in detail and provide specific tags.

Focus on these categories:

1. OBJECTS & ITEMS:
   - Vehicles: motorcycle, bike, car, truck, mecha
   - Weapons: gun, sword, rifle, pistol, knife
   - Items: bag, phone, book, umbrella, etc.

2. HAIR COLOR (if character present):
   - white hair, silver hair, pink hair, blonde hair, black hair,
   - red hair, blue hair, purple hair, green hair, brown hair
   - multicolored hair, gradient hair

3. OUTFIT/COSTUME:
   - bunny girl, maid outfit, school uniform, military uniform
   - mecha suit, armor, casual clothes, formal wear
   - swimsuit, kimono, dress, hoodie, etc.

4. CHARACTER FEATURES:
   - 1girl, 1boy, multiple girls, multiple boys
   - long hair, short hair, twintails, ponytail
   - animal ears, wings, horns, tail

5. SETTING & STYLE:
   - outdoor, indoor, city, nature, cyberpunk, fantasy
   - day, night, sunset, rain
   - realistic, anime style, chibi, sketch

Return ONLY comma-separated tags in lowercase English.
Focus on the most prominent and important features.
Maximum 15 tags.

Example format: 1girl,pink hair,long hair,bunny girl,gun,motorcycle,outdoor,night,neon lights

Tags:"""


def analyze_image_with_gemma(image_path):
    """
    Gemma 3 VLM으로 이미지 분석 및 태그 생성

    Args:
        image_path (str): 이미지 파일 경로

    Returns:
        list: 태그 리스트
    """
    try:
        print(f"  🔍 Analyzing with Gemma3...")

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': get_tagging_prompt(),
                    'images': [image_path]
                }
            ]
        )

        # 응답에서 태그 추출
        content = response['message']['content'].strip()

        # "Tags:" 이후의 내용만 추출 (모델이 추가 설명을 붙일 수 있음)
        if 'Tags:' in content:
            content = content.split('Tags:')[-1].strip()

        # 첫 줄만 가져오기 (모델이 여러 줄로 응답할 수 있음)
        first_line = content.split('\n')[0].strip()

        # 쉼표로 구분하여 태그 리스트 생성
        tags = [tag.strip().lower() for tag in first_line.split(',') if tag.strip()]

        # 필터링
        tags = filter_tags(tags)

        return tags

    except Exception as e:
        print(f"  ❌ Error analyzing image: {e}")
        return []


def filter_tags(tags, min_length=2, max_tags=15):
    """
    태그 필터링 및 정제

    Args:
        tags (list): 원본 태그 리스트
        min_length (int): 최소 태그 길이
        max_tags (int): 최대 태그 개수

    Returns:
        list: 필터링된 태그 리스트
    """
    # 불용어 및 제외할 단어
    stopwords = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has',
        'example', 'format', 'tags', 'image', 'picture', 'photo'
    }

    filtered = []
    seen = set()

    for tag in tags:
        # 정규화
        tag = tag.lower().strip()
        tag = tag.replace('_', ' ')  # 언더스코어를 공백으로

        # 조건 확인
        if len(tag) < min_length:
            continue
        if tag in stopwords:
            continue
        if tag in seen:
            continue

        # 특수문자만으로 구성된 태그 제외
        if not any(c.isalnum() for c in tag):
            continue

        filtered.append(tag)
        seen.add(tag)

    # 최대 개수 제한
    return filtered[:max_tags]


def add_tags_to_image(image_id, tags_list, dry_run=False):
    """
    이미지에 태그 추가

    Args:
        image_id (int): Image 모델의 ID
        tags_list (list): 추가할 태그 리스트
        dry_run (bool): True면 실제로 저장하지 않음

    Returns:
        bool: 성공 여부
    """
    try:
        image = Image.query.get(image_id)
        if not image:
            print(f"  ⚠️  Image ID {image_id} not found")
            return False

        added_tags = []

        for tag_name in tags_list:
            # 기존 태그 확인
            tag = Tag.query.filter_by(name=tag_name).first()

            # 태그가 없으면 생성
            if not tag:
                tag = Tag(name=tag_name)
                if not dry_run:
                    db.session.add(tag)

            # 이미지에 이미 태그가 있는지 확인
            if tag not in image.tags:
                if not dry_run:
                    image.tags.append(tag)
                added_tags.append(tag_name)

        if not dry_run and added_tags:
            db.session.commit()

        if added_tags:
            print(f"  ✅ Added {len(added_tags)} tags: {', '.join(added_tags)}")
        else:
            print(f"  ℹ️  No new tags to add")

        return True

    except Exception as e:
        print(f"  ❌ Error adding tags: {e}")
        if not dry_run:
            db.session.rollback()
        return False


def auto_tag_all_images(untagged_only=True, limit=None):
    """
    모든 이미지에 자동으로 태그 추가

    Args:
        untagged_only (bool): True면 태그 없는 이미지만 처리
        limit (int): 처리할 최대 이미지 수 (None이면 전체)
    """
    print("=" * 80)
    print("🚀 Gemma 3 자동 태깅 시작")
    print("=" * 80)
    print(f"모델: {OLLAMA_MODEL}")
    print(f"Ready 폴더: {READY_FOLDER}")
    print(f"태그 없는 이미지만: {untagged_only}")
    print(f"Dry Run 모드: {DRY_RUN}")
    if limit:
        print(f"처리 제한: {limit}개")
    print("=" * 80)
    print()

    # Ollama 연결 확인
    # try:
    #     models = ollama.list()
    #     model_names = [m['name'] for m in models.get('models', [])]
    #     if OLLAMA_MODEL not in model_names:
    #         print(f"❌ Error: 모델 '{OLLAMA_MODEL}'를 찾을 수 없습니다.")
    #         print(f"사용 가능한 모델: {', '.join(model_names)}")
    #         return
    #     print(f"✅ Ollama 연결 성공\n")
    # except Exception as e:
    #     print(f"❌ Error: Ollama에 연결할 수 없습니다: {e}")
    #     print("Ollama가 실행 중인지 확인하세요: ollama serve")
    #     return

    with app.app_context():
        # 처리할 이미지 가져오기
        if untagged_only:
            query = Image.query.filter(~Image.tags.any())
        else:
            query = Image.query

        if limit:
            images = query.limit(limit).all()
        else:
            images = query.all()

        total = len(images)

        if total == 0:
            print("처리할 이미지가 없습니다.")
            return

        print(f"📊 처리할 이미지: {total}개\n")

        success_count = 0
        failed_count = 0
        skipped_count = 0

        for idx, image in enumerate(images, 1):
            print(f"[{idx}/{total}] {image.original_filename}")

            # 이미지 경로
            image_path = os.path.join(READY_FOLDER, image.filename)

            if not os.path.exists(image_path):
                print(f"  ⚠️  파일 없음: {image_path}")
                skipped_count += 1
                print()
                continue

            try:
                # VLM으로 태그 생성
                start_time = time.time()
                tags = analyze_image_with_gemma(image_path)
                elapsed = time.time() - start_time

                if not tags:
                    print(f"  ⚠️  태그 생성 실패")
                    failed_count += 1
                    print()
                    continue

                print(f"  🏷️  생성된 태그 ({len(tags)}개): {', '.join(tags)}")
                print(f"  ⏱️  처리 시간: {elapsed:.2f}초")

                # DB에 태그 추가
                if add_tags_to_image(image.id, tags, dry_run=DRY_RUN):
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"  ❌ 오류: {e}")
                failed_count += 1

            print()

            # 배치 간 대기 (API 과부하 방지)
            if idx < total:
                time.sleep(BATCH_DELAY)

    # 결과 출력
    print("=" * 80)
    print("📊 자동 태깅 완료")
    print("=" * 80)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {failed_count}개")
    print(f"⚠️  스킵: {skipped_count}개")
    print(f"📊 총계: {total}개")
    print("=" * 80)

    if DRY_RUN:
        print("\n⚠️  DRY RUN 모드로 실행되었습니다. DB에 저장되지 않았습니다.")
        print("실제 저장하려면 스크립트에서 DRY_RUN = False로 설정하세요.")


def test_single_image(image_filename):
    """
    단일 이미지 테스트용

    Args:
        image_filename (str): 이미지 파일명
    """
    print(f"🧪 테스트 모드: {image_filename}")
    print("=" * 80)

    image_path = os.path.join(READY_FOLDER, image_filename)

    if not os.path.exists(image_path):
        print(f"❌ 파일 없음: {image_path}")
        return

    print(f"이미지 경로: {image_path}\n")

    # 태그 생성
    tags = analyze_image_with_gemma(image_path)

    print(f"\n생성된 태그 ({len(tags)}개):")
    for i, tag in enumerate(tags, 1):
        print(f"  {i}. {tag}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Gemma 3 VLM 자동 이미지 태깅')
    parser.add_argument('--all', action='store_true', help='이미 태그된 이미지도 재처리')
    parser.add_argument('--limit', type=int, help='처리할 최대 이미지 수')
    parser.add_argument('--test', type=str, help='단일 이미지 테스트 (파일명)')
    parser.add_argument('--dry-run', action='store_true', help='DB에 저장하지 않고 출력만')

    args = parser.parse_args()

    if args.dry_run:
        DRY_RUN = True

    if args.test:
        # 테스트 모드
        test_single_image(args.test)
    else:
        # 일괄 처리 모드
        auto_tag_all_images(
            untagged_only=not args.all,
            limit=args.limit
        )

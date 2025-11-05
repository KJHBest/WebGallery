# VLM 자동 태깅 가이드

이 문서는 로컬 VLM (Vision Language Model)을 사용하여 이미지 갤러리에 자동으로 태그를 추가하는 방법을 설명합니다.

## 시스템 구조

### 현재 데이터베이스 스키마

```python
# Image 모델
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.relationship('Tag', secondary=image_tags, backref='images')

# Tag 모델
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
```

### 이미지 위치
- **Ready 폴더**: `static/ready`
- 이 폴더의 이미지들이 자동으로 DB에 등록됨

---

## 방법 1: 스탠드얼론 스크립트로 태그 추가

### 예제: Gemma VLM 사용

```python
# auto_tag_images.py

import os
from app import app, db
from models import Image, Tag
from PIL import Image as PILImage

# VLM 라이브러리 예제 (실제 사용하는 라이브러리에 맞게 수정)
# 예: ollama, transformers, llama-cpp-python 등
import ollama  # 또는 다른 VLM 라이브러리

def analyze_image_with_vlm(image_path):
    """
    VLM을 사용하여 이미지를 분석하고 태그 생성

    Args:
        image_path: 이미지 파일 경로

    Returns:
        list: 태그 리스트 (예: ['portrait', 'woman', 'outdoor', 'sunset'])
    """

    # Ollama/Gemma 예제
    response = ollama.chat(
        model='llava',  # 또는 'gemma-vision' 등
        messages=[{
            'role': 'user',
            'content': 'Analyze this image and provide relevant tags. Return only comma-separated tags (e.g., portrait,woman,outdoor,sunset). Focus on: subject, style, mood, colors, composition.',
            'images': [image_path]
        }]
    )

    # 응답에서 태그 추출
    tags_string = response['message']['content'].strip()
    tags = [tag.strip().lower() for tag in tags_string.split(',')]

    return tags


def add_tags_to_image(image_id, tags_list):
    """
    이미지에 태그 추가

    Args:
        image_id: Image 모델의 ID
        tags_list: 추가할 태그 리스트
    """
    with app.app_context():
        image = Image.query.get(image_id)
        if not image:
            print(f"Image ID {image_id} not found")
            return

        for tag_name in tags_list:
            # 기존 태그 확인
            tag = Tag.query.filter_by(name=tag_name).first()

            # 태그가 없으면 생성
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)

            # 이미지에 이미 태그가 있는지 확인
            if tag not in image.tags:
                image.tags.append(tag)

        db.session.commit()
        print(f"Added tags to {image.original_filename}: {', '.join(tags_list)}")


def auto_tag_all_images():
    """모든 태그되지 않은 이미지에 자동으로 태그 추가"""
    ready_folder = 'static/ready'

    with app.app_context():
        # 태그가 없는 이미지만 가져오기
        images = Image.query.filter(~Image.tags.any()).all()

        print(f"Found {len(images)} images without tags")

        for idx, image in enumerate(images, 1):
            print(f"\n[{idx}/{len(images)}] Processing: {image.original_filename}")

            # 이미지 경로
            image_path = os.path.join(ready_folder, image.filename)

            if not os.path.exists(image_path):
                print(f"  ⚠️  File not found: {image_path}")
                continue

            try:
                # VLM으로 태그 생성
                tags = analyze_image_with_vlm(image_path)
                print(f"  Generated tags: {', '.join(tags)}")

                # DB에 태그 추가
                add_tags_to_image(image.id, tags)
                print(f"  ✓ Tags added successfully")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue


if __name__ == '__main__':
    print("Starting auto-tagging process...")
    auto_tag_all_images()
    print("\nAuto-tagging completed!")
```

### 실행 방법

```bash
# 1. 가상환경 활성화 (필요시)
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 2. VLM 라이브러리 설치
pip install ollama  # 또는 사용하는 VLM 라이브러리

# 3. 스크립트 실행
python auto_tag_images.py
```

---

## 방법 2: 웹 인터페이스로 태그 추가

앱에 API 엔드포인트를 추가하여 웹에서 태그를 생성할 수 있습니다.

### app.py에 추가할 코드

```python
@app.route('/api/image/<int:image_id>/auto-tag', methods=['POST'])
def auto_tag_image(image_id):
    """특정 이미지에 자동 태그 추가"""
    image = Image.query.get_or_404(image_id)

    # 이미지 경로
    image_path = os.path.join(app.config['READY_FOLDER'], image.filename)

    if not os.path.exists(image_path):
        return jsonify({'error': 'Image file not found'}), 404

    try:
        # VLM으로 태그 생성 (함수는 위에서 정의)
        tags = analyze_image_with_vlm(image_path)

        # 태그 추가
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)

            if tag not in image.tags:
                image.tags.append(tag)

        db.session.commit()

        return jsonify({
            'success': True,
            'tags': tags,
            'message': f'Added {len(tags)} tags'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-tag-all', methods=['POST'])
def auto_tag_all():
    """모든 태그 없는 이미지에 자동 태그 추가 (백그라운드 작업 권장)"""
    images = Image.query.filter(~Image.tags.any()).all()

    tagged_count = 0
    for image in images:
        image_path = os.path.join(app.config['READY_FOLDER'], image.filename)

        if not os.path.exists(image_path):
            continue

        try:
            tags = analyze_image_with_vlm(image_path)

            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)

                if tag not in image.tags:
                    image.tags.append(tag)

            db.session.commit()
            tagged_count += 1

        except Exception:
            continue

    return jsonify({
        'success': True,
        'tagged_count': tagged_count,
        'total': len(images)
    })
```

---

## 방법 3: 배치 처리 (대용량)

대량의 이미지를 처리할 때는 배치로 처리하는 것이 효율적입니다.

```python
# batch_auto_tag.py

import os
import time
from app import app, db
from models import Image, Tag

# VLM 라이브러리
import ollama

def batch_analyze_images(image_paths, batch_size=10):
    """배치로 이미지 분석"""
    results = []

    for i in range(0, len(image_paths), batch_size):
        batch = image_paths[i:i+batch_size]

        for image_path in batch:
            try:
                tags = analyze_image_with_vlm(image_path)
                results.append({
                    'path': image_path,
                    'tags': tags,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'path': image_path,
                    'error': str(e),
                    'success': False
                })

        # API rate limit 방지
        time.sleep(1)

    return results


def process_batch():
    """배치 처리 메인 함수"""
    ready_folder = 'static/ready'

    with app.app_context():
        # 처리할 이미지 가져오기
        images = Image.query.filter(~Image.tags.any()).all()

        print(f"Processing {len(images)} images in batches...")

        # 이미지 경로 리스트 생성
        image_data = []
        for image in images:
            image_path = os.path.join(ready_folder, image.filename)
            if os.path.exists(image_path):
                image_data.append({
                    'id': image.id,
                    'path': image_path,
                    'filename': image.original_filename
                })

        # 배치 분석
        results = batch_analyze_images([img['path'] for img in image_data])

        # DB 업데이트
        success_count = 0
        for img_data, result in zip(image_data, results):
            if not result['success']:
                print(f"✗ Failed: {img_data['filename']}")
                continue

            try:
                image = Image.query.get(img_data['id'])

                for tag_name in result['tags']:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)

                    if tag not in image.tags:
                        image.tags.append(tag)

                db.session.commit()
                success_count += 1
                print(f"✓ Tagged: {img_data['filename']} ({len(result['tags'])} tags)")

            except Exception as e:
                print(f"✗ DB Error for {img_data['filename']}: {e}")
                db.session.rollback()

        print(f"\nCompleted: {success_count}/{len(image_data)} images tagged")


if __name__ == '__main__':
    process_batch()
```

---

## VLM 모델 선택지

### 1. Ollama (추천)
```bash
# Ollama 설치
# https://ollama.ai

# 모델 다운로드
ollama pull llava
ollama pull bakllava

# Python 사용
pip install ollama
```

### 2. Transformers (Hugging Face)
```bash
pip install transformers torch pillow

# 모델 예제: BLIP, CLIP
```

```python
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

def analyze_with_blip(image_path):
    image = Image.open(image_path).convert('RGB')
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    # caption을 태그로 변환하는 로직 추가
    return caption.split()
```

### 3. LLaMA.cpp
```bash
pip install llama-cpp-python
```

---

## 프롬프트 엔지니어링 팁

VLM에 보내는 프롬프트를 개선하여 더 나은 태그를 생성할 수 있습니다.

```python
def get_tagging_prompt():
    """최적화된 태그 생성 프롬프트"""
    return """Analyze this image and generate relevant tags.

Focus on:
- Main subject (person, object, animal, etc.)
- Style (realistic, anime, 3D, painting, photo, etc.)
- Mood/Atmosphere (happy, dark, dramatic, peaceful, etc.)
- Colors (vibrant, monochrome, warm, cool, etc.)
- Composition (portrait, landscape, close-up, etc.)
- Setting/Location (indoor, outdoor, urban, nature, etc.)
- Action/Activity (standing, running, sitting, etc.)

Return ONLY comma-separated tags in lowercase.
Example format: portrait,woman,outdoor,sunset,dramatic,warm colors

Tags (max 10):"""
```

---

## 태그 품질 개선

### 태그 필터링
```python
def filter_tags(tags, min_length=3, max_tags=15):
    """태그 필터링 및 정제"""
    # 불용어 제거
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at'}

    filtered = []
    for tag in tags:
        tag = tag.lower().strip()

        # 조건 확인
        if len(tag) < min_length:
            continue
        if tag in stopwords:
            continue
        if tag in filtered:
            continue

        filtered.append(tag)

    # 최대 개수 제한
    return filtered[:max_tags]
```

### 태그 정규화
```python
def normalize_tag(tag):
    """태그 정규화"""
    # 특수문자 제거
    import re
    tag = re.sub(r'[^\w\s-]', '', tag)

    # 공백을 하이픈으로
    tag = tag.replace(' ', '-')

    # 소문자 변환
    tag = tag.lower()

    return tag
```

---

## 실행 예제

```bash
# 1. 모든 태그 없는 이미지에 자동 태그 추가
python auto_tag_images.py

# 2. 배치 처리로 대량 이미지 처리
python batch_auto_tag.py

# 3. 특정 이미지만 처리
python -c "from auto_tag_images import add_tags_to_image; add_tags_to_image(123, ['portrait', 'woman', 'outdoor'])"
```

---

## 주의사항

1. **API Rate Limit**: VLM API 사용 시 rate limit 확인
2. **배치 크기**: 한 번에 너무 많은 이미지를 처리하면 메모리 문제 발생 가능
3. **태그 중복**: 동일한 태그가 중복 생성되지 않도록 확인
4. **에러 처리**: VLM 분석 실패 시 적절한 에러 처리 필요
5. **성능**: 로컬 VLM은 GPU 사용 시 훨씬 빠름 (CUDA 설정)

---

## 문제 해결

### VLM이 너무 느림
- GPU 가속 활성화
- 더 작은 모델 사용 (llava vs llava:7b vs llava:13b)
- 배치 크기 조정

### 태그 품질이 낮음
- 프롬프트 개선
- 다른 VLM 모델 시도
- 후처리 필터링 강화

### DB 연결 오류
```python
# app context 확인
with app.app_context():
    # DB 작업
    pass
```

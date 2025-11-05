# Gemma 3 자동 태깅 사용 가이드

## 설치

### 1. Ollama 설치 및 모델 다운로드

이미 다운로드하셨다고 했지만, 확인 방법:

```bash
# Ollama 실행 확인
ollama serve

# 다른 터미널에서 모델 확인
ollama list

# gemma3:27b-it-q8_0 모델이 목록에 있어야 함
```

### 2. Python 라이브러리 설치

```bash
# 프로젝트 디렉토리에서
pip install ollama
```

---

## 사용 방법

### 기본 사용 (태그 없는 이미지만 처리)

```bash
python auto_tag_gemma.py
```

### 모든 이미지 재처리

```bash
python auto_tag_gemma.py --all
```

### 처리 개수 제한 (테스트용)

```bash
# 처음 10개만 처리
python auto_tag_gemma.py --limit 10
```

### Dry Run 모드 (DB에 저장하지 않고 테스트)

```bash
python auto_tag_gemma.py --dry-run --limit 5
```

### 단일 이미지 테스트

```bash
# 특정 이미지 하나만 테스트
python auto_tag_gemma.py --test "ComfyUI_00001_.png"
```

---

## 예제 출력

### 일괄 처리

```
================================================================================
🚀 Gemma 3 자동 태깅 시작
================================================================================
모델: gemma3:27b-it-q8_0
Ready 폴더: static/ready
태그 없는 이미지만: True
Dry Run 모드: False
================================================================================

✅ Ollama 연결 성공

📊 처리할 이미지: 50개

[1/50] anime_girl_001.png
  🔍 Analyzing with Gemma3...
  🏷️  생성된 태그 (12개): 1girl, pink hair, long hair, bunny girl, black stockings, white gloves, sitting, indoor, neon lights, night, cyberpunk, smile
  ⏱️  처리 시간: 3.24초
  ✅ Added 12 tags: 1girl, pink hair, long hair, bunny girl, black stockings, white gloves, sitting, indoor, neon lights, night, cyberpunk, smile

[2/50] mecha_battle.png
  🔍 Analyzing with Gemma3...
  🏷️  생성된 태그 (10개): 1girl, white hair, short hair, mecha suit, armor, rifle, outdoor, explosion, action, dramatic
  ⏱️  처리 시간: 3.18초
  ✅ Added 10 tags: 1girl, white hair, short hair, mecha suit, armor, rifle, outdoor, explosion, action, dramatic

...

================================================================================
📊 자동 태깅 완료
================================================================================
✅ 성공: 48개
❌ 실패: 1개
⚠️  스킵: 1개
📊 총계: 50개
================================================================================
```

### 단일 이미지 테스트

```
🧪 테스트 모드: test_image.png
================================================================================
이미지 경로: static/ready\test_image.png

  🔍 Analyzing with Gemma3...

생성된 태그 (13개):
  1. 1girl
  2. silver hair
  3. long hair
  4. maid outfit
  5. red eyes
  6. holding tray
  7. indoor
  8. mansion
  9. elegant
  10. standing
  11. smile
  12. apron
  13. headband

================================================================================
```

---

## 설정 커스터마이징

`auto_tag_gemma.py` 파일 상단의 설정을 수정할 수 있습니다:

```python
# 모델 설정
OLLAMA_MODEL = "gemma3:27b-it-q8_0"  # 사용할 모델

# 폴더 설정
READY_FOLDER = 'static/ready'  # 이미지 폴더

# 성능 설정
BATCH_DELAY = 0.5  # 이미지 간 대기 시간 (초)

# 테스트 설정
DRY_RUN = False  # True로 설정하면 DB에 저장 안함
```

---

## 프롬프트 커스터마이징

더 나은 태그를 얻으려면 `get_tagging_prompt()` 함수를 수정하세요:

```python
def get_tagging_prompt():
    return """Analyze this anime/illustration image...

    # 여기에 원하는 카테고리 추가
    # 예: 6. ACCESSORIES: glasses, earrings, necklace, hat

    Tags:"""
```

### 추가 가능한 카테고리

- **표정**: smile, angry, sad, surprised, neutral
- **액세서리**: glasses, earrings, necklace, hat, gloves
- **포즈**: standing, sitting, lying, running, fighting
- **배경**: city, beach, forest, room, street
- **시간대**: morning, noon, sunset, night
- **날씨**: sunny, cloudy, rainy, snowy
- **아트 스타일**: cel shading, watercolor, sketch, 3d render

---

## 태그 필터링 수정

특정 태그를 제외하고 싶다면 `filter_tags()` 함수의 `stopwords`에 추가:

```python
stopwords = {
    'a', 'an', 'the', 'and', 'or', 'but',
    # 제외할 태그 추가
    'example', 'sample', 'test'
}
```

---

## 성능 최적화

### GPU 사용

Ollama는 자동으로 GPU를 사용하지만, 확인 방법:

```bash
# Ollama 로그 확인
ollama ps

# GPU 사용 확인
nvidia-smi  # NVIDIA GPU의 경우
```

### 처리 속도

- **gemma3:27b-it-q8_0**: 이미지당 약 3-5초 (GPU 기준)
- 100개 이미지: 약 5-10분
- 1000개 이미지: 약 50-100분

### 배치 처리 최적화

많은 이미지를 처리할 때:

1. **밤에 실행**: 장시간 처리 필요
2. **limit 옵션**: 먼저 소량으로 테스트
3. **BATCH_DELAY 조정**: 시스템 부하에 따라 조정

```bash
# 10개씩 나눠서 처리
python auto_tag_gemma.py --limit 10
# 결과 확인 후
python auto_tag_gemma.py --limit 20
# ...
```

---

## 문제 해결

### 1. "Ollama에 연결할 수 없습니다"

```bash
# Ollama 서버 시작
ollama serve

# 다른 터미널에서 스크립트 실행
python auto_tag_gemma.py
```

### 2. "모델을 찾을 수 없습니다"

```bash
# 모델 목록 확인
ollama list

# 모델명이 정확한지 확인
# 스크립트의 OLLAMA_MODEL 변수 수정
```

### 3. 태그 품질이 낮음

- 프롬프트를 더 구체적으로 수정
- 다른 이미지로 테스트
- 모델 온도 조정 (고급)

### 4. 처리 속도가 느림

- GPU 사용 확인
- 더 작은 모델 사용 (gemma3:9b 등)
- BATCH_DELAY 줄이기

### 5. 메모리 부족

- 한 번에 처리하는 개수 줄이기 (`--limit` 사용)
- Ollama 재시작
- 시스템 메모리 확인

---

## 고급 사용법

### Python에서 직접 호출

```python
from auto_tag_gemma import analyze_image_with_gemma, add_tags_to_image
from app import app

# 단일 이미지 분석
tags = analyze_image_with_gemma("static/ready/test.png")
print(tags)

# DB에 추가
with app.app_context():
    add_tags_to_image(image_id=123, tags_list=tags)
```

### 특정 조건의 이미지만 처리

```python
# auto_tag_gemma.py 수정

with app.app_context():
    # 조회수 많은 이미지만
    images = Image.query.filter(Image.views > 100).all()

    # 특정 날짜 이후 이미지만
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    images = Image.query.filter(Image.created_at > week_ago).all()
```

---

## 웹 UI에 통합 (선택사항)

버튼 클릭으로 태깅하고 싶다면 `app.py`에 추가:

```python
from auto_tag_gemma import analyze_image_with_gemma, add_tags_to_image

@app.route('/api/image/<int:image_id>/auto-tag', methods=['POST'])
def api_auto_tag(image_id):
    """특정 이미지에 자동 태그 추가"""
    image = Image.query.get_or_404(image_id)
    image_path = os.path.join(app.config['READY_FOLDER'], image.filename)

    if not os.path.exists(image_path):
        return jsonify({'error': 'Image not found'}), 404

    try:
        tags = analyze_image_with_gemma(image_path)
        add_tags_to_image(image_id, tags)
        return jsonify({'success': True, 'tags': tags})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 팁

1. **처음에는 테스트**: `--test`와 `--dry-run`으로 먼저 확인
2. **소량부터**: `--limit 10`으로 결과 확인 후 전체 실행
3. **프롬프트 개선**: 원하는 태그가 안 나오면 프롬프트 수정
4. **정기 실행**: 새 이미지 추가 시 정기적으로 실행
5. **백업**: DB 백업 후 실행 권장

```bash
# DB 백업
cp gallery.db gallery.db.backup

# 태깅 실행
python auto_tag_gemma.py

# 문제 발생 시 복구
cp gallery.db.backup gallery.db
```

---

## 예상 태그 예제

### 바니걸 이미지
```
1girl, pink hair, long hair, bunny girl, bunny ears, black leotard,
white gloves, black stockings, high heels, indoor, stage, spotlight
```

### 메이드복 이미지
```
1girl, silver hair, braided hair, maid outfit, apron, headband,
tea cup, tray, indoor, mansion, elegant, smile
```

### 메카물 이미지
```
1girl, blue hair, short hair, mecha suit, armor, helmet, rifle,
outdoor, battlefield, smoke, explosion, action pose
```

### 바이크 이미지
```
1girl, red hair, ponytail, motorcycle, leather jacket, helmet,
outdoor, highway, sunset, speed, motion blur
```

---

## 문의 및 개선

- 태그 품질이 만족스럽지 않으면 프롬프트 수정
- 새로운 카테고리가 필요하면 `get_tagging_prompt()` 수정
- 성능 문제는 BATCH_DELAY나 limit 조정

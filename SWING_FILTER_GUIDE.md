# 🎯 스윙 검증 필터링 완화 가이드

## ✅ 변경 사항

스윙 영상 검증 필터링이 **기본적으로 완화**되었습니다.

### 이전 설정
- 포즈 감지 실패 시 → **에러 반환**
- 백스윙 각도 < 40도 → **필터링**
- 어깨 회전 < 15도 → **필터링**
- 어깨 간 거리 < 0.05 → **필터링**

### 현재 설정 (완화됨)
- 포즈 감지 실패 시 → **기본값으로 진행** (완화)
- 필터링 → **기본적으로 비활성화**
- 필터링 활성화 시에도 기준값이 매우 낮음 (10도, 3도 등)

---

## 🔧 환경변수 설정

### 1. 포즈 감지 완화

**기본값**: 포즈를 감지하지 못해도 계속 진행

```bash
# 엄격 모드 (포즈 감지 실패 시 에러 반환)
export STRICT_POSE_DETECTION=true
```

### 2. 필터링 활성화/비활성화

**기본값**: 필터링 비활성화 (모든 영상 허용)

```bash
# 필터링 활성화 (완화된 기준 적용)
export ENABLE_SWING_FILTER=true

# 필터링 비활성화 (기본값 - 모든 영상 허용)
export ENABLE_SWING_FILTER=false
```

### 3. 필터링 기준값 조정

필터링을 활성화한 경우, 기준값을 조정할 수 있습니다:

```bash
# 백스윙 각도 최소 기준 (기본: 10도)
export MIN_BACKSWING_ANGLE=10.0

# 어깨 회전 범위 최소 기준 (기본: 3도)
export MIN_SHOULDER_ROT=3.0

# 골반 회전 범위 최소 기준 (기본: 1도)
export MIN_HIP_ROT=1.0

# 어깨 간 거리 최소 비율 (기본: 0.01)
export MIN_SHOULDER_SPAN=0.01
```

---

## 📋 사용 예시

### 완화 모드 (기본값 - 모든 영상 허용)

```bash
# 환경변수 설정 없이 실행하면 완화 모드로 동작
python app.py
```

### 약간의 필터링 적용

```bash
# .env 파일에 추가하거나
ENABLE_SWING_FILTER=true
MIN_BACKSWING_ANGLE=20.0
MIN_SHOULDER_ROT=5.0
```

### 완전한 필터링 비활성화

```bash
# 기본값이므로 별도 설정 불필요
# 또는 명시적으로
ENABLE_SWING_FILTER=false
STRICT_POSE_DETECTION=false
```

---

## 🚀 EC2 서버에서 설정

### PM2 사용 시

`ecosystem.config.js`에 환경변수 추가:

```javascript
{
  name: 'inswing-ai',
  script: 'app.py',
  interpreter: 'python3',
  env: {
    ENABLE_SWING_FILTER: 'false',          // 필터링 비활성화
    STRICT_POSE_DETECTION: 'false',        // 포즈 감지 완화
  }
}
```

또는 `.env` 파일에 추가:

```bash
cd ~/inswing-ai
echo "ENABLE_SWING_FILTER=false" >> .env
echo "STRICT_POSE_DETECTION=false" >> .env
```

---

## ⚙️ 권장 설정

### 개발/테스트 환경
```bash
ENABLE_SWING_FILTER=false          # 모든 영상 허용
STRICT_POSE_DETECTION=false        # 포즈 감지 완화
```

### 운영 환경 (약간의 필터링)
```bash
ENABLE_SWING_FILTER=true           # 필터링 활성화
MIN_BACKSWING_ANGLE=20.0           # 완화된 기준
MIN_SHOULDER_ROT=5.0
MIN_HIP_ROT=2.0
STRICT_POSE_DETECTION=false        # 포즈 감지 완화
```

### 엄격한 필터링 (이전 동작)
```bash
ENABLE_SWING_FILTER=true
MIN_BACKSWING_ANGLE=40.0           # 엄격한 기준
MIN_SHOULDER_ROT=15.0
MIN_HIP_ROT=5.0
MIN_SHOULDER_SPAN=0.05
STRICT_POSE_DETECTION=true         # 포즈 감지 엄격
```

---

## 📝 변경 요약

| 설정 | 이전 | 현재 (완화) |
|------|------|-------------|
| 포즈 감지 실패 | 에러 반환 | 기본값으로 진행 |
| 필터링 기본값 | 활성화 | **비활성화** |
| 백스윙 기준 | 40도 | 10도 (활성화 시) |
| 어깨 회전 기준 | 15도 | 3도 (활성화 시) |
| 골반 회전 기준 | 5도 | 1도 (활성화 시) |
| 어깨 간 거리 기준 | 0.05 | 0.01 (활성화 시) |

---

## ⚠️ 주의사항

1. **필터링을 완전히 비활성화하면** 모든 영상이 허용됩니다 (스윙이 아닌 영상도 포함)
2. **포즈를 전혀 감지하지 못한 경우** 기본값(더미 메트릭)으로 분석이 진행됩니다
3. **운영 환경에서는** 적절한 필터링을 활성화하는 것을 권장합니다

---

## 🔄 변경 사항 적용

코드 변경 후 서버 재시작:

```bash
# PM2 사용 시
pm2 restart inswing-ai

# 직접 실행 시
# 서버 중지 후 재시작
```


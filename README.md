# INSWING AI Analysis Server

골프 스윙 비디오를 분석하는 AI 서버입니다. MediaPipe를 사용하여 스윙 동작을 추적하고 15개의 메트릭을 추출합니다.

## 🚀 기능

- **MediaPipe 기반 포즈 추정**: 33개 랜드마크로 골퍼의 자세 추적
- **15개 메트릭 추출**: 백스윙 각도, 임팩트 속도, 템포, 밸런스 등
- **Flask REST API**: 비디오 업로드 및 분석 결과 반환
- **PM2 프로세스 관리**: 자동 재시작 및 모니터링

## 📋 요구사항

- Python 3.9 이상
- OpenCV
- MediaPipe
- NumPy
- Flask

## 🔧 설치

```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 🏃 실행

### 개발 모드
```bash
python app.py
```

### 프로덕션 모드 (PM2 사용)
```bash
pm2 start ecosystem.config.js
pm2 status
pm2 logs inswing-ai
```

## 📡 API 엔드포인트

### `GET /`
서비스 정보 반환
```json
{
  "service": "INSWING AI Analysis Server",
  "version": "1.0",
  "status": "running"
}
```

### `GET /health`
헬스체크
```json
{
  "status": "healthy"
}
```

### `POST /analyze`
비디오 분석

**Request:**
- Content-Type: `multipart/form-data`
- Field: `video` (파일)

**Response:**
```json
{
  "ok": true,
  "analysis": {
    "backswing_angle": 120.5,
    "impact_speed": 95.3,
    "follow_through_angle": 135.2,
    "balance_score": 0.87,
    "tempo_ratio": 2.8,
    "backswing_time_sec": 1.2,
    "downswing_time_sec": 0.43,
    "head_movement_pct": 12.5,
    "shoulder_rotation_range": 85.3,
    "hip_rotation_range": 42.1,
    "rotation_efficiency": 75,
    "overall_score": 82,
    "frames_analyzed": 90,
    "total_frames": 90
  }
}
```

## 📊 추출 메트릭

### v1 기본 메트릭 (4개)
1. **backswing_angle**: 백스윙 각도 (어깨-팔꿈치-손목)
2. **impact_speed**: 임팩트 속도 (손목 이동 거리 기반)
3. **follow_through_angle**: 팔로우스루 각도 (어깨-엉덩이-팔꿈치)
4. **balance_score**: 밸런스 점수 (0~1, 엉덩이 수평 유지)

### v2 확장 메트릭 (11개)
5. **tempo_ratio**: 템포 비율 (백스윙:다운스윙 시간)
6. **backswing_time_sec**: 백스윙 시간 (초)
7. **downswing_time_sec**: 다운스윙 시간 (초)
8. **head_movement_pct**: 머리 흔들림 (%)
9. **shoulder_rotation_range**: 어깨 회전 범위 (도)
10. **hip_rotation_range**: 골반 회전 범위 (도)
11. **rotation_efficiency**: 회전 효율 점수 (0~100)
12. **overall_score**: 종합 스윙 점수 (0~100)

## 🔍 분석 알고리즘

1. **포즈 추정**: MediaPipe Pose로 33개 랜드마크 추출
2. **주요 포인트**: 어깨, 팔꿈치, 손목, 엉덩이, 코(머리)
3. **탑 위치 탐색**: 손목 y 좌표 최소값
4. **임팩트 추정**: 탑 이후 최대 속도 지점
5. **메트릭 계산**: 각도, 속도, 위치 기반 계산
6. **종합 점수**: 가중 평균으로 0~100 점수 산출

## 🧪 테스트

```bash
# MediaPipe 테스트
python test_mediapipe.py

# 서버 테스트
python test_server.py
```

## 📁 프로젝트 구조

```
inswing-ai/
├── app.py                 # Flask 서버
├── analyze_swing.py       # MediaPipe 분석 로직
├── ecosystem.config.js    # PM2 설정
├── test_server.py         # 서버 테스트
├── test_mediapipe.py      # MediaPipe 테스트
├── requirements.txt       # Python 의존성
└── README.md              # 프로젝트 문서
```

## 🔄 EC2 배포

### 서버 설정
- 포트: 5000
- 호스트: 0.0.0.0 (외부 접근 허용)
- 프로세스 관리: PM2

### PM2 명령어
```bash
# 시작
pm2 start ecosystem.config.js

# 재시작
pm2 restart inswing-ai

# 중지
pm2 stop inswing-ai

# 로그 확인
pm2 logs inswing-ai

# 상태 확인
pm2 status
```

## 🔗 연동

이 서버는 `inswing-api`의 `/swings` 엔드포인트에서 호출됩니다:

```javascript
// inswing-api/routes/swings.js
const aiResponse = await axios.post(
  'http://localhost:5000/analyze',
  formData,
  { headers: formData.getHeaders(), timeout: 900000 }
);
```

## 📝 참고사항

- 오른손잡이 기준으로 분석 (왼손잡이는 코드 수정 필요)
- 비디오는 임시 저장 후 분석 완료 시 자동 삭제
- 타임아웃: 900초 (15분)
- 메모리 제한: 500MB (PM2 설정)

## 🐛 문제 해결

### MediaPipe 설치 오류
```bash
pip install --upgrade pip
pip install mediapipe
```

### OpenCV 오류
```bash
pip install opencv-python-headless  # 서버 환경용
```

### 포트 충돌
```bash
# 포트 5000 사용 중인 프로세스 확인
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows
```

## 📄 라이선스

INSWING 프로젝트의 일부입니다.


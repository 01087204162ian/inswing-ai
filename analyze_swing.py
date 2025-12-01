import cv2
import mediapipe as mp
import numpy as np
import math

mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    """3개 포인트로 각도 계산 (a-b-c 기준 각도)"""
    a = np.array(a)  # 첫번째 포인트
    b = np.array(b)  # 중간 포인트 (꼭지점)
    c = np.array(c)  # 세번째 포인트

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
        a[1] - b[1], a[0] - b[0]
    )
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


def analyze_golf_swing(video_path):
    """골프 스윙 비디오 분석"""

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {"error": "비디오 파일을 열 수 없습니다"}

    # 비디오 정보
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        # fps 정보가 이상하면 대략 30fps로 가정
        fps = 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # v1 기본 메트릭
    backswing_angles = []
    impact_speeds = []
    follow_through_angles = []
    balance_scores = []

    # v2 확장 메트릭용
    shoulder_line_angles = []  # 어깨 라인 각도
    hip_line_angles = []       # 골반 라인 각도
    head_positions = []        # 머리 좌표 추적 (nose)
    wrist_positions = []       # 손목 좌표 추적 (tempo 계산용)
    wrist_frame_indices = []   # 손목 좌표에 대응하는 프레임 인덱스

    prev_wrist_pos = None
    max_shoulder_span = 0.0    # 화면 대비 좌우 어깨 간 거리의 최대값 (가까운 사람만 통과시키기 위함)

    with mp_pose.Pose(
        static_image_mode=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # RGB 변환
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            if not results.pose_landmarks:
                continue

            landmarks = results.pose_landmarks.landmark

            # 주요 포인트 추출
            left_shoulder = [landmarks[11].x, landmarks[11].y]
            right_shoulder = [landmarks[12].x, landmarks[12].y]
            left_elbow = [landmarks[13].x, landmarks[13].y]
            right_elbow = [landmarks[14].x, landmarks[14].y]
            left_wrist = [landmarks[15].x, landmarks[15].y]
            right_wrist = [landmarks[16].x, landmarks[16].y]
            left_hip = [landmarks[23].x, landmarks[23].y]
            right_hip = [landmarks[24].x, landmarks[24].y]
            nose = [landmarks[0].x, landmarks[0].y]

            # 오른손잡이 가정 (왼손잡이는 반대)
            shoulder = right_shoulder
            elbow = right_elbow
            wrist = right_wrist
            hip = right_hip

            # ---- v1 메트릭 ----

            # 1) 백스윙 각도 (어깨-팔꿈치-손목)
            angle = calculate_angle(shoulder, elbow, wrist)
            backswing_angles.append(angle)

            # 2) 임팩트 속도 (손목 이동 거리)
            if prev_wrist_pos is not None:
                distance = math.sqrt(
                    (wrist[0] - prev_wrist_pos[0]) ** 2
                    + (wrist[1] - prev_wrist_pos[1]) ** 2
                )
                speed = distance * fps  # 픽셀/초 (정확한 단위는 아니지만 상대적 속도로 사용)
                impact_speeds.append(speed)
            prev_wrist_pos = wrist

            # 3) 팔로우스루 각도 (어깨-엉덩이-팔꿈치)
            follow_angle = calculate_angle(hip, shoulder, elbow)
            follow_through_angles.append(follow_angle)

            # 4) 밸런스 점수 (엉덩이 수평 유지)
            hip_balance = abs(left_hip[1] - right_hip[1])  # y 차이
            balance_scores.append(1 - hip_balance)  # 0~1 근처 값 (1에 가까울수록 좋음)

            # ---- v2 메트릭을 위한 추가 데이터 수집 ----

            # 어깨 라인 각도 (오른어깨→왼어깨)
            shoulder_dx = left_shoulder[0] - right_shoulder[0]
            shoulder_dy = left_shoulder[1] - right_shoulder[1]
            shoulder_angle = math.degrees(math.atan2(shoulder_dy, shoulder_dx))
            shoulder_line_angles.append(shoulder_angle)

            # 어깨 간 수평 거리 (사람이 화면에서 얼마나 크게 보이는지 추정)
            shoulder_span = abs(shoulder_dx)
            if shoulder_span > max_shoulder_span:
                max_shoulder_span = shoulder_span

            # 골반 라인 각도 (오른엉덩이→왼엉덩이)
            hip_dx = left_hip[0] - right_hip[0]
            hip_dy = left_hip[1] - right_hip[1]
            hip_angle = math.degrees(math.atan2(hip_dy, hip_dx))
            hip_line_angles.append(hip_angle)

            # 머리(코 기준) 위치
            head_positions.append(nose)

            # 템포 계산용 손목 위치 + 프레임 인덱스
            wrist_positions.append(wrist)
            wrist_frame_indices.append(frame_count)

    cap.release()

    # 결과 집계
    if len(backswing_angles) == 0:
        return {"error": "스윙 자세를 감지할 수 없습니다"}

    # ---------- v1 기본 메트릭 계산 ----------
    max_backswing_angle = round(max(backswing_angles), 2)

    if impact_speeds:
        max_impact_speed = round(max(impact_speeds), 2)
    else:
        max_impact_speed = 0.0

    max_follow_through_angle = round(max(follow_through_angles), 2)

    if balance_scores:
        balance_mean = float(np.mean(balance_scores))
        # 0~1 범위로 클램핑
        balance_mean = max(0.0, min(1.0, balance_mean))
        balance_score = round(balance_mean, 2)
    else:
        balance_score = 0.0

    # ---------- v2 확장 메트릭 계산 ----------

    # 1) 템포(백스윙/다운스윙 시간 + 비율)
    tempo_ratio = None
    backswing_time_sec = None
    downswing_time_sec = None

    if len(wrist_positions) >= 3 and fps > 0:
        # y 좌표를 기준으로 탑(top) 위치 탐색 (y가 작을수록 화면 위쪽)
        wrist_ys = [p[1] for p in wrist_positions]
        top_idx = int(np.argmin(wrist_ys))  # 탑 프레임의 인덱스

        start_frame = wrist_frame_indices[0]
        top_frame = wrist_frame_indices[top_idx]

        # 탑 이후 구간에서 손목 속도가 가장 큰 지점을 임팩트 근처로 가정
        speeds_for_tempo = []
        for i in range(1, len(wrist_positions)):
            dx = wrist_positions[i][0] - wrist_positions[i - 1][0]
            dy = wrist_positions[i][1] - wrist_positions[i - 1][1]
            dist = math.sqrt(dx * dx + dy * dy)
            speeds_for_tempo.append(dist * fps)

        impact_frame = None
        if top_idx < len(speeds_for_tempo):
            # top 이후 구간에서 최대 속도 찾기
            search_start = top_idx  # speeds_for_tempo는 i-1 인덱스 기준
            max_speed = -1
            max_speed_idx = None
            for j in range(search_start, len(speeds_for_tempo)):
                if speeds_for_tempo[j] > max_speed:
                    max_speed = speeds_for_tempo[j]
                    max_speed_idx = j

            if max_speed_idx is not None and max_speed_idx + 1 < len(wrist_frame_indices):
                impact_frame = wrist_frame_indices[max_speed_idx + 1]

        if impact_frame is not None and impact_frame > top_frame > start_frame:
            backswing_time_sec = round((top_frame - start_frame) / fps, 2)
            downswing_time_sec = round((impact_frame - top_frame) / fps, 2)
            if downswing_time_sec > 0:
                tempo_ratio = round(backswing_time_sec / downswing_time_sec, 2)

    # 2) 머리 흔들림 (head_movement_pct)
    head_movement_pct = None
    if head_positions:
        base_head = head_positions[0]
        max_dist = 0.0
        for p in head_positions:
            dx = p[0] - base_head[0]
            dy = p[1] - base_head[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > max_dist:
                max_dist = dist
        head_movement_pct = round(max_dist * 100.0, 2)  # 0~100% 정도의 스케일

    # 3) 어깨/골반 회전 범위
    shoulder_rotation_range = None
    hip_rotation_range = None

    if len(shoulder_line_angles) >= 2:
        shoulder_rotation_range = round(
            max(shoulder_line_angles) - min(shoulder_line_angles), 2
        )

    if len(hip_line_angles) >= 2:
        hip_rotation_range = round(
            max(hip_line_angles) - min(hip_line_angles), 2
        )

    # 스윙이 아닌 일반적인 움직임(작은 회전, 작은 백스윙 등)을 필터링하기 위한 최소 기준
    # 너무 엄격하면 정상 스윙도 막힐 수 있으니, 일단 느슨한 값으로 시작해서 현장에서 튜닝
    MIN_BACKSWING_ANGLE = 60.0      # 백스윙 최대 각도 최소 기준 (대략 어깨 정도까지는 올라가야 함)
    MIN_SHOULDER_ROT = 25.0         # 어깨 회전 범위 최소 기준
    MIN_HIP_ROT = 10.0              # 골반 회전 범위 최소 기준
    MIN_SHOULDER_SPAN = 0.10        # 어깨 간 거리 최소 비율 (프레임 너비 대비, 사람 크기 필터)

    # 백스윙 각도가 너무 작고, 회전 범위도 매우 작으면 골프 스윙이 아니라고 간주
    # (단순 팔 움직임, 서 있는 자세 등)
    if (
        max_backswing_angle < MIN_BACKSWING_ANGLE and
        (shoulder_rotation_range is None or shoulder_rotation_range < MIN_SHOULDER_ROT) and
        (hip_rotation_range is None or hip_rotation_range < MIN_HIP_ROT)
    ):
        return {"error": "스윙 자세를 감지할 수 없습니다"}

    # 화면 속 작은 캐릭터(스크린 골프 아바타)와 실제 사람을 구분하기 위한 추가 필터
    # 실제 사람이 카메라에 어느 정도 가깝게 찍혔다면 어깨 간 거리 비율이 0.1~0.2 이상 나오는 경우가 많음.
    # 어깨 간 거리가 너무 작다면 (예: 스크린 속 캐릭터만 보이는 경우) 스윙으로 보지 않음.
    if max_shoulder_span < MIN_SHOULDER_SPAN:
        return {"error": "스윙하는 사람의 전체 몸이 화면에 충분히 보이지 않습니다."}
    ):
        return {"error": "스윙 자세를 감지할 수 없습니다"}

    # 4) 회전 효율 (rotation_efficiency: 0~100)
    rotation_efficiency = None
    if (
        shoulder_rotation_range is not None
        and hip_rotation_range is not None
        and hip_rotation_range != 0
    ):
        actual_ratio = shoulder_rotation_range / hip_rotation_range
        ideal_ratio = 2.0  # 이상적인 어깨:골반 회전 비율을 2:1로 가정
        diff = abs(actual_ratio - ideal_ratio)

        # diff가 0이면 100점, diff가 2 이상이면 0점으로 선형 감소
        if diff >= 2.0:
            rotation_efficiency_score = 0.0
        else:
            rotation_efficiency_score = (1.0 - diff / 2.0) * 100.0

        rotation_efficiency = int(round(max(0.0, min(100.0, rotation_efficiency_score))))

    # 5) 종합 스윙 점수 (overall_score: 0~100)
    overall_score = None
    component_scores = []
    component_weights = []

    # tempo 점수 (3:1에 가까울수록 좋게)
    if tempo_ratio is not None:
        tempo_diff = abs(tempo_ratio - 3.0)
        # diff 0 -> 100, diff 1 -> 70, diff 2 -> 40, diff 3 -> 10, 그 이상 -> 0 정도 느낌
        tempo_score = max(0.0, 100.0 - tempo_diff * 30.0)
        component_scores.append(tempo_score)
        component_weights.append(0.3)

    # 머리 흔들림 점수 (적을수록 좋음)
    if head_movement_pct is not None:
        # 0% -> 100점, 10% -> 70점, 20% -> 40점, 30% -> 10점, 그 이상 -> 0점
        head_score = max(0.0, 100.0 - head_movement_pct * 3.0)
        component_scores.append(head_score)
        component_weights.append(0.2)

    # 밸런스 점수 (0~1을 0~100으로)
    if balance_score is not None:
        bal_score = max(0.0, min(1.0, balance_score)) * 100.0
        component_scores.append(bal_score)
        component_weights.append(0.2)

    # 회전 효율 점수
    if rotation_efficiency is not None:
        component_scores.append(float(rotation_efficiency))
        component_weights.append(0.3)

    if component_weights:
        total_w = sum(component_weights)
        weighted_sum = sum(s * w for s, w in zip(component_scores, component_weights))
        overall_score = int(round(weighted_sum / total_w))

    # 최종 결과
    result = {
        # v1 기본 메트릭
        "backswing_angle": max_backswing_angle,
        "impact_speed": max_impact_speed,
        "follow_through_angle": max_follow_through_angle,
        "balance_score": balance_score,

        # v2 확장 메트릭
        "tempo_ratio": tempo_ratio,
        "backswing_time_sec": backswing_time_sec,
        "downswing_time_sec": downswing_time_sec,
        "head_movement_pct": head_movement_pct,
        "shoulder_rotation_range": shoulder_rotation_range,
        "hip_rotation_range": hip_rotation_range,
        "rotation_efficiency": rotation_efficiency,
        "overall_score": overall_score,

        # 참고 정보
        "frames_analyzed": frame_count,
        "total_frames": total_frames,
    }

    return result

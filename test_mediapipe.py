import cv2
import mediapipe as mp
import numpy as np

print("=== MediaPipe 테스트 시작 ===")
print(f"OpenCV 버전: {cv2.__version__}")
print(f"MediaPipe 버전: {mp.__version__}")
print(f"NumPy 버전: {np.__version__}")

# MediaPipe Pose 초기화
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

print("\n✅ MediaPipe Pose 모듈 로드 성공!")
print("✅ 모든 패키지 정상 작동!")

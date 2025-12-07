from flask import Flask, request, jsonify
import os
from analyze_swing import analyze_golf_swing

app = Flask(__name__)

# 업로드 폴더
UPLOAD_FOLDER = '/tmp/videos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return jsonify({
        'service': 'INSWING AI Analysis Server',
        'version': '1.0',
        'status': 'running'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/analyze', methods=['POST'])
def analyze():
    """비디오 분석 API"""
    
    # 파일 체크
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    video = request.files['video']
    
    if video.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # 임시 저장
    video_path = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(video_path)
    
    try:
        # 분석 실행
        result = analyze_golf_swing(video_path)
        
        # 파일 삭제
        os.remove(video_path)
        
        if 'error' in result:
            return jsonify(result), 400
        
        # 문서 요구사항에 맞게 응답 형식 변경
        invalid_swing = result.pop('invalid_swing', False)  # result에서 제거하고 별도로 관리
        analysis_version = 'v2'  # 현재 버전
        
        return jsonify({
            'metrics': result,
            'analysis_version': analysis_version,
            'invalid_swing': invalid_swing
        })
        
    except Exception as e:
        # 파일 삭제
        if os.path.exists(video_path):
            os.remove(video_path)
        
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

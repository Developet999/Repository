import os
import cv2
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from moviepy.editor import VideoFileClip

app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
MAX_DURATION = 12 * 60

for f in [UPLOAD_FOLDER, RESULT_FOLDER]:
    if not os.path.exists(f): os.makedirs(f)

@app.route('/')
def home():
    # هذا السطر يضمن ظهور ملف index.html عند فتح الموقع
    return send_from_directory('.', 'index.html')

@app.route('/process_video', methods=['POST'])
def process():
    if 'video' not in request.files:
        return jsonify({"error": "No video uploaded"}), 400
    
    file = request.files['video']
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_filename = "CLEAN_ABDO_" + file.filename
    output_path = os.path.join(RESULT_FOLDER, output_filename)
    
    file.save(input_path)

    # فحص المدة (شرط الـ 12 دقيقة)
    try:
        clip = VideoFileClip(input_path)
        if clip.duration > MAX_DURATION:
            clip.close()
            os.remove(input_path)
            return jsonify({"error": "الفيديو يتجاوز 12 دقيقة"}), 403
        clip.close()
    except Exception as e:
        return jsonify({"error": "خطأ في قراءة ملف الفيديو"}), 500

    # محرك الإزالة (تمويه الزوايا تلقائياً)
    video = cv2.VideoCapture(input_path)
    w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    while True:
        ret, frame = video.read()
        if not ret: break
        # معالجة المنطقة العلوية اليمنى (مكان الشعار المعتاد) كما هي في كودك
        roi = frame[10:110, w-210:w-10]
        frame[10:110, w-210:w-10] = cv2.GaussianBlur(roi, (41, 41), 0)
        out.write(frame)

    video.release()
    out.release()
    
    return jsonify({
        "message": "تمت المعالجة بنجاح بواسطة ABDO AI",
        "download_url": f"/download/{output_filename}"
    })

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
from flask import Flask, request, jsonify, render_template
import openai
import sqlite3
import os
from werkzeug.utils import secure_filename
import secrets


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = secrets.token_hex(16)  # 보안 키 추가
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# DB 초기화
def init_db():
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        story TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()


# STT (음성 → 텍스트 변환) 개선
@app.route("/api/stt", methods=["POST"])
def stt():
    if 'file' not in request.files:
        return jsonify({"error": "음성 파일이 필요합니다."}), 400

    file = request.files['file']
    # 실제 음성 인식 API 호출 (예: Google Speech-to-Text)
    # 여기서는 데모용으로 고정 텍스트 반환
    recognized_text = "오늘 나는 엄마와 시장에 다녀왔어요."

    return jsonify({"text": recognized_text})


# AI 스토리 요약 (GPT 기반)
@app.route("/api/story", methods=["POST"])
def story():
    text = request.json.get("text")
    # 실제 OpenAI API 사용 예시
    story = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "감동적인 스토리로 각색해줘."},
            {"role": "user", "content": text}
        ]
    )["choices"][0]["message"]["content"]
    return jsonify({"story": story})

# 스토리 저장 API
@app.route("/api/story/save", methods=["POST"])
def save_story():
    username = request.json.get("username")
    story = request.json.get("story")
    if not username or not story:
        return jsonify({"error": "username과 story가 필요합니다."}), 400
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("INSERT INTO stories (username, story) VALUES (?, ?)", (username, story))
    conn.commit()
    conn.close()
    return jsonify({"result": "success"})

# 사용자별 스토리 목록 조회 API
@app.route("/api/story/list", methods=["GET"])
def list_story():
    username = request.args.get("username")
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    if username:
        c.execute("SELECT id, story, created_at FROM stories WHERE username=? ORDER BY created_at DESC", (username,))
    else:
        c.execute("SELECT id, username, story, created_at FROM stories ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    if username:
        result = [{"id": r[0], "story": r[1], "created_at": r[2]} for r in rows]
    else:
        result = [{"id": r[0], "username": r[1], "story": r[2], "created_at": r[3]} for r in rows]
    return jsonify(result)

# 자기소개 음성 업로드 API
@app.route("/api/intro/upload", methods=["POST"])
def upload_intro():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 필요합니다."}), 400
    file = request.files['file']
    username = request.form.get("username", "anonymous")
    filename = secure_filename(username + "_intro_" + file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    return jsonify({"result": "success", "url": f"/uploads/{filename}"})


# TTS (텍스트 → 음성), 예시용
@app.route("/api/tts", methods=["POST"])
def tts():
    story = request.json.get("story")
    # 실제로는 TTS API 호출, 여기서는 데모용 URL 반환
    return jsonify({"url": "https://www.w3schools.com/html/horse.mp3"})


# 이미지 생성 (텍스트 → 이미지) 개선
@app.route("/api/image", methods=["POST"])
def image():
    story = request.json.get("story")
    if not story:
        return jsonify({"error": "텍스트가 필요합니다."}), 400

    # 실제 이미지 생성 API 호출 (예: DALL-E, Stable Diffusion)
    # 여기서는 데모용 이미지 URL 반환
    generated_image_url = "https://placekitten.com/400/300"

    return jsonify({"url": generated_image_url})

@app.route("/")
def home():
    return render_template("index.html")

# 파비콘 요청 처리 (404 에러 방지용)
@app.route("/favicon.ico")
def favicon():
    return "", 204

# 업로드된 파일 제공용 (개발용)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return app.send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# AI 대화 API
@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "메시지가 필요합니다."}), 400

    # OpenAI API를 사용하여 응답 생성 (예시)
    ai_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "친절한 AI 비서입니다. 사용자 질문에 답변하세요."},
            {"role": "user", "content": user_message}
        ]
    )["choices"][0]["message"]["content"]

    return jsonify({"response": ai_response})

# Vercel 배포를 위한 app 객체 export
app.debug = False

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000)
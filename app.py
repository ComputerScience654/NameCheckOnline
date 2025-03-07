import requests  # ใช้สำหรับส่ง HTTP Request ไปยัง LINE API
from flask import Flask, request, jsonify, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import datetime
import os

# ตั้งค่า LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN = "apkCQYUR4pPCngL42rber8/Fj5IBiWArNkAGaqVrtXzH46NMGw8o+1YcWp4PRAWFsz0VhArT0fpvdVmoEEDyInp8Uef0VvAmInr/sWJNiDy3A7xLHI0TMeWMjBXXY6kjBkUgi6ue1RG1rFJDKWwK8QdB04t89/1O/w1cDnyilFU="  # ใส่ Channel Access Token
LINE_USER_ID = "Ufec8ece330f09ee6f227a9241bb0a7d1"  # ใส่ User ID หรือ Group ID ที่ต้องการส่งแจ้งเตือน

def send_line_message(text):
    """ ส่งข้อความไปยัง LINE Messaging API """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,  # ส่งไปยัง User ID หรือ Group ID
        "messages": [{"type": "text", "text": text}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("📢 ส่งข้อความไปยัง LINE สำเร็จ!")
        else:
            print("❌ ไม่สามารถส่งข้อความไปยัง LINE ได้:", response.text)
    except Exception as e:
        print("⚠️ Error sending LINE message:", e)

def send_line_image(image_url):
    """ ส่งรูปภาพไปยัง LINE Messaging API """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("📢 ส่งรูปไปยัง LINE สำเร็จ!")
        else:
            print("❌ ไม่สามารถส่งรูปไปยัง LINE ได้:", response.text)
    except Exception as e:
        print("⚠️ Error sending LINE image:", e)


app = Flask(__name__)
CORS(app)

# ตั้งค่าการอัปโหลดรูปภาพ
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/attendance_db'  # แก้ไขให้ตรงกับ MySQL ของคุณ
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'  # ใช้ key ที่ปลอดภัย

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Model Users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Model Attendance
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), nullable=False)
    image_path = db.Column(db.String(255), nullable=True)  # เก็บ path ของรูปภาพ
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# สร้าง Database
with app.app_context():
    db.create_all()

# ------------------- Route สำหรับเรนเดอร์หน้า HTML -------------------

@app.route('/')
def home():
    return render_template('base.html')  # หน้า Login

@app.route('/login')
def login_page():
    return render_template('login.html')  # หน้าเข้าสู่ระบบ

@app.route('/register')
def register_page():
    return render_template('register.html')  # หน้า Register

@app.route('/forgot')
def forgot_page():
    return render_template('forgot.html')  # หน้า ลืมรหัสผ่าน

@app.route('/home')
def attendance_page():
    return render_template('home.html')  # หน้า เช็คชื่อ

@app.route('/history')
def history_page():
    return render_template('history.html')  # หน้าแสดงประวัติ

# ------------------- API สำหรับ Authentication -------------------

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(email=data['email'], username=data['username'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        token = create_access_token(identity=str(user.id))  # แปลงเป็น String
        return jsonify({'token': token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# ------------------- API สำหรับ Attendance -------------------

@app.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    try:
        if 'image' not in request.files:
            return jsonify({'message': 'No image uploaded'}), 400

        file = request.files['image']
        student_name = request.form.get('fullName')
        student_id = request.form.get('studentID')
        timestamp = datetime.datetime.now()

        if not file or not student_name or not student_id:
            return jsonify({'message': 'Invalid data'}), 400

        filename = f"{student_id}_{timestamp.strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_attendance = Attendance(
            student_name=student_name,
            student_id=student_id,
            image_path=filepath,
            timestamp=timestamp
        )

        db.session.add(new_attendance)
        db.session.commit()

        # สร้าง URL ของรูปภาพ
        NGROK_URL = "https://e9e1-49-230-139-44.ngrok-free.app"  # ใส่ URL จาก ngrok
        image_url = f"{NGROK_URL}/static/uploads/{filename}"

        # ✨ ส่งข้อความแจ้งเตือนพร้อมรูปภาพไปยัง LINE
        line_message = f"📌 เช็คชื่อสำเร็จ!\n👤 ชื่อ: {student_name}\n🆔 รหัสนักเรียน: {student_id}\n⏰ เวลา: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        send_line_message(line_message)  # ส่งข้อความ
        send_line_image(image_url)  # ส่งรูปภาพ

        return jsonify({'message': 'Attendance recorded successfully'}), 201

    except Exception as e:
        print("Error:", e)
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/history-data', methods=['GET'])
@jwt_required()
def get_history():
    records = Attendance.query.order_by(Attendance.timestamp.desc()).all()
    history = [{
        'id': rec.id,
        'name': rec.student_name,
        'student_id': rec.student_id,
        'timestamp': rec.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'image_url': url_for('static', filename=f"uploads/{os.path.basename(rec.image_path)}", _external=True) if rec.image_path else None
    } for rec in records]
    
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True)


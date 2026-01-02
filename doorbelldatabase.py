# ================================
# SMART-DOORBELL
# ================================


import threading
import os
import time
import sqlite3
import cv2
import face_recognition
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from ultralytics import YOLO
import datetime
import numpy as np
import paho.mqtt.client as mqtt
import pickle

# ---------------- DB CONFIG ----------------
DB_PATH = "doorbell.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Main faces table
    c.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            name TEXT,
            category TEXT,
            snapshot BLOB
        )
    ''')

    # Special faces (authorized / blocked only)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            name TEXT,
            encoding BLOB,
            category TEXT CHECK(category IN ('authorized','blocked'))
        )
    ''')

    conn.commit()
    conn.close()


def save_face_to_db(category, name, frame, encoding):
    try:
        _, buffer = cv2.imencode(".jpg", frame)
        img_bytes = buffer.tobytes()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Save in faces table
        c.execute("""
            INSERT INTO access_logs (timestamp,name,category,snapshot)
            VALUES (?, ?, ?, ?)
        """, (
            
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            name,
            category,
            img_bytes,
        ))
        conn.commit()
        conn.close()
        print(f"💾 Saved {category} face ({name}) to database.")
    except Exception as e:
        print("❌ DB insert error:", e)


# ---------------- MQTT CONFIG ----------------
BROKER = "172.16.0.122"
PORT = 1883
TOPIC = "doorbell/command"
USERNAME = "bms"
PASSWORD = "bms@123"

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 60)

# ---------------- EMAIL CONFIG ----------------
SENDER_EMAIL = "sangareshwari3110@gmail.com"
APP_PASSWORD = "mpkqxjyrehtbmfff"
RECEIVER_EMAIL = "sangareshwari3110@gmail.com"



SERVER_IP = "172.16.0.109"
SERVER_PORT = 5000

# ---------------- EMAIL ALERT ----------------
def send_alert_email(message, snapshot_frame=None):
    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = "🚨 Doorbell Alert!"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif; text-align:center; background-color:#f9f9f9; padding:20px;">
            <div style="max-width:600px; margin:auto; background-color:#ffffff; padding:20px; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.1);">
                <h2 style="color:#333;">🚨 Doorbell Alert!</h2>
                <p style="font-size:16px; color:#555;">{message}</p>
                {"<img src='cid:snapshot' style='max-width:100%; height:auto; border-radius:10px; margin:20px 0;'>" if snapshot_frame is not None else ""}
                <div style="margin-top:20px;">
                    <a href="http://{SERVER_IP}:{SERVER_PORT}/decision?action=allow"
                       style="padding:12px 25px; background-color:#28a745; color:white; text-decoration:none; font-weight:bold; border-radius:5px; margin-right:10px;">
                       ✅ ALLOW
                    </a>
                    <a href="http://{SERVER_IP}:{SERVER_PORT}/decision?action=deny"
                       style="padding:12px 25px; background-color:#dc3545; color:white; text-decoration:none; font-weight:bold; border-radius:5px;">
                       ❌ DENY
                    </a>
                </div>
                <p style="font-size:12px; color:#999; margin-top:20px;">
                    This is an automated message from your Smart Doorbell.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        if snapshot_frame is not None:
            _, buffer = cv2.imencode(".jpg", snapshot_frame)
            img_data = buffer.tobytes()
            image = MIMEImage(img_data, name="snapshot.jpg")
            image.add_header('Content-ID', '<snapshot>')
            msg.attach(image)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("📧 Email sent successfully!")
    except Exception as e:
        print("❌ Email sending failed:", e)


# ---------------- YOLO & FACE SETUP ----------------
init_db()
model = YOLO("yolov8n.pt")
frontal_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

authorized_faces, authorized_names = [], []
blocklist_faces, blocklist_names = [], []
# Open DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Fetch all users
c.execute("SELECT name, encoding, category FROM users")
rows = c.fetchall()
conn.close()

for name, enc_blob, category in rows:
    try:
        # Decode the BLOB back into numpy array
        encoding = pickle.loads(enc_blob)

        # Make sure it's numpy array
        encoding = np.array(encoding)

        if category == "authorized":
            authorized_faces.append(encoding)
            authorized_names.append(name)
        elif category == "blocked":
            blocklist_faces.append(encoding)
            blocklist_names.append(name)

    except Exception as e:
        print(f"⚠️ Skipping {name}, error decoding encoding: {e}")
        
print(f"✅ Loaded {len(authorized_faces)} authorized and {len(blocklist_faces)} blocked faces from DB")

# ---------------- ALERT TRACKING ----------------
alerted_unknowns = []
alerted_blocklist = []
temp_encodings = []
TIMEOUT = 60

def is_new_face(face_encoding, alerted_list, tolerance=0.45):
    for enc, last_seen in alerted_list:
        distance = face_recognition.face_distance([enc], face_encoding)[0]
        if distance < tolerance:
            return False
    return True

def update_alerted_list(alerted_list):
    current_time = time.time()
    return [(enc, ts) for enc, ts in alerted_list if current_time - ts < TIMEOUT]


# ---------------- CAMERA LOOP ----------------
#RTSP_URL = "rtsp://admin:Admin%40123@172.16.0.248:554/ch01/1"
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    current_time = time.time()

    alerted_unknowns = update_alerted_list(alerted_unknowns)
    alerted_blocklist = update_alerted_list(alerted_blocklist)

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if cls == 0 and conf > 0.6:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                person_roi = frame[y1:y2, x1:x2]

                gray = cv2.cvtColor(person_roi, cv2.COLOR_BGR2GRAY)
                faces = frontal_face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

                for (fx, fy, fw, fh) in faces:
                    face_frame = person_roi[fy:fy+fh, fx:fx+fw]
                    rgb_face = cv2.cvtColor(face_frame, cv2.COLOR_BGR2RGB)
                    encodings = face_recognition.face_encodings(rgb_face)

                    name = "Unknown"
                    color = (255, 255, 0)

                    if encodings:
                        encoding = encodings[0]

                        # Authorized
                        matches_auth = face_recognition.compare_faces(authorized_faces, encoding, tolerance=0.5)
                        if True in matches_auth:
                            idx = matches_auth.index(True)
                            name = authorized_names[idx]
                            color = (0, 255, 0)

                            already_cached = any(face_recognition.face_distance([enc], encoding)[0] < 0.45 for enc, _ in temp_encodings)
                            if not already_cached:
                                client.publish(TOPIC, '{"status":1}')
                                print(f"✅ Door unlocked automatically for {name}")
                                save_face_to_db("authorized", name, face_frame, encoding)
                                temp_encodings.append((encoding, time.time()))

                        else:
                            # Blocklist
                            matches_block = face_recognition.compare_faces(blocklist_faces, encoding, tolerance=0.5)
                            if True in matches_block:
                                idx = matches_block.index(True)
                                name = "BLOCKED: " + blocklist_names[idx]
                                color = (0, 0, 255)
                                if is_new_face(encoding, alerted_blocklist):
                                    save_face_to_db("blocked", blocklist_names[idx], face_frame, encoding)
                                    print(f"🚨 ALERT! Blocklisted {blocklist_names[idx]} detected!")
                                    client.publish("doorbell/alert", '{"request":"True"}')
                                    send_alert_email(f"🚨 ALERT! Blocklisted '{blocklist_names[idx]}' detected!", face_frame)
                                    temp_encodings.append((encoding, time.time()))
                                    alerted_blocklist.append((encoding, current_time))
                            else:
                                # Unknown
                                if is_new_face(encoding, alerted_unknowns):
                                    save_face_to_db("unknown", "Unknown", face_frame, encoding)
                                    print("❓ Unknown person at door")
                                    client.publish("doorbell/alert", '{"request":"True"}')
                                    send_alert_email("❓ ALERT! Unknown person detected at the door!", face_frame)
                                    temp_encodings.append((encoding, time.time()))
                                    alerted_unknowns.append((encoding, current_time))

                    cv2.rectangle(frame, (x1+fx, y1+fy), (x1+fx+fw, y1+fy+fh), color, 2)
                    cv2.putText(frame, name, (x1+fx, y1+fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Smart Doorbell", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

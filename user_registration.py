import cv2
import face_recognition
import sqlite3
import pickle
import datetime

DB_PATH = "doorbell.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    encoding BLOB,
                    category TEXT CHECK(category IN ('authorized','blocked')),
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

def register_user(name, category):
    video = cv2.VideoCapture(0)
    print("📸 Press 'c' to capture your face")

    face_encoding = None
    while True:
        ret, frame = video.read()
        if not ret:
            continue

        cv2.imshow("Registration - Press 'c'", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)

            if len(face_locations) != 1:
                print("⚠ Please make sure exactly ONE face is visible")
                continue

            encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            if encodings:
                face_encoding = encodings[0]
                print("✅ Face captured")
                break
            else:
                print("❌ Could not encode face, try again")

        elif key == ord('q'):
            print("❌ Registration cancelled")
            break

    video.release()
    cv2.destroyAllWindows()

    if face_encoding is not None:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (name, encoding, category, timestamp) VALUES (?,?,?,?)",
                  (name, pickle.dumps(face_encoding), category, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"🎉 User '{name}' registered as {category}")

if __name__ == "__main__":
    init_db()
    while True:
        name = input("Enter user name: ")
        category = input("Enter category (authorized/blocked): ").strip().lower()
        register_user(name, category)
        
        choice = input("Do you want to register more users?(y/n) \n")
        if choice == 'n':
            break
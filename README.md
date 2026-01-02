# 🔔 Smart Doorbell System (AI-Powered)

An **AI-powered smart doorbell system** that uses computer vision and face recognition to identify visitors at your doorstep. The system classifies people as **authorized**, **blocked**, or **unknown**, sends **real-time alerts via MQTT and email**, and allows **remote allow/deny access** from anywhere through a secure web interface.

---

## ✨ Features

- 🎥 **Camera-based doorbell system** (USB / IP camera)
- 🧍 **Person detection using YOLOv8**
- 😀 **Face recognition** for identifying visitors
- 🟢 **Authorized users** – auto door unlock
- 🔴 **Blocked users** – instant alert & denial
- ❓ **Unknown users** – email alert with snapshot
- 📧 **Email notifications** with visitor image and ALLOW / DENY buttons
- 🌐 **Remote access control** via Flask web server
- 📡 **MQTT integration** for IoT / mobile / web backend
- 🗄 **SQLite database** for logs and registered users
- 🕒 **Duplicate alert prevention** using timeout logic

---

## 🧠 System Architecture

```
Camera → YOLO (Person Detection)
        → Face Detection → Face Recognition
        → Classification (Authorized / Blocked / Unknown)
        → MQTT Publish + Email Alert
        → Remote Allow / Deny via Web Server
```

---

## 📁 Project Structure

```
Smart-Doorbell/
│
├── doorbell.py            # Main AI doorbell detection & alert system
├── server.py              # Flask server for allow/deny decisions
├── user_registration.py   # Register authorized / blocked users
├── doorbell.db            # SQLite database (users & access logs)
├── outputs/               # Output screenshots & detections
├── README.md              # Project documentation
```

---

## 🛠️ Technologies Used

- **Python 3.x**
- **OpenCV** – camera handling & image processing
- **YOLOv8 (Ultralytics)** – person detection
- **face_recognition (dlib)** – face encoding & matching
- **Flask** – web server for remote decisions
- **SQLite** – local database
- **MQTT (paho-mqtt)** – IoT messaging
- **SMTP (Gmail)** – email alerts

---

## ⚙️ Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/Smart-Doorbell.git
cd Smart-Doorbell
```

### 2️⃣ Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Install Dependencies
```bash
pip install opencv-python ultralytics face-recognition flask flask-cors paho-mqtt numpy
```

> ⚠️ **Note:** `face-recognition` requires **dlib**. On Windows, install a precompiled wheel if needed.

---

## 🗄️ Database Setup

The SQLite database (`doorbell.db`) is automatically created.

### Tables:
- **users** – authorized & blocked face encodings
- **access_logs** – timestamp, name, category, snapshot

---

## 👤 Register Users

Run the user registration script to add faces:

```bash
python user_registration.py
```

- Press **`c`** to capture face
- Register user as:
  - `authorized`
  - `blocked`

---

## ▶️ Run the System

### 1️⃣ Start the Flask Server
```bash
python server.py
```

This enables remote **ALLOW / DENY** access from email links.

---

### 2️⃣ Start the Smart Doorbell
```bash
python doorbell.py
```

- Detects visitors
- Sends MQTT messages
- Triggers email alerts
- Unlocks door automatically for authorized users

---

## 📧 Email Alert Workflow

- Visitor detected → snapshot captured
- Email sent with visitor image
- Click **ALLOW** → door unlock command via MQTT
- Click **DENY** → access blocked

---

## 📡 MQTT Topics

| Topic | Purpose |
|------|--------|
| `doorbell/command` | Door unlock / lock control |
| `doorbell/alert` | Visitor alert notification |

---

## 📸 Output Samples

All detection screenshots and results are stored in the **outputs/** folder.

---

## 🔐 Security Notes

- Do **not** commit real email passwords
- Use environment variables for production
- Secure MQTT broker with TLS if deployed publicly

---

## 🚀 Future Enhancements

- Mobile app integration
- Live video streaming
- Cloud database (Firebase / AWS)
- Voice assistant support
- Multi-user access control
- Face anti-spoofing

---

## 👩‍💻 Author

**Sansi**  
AI Engineer | Computer Vision | IoT Systems

---

## ⭐ Support

If you like this project, please ⭐ star the repository and share it!

---

## 📜 License

This project is open-source and available under the **MIT License**.


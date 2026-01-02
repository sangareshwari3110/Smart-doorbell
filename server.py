from flask import Flask, request, jsonify, Response, render_template_string, redirect, url_for
import sqlite3
import datetime
from flask_cors import CORS
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_PATH = "doorbell.db"

# ---------------- CONFIG ----------------
BROKER = "172.16.0.122"  # MQTT broker
PORT = 1883
TOPIC = "doorbell/command"

USERNAME = "bms"
PASSWORD = "bms@123"

SENDER_EMAIL = "sangareshwari3110@gmail.com"
APP_PASSWORD = "mpkqxjyrehtbmfff" #yintiudpvrghplok
RECEIVER_EMAIL = "sangareshwari3110@gmail.com"

SERVER_IP = "172.16.0.109"
SERVER_PORT = 5000


# ---------------- MQTT ----------------
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 60)



app = Flask(__name__)
CORS(app)


def build_decision_html(action, actor_ip, when_str):
    approved = (action == "allow")

    # Color and icon per decision
    badge_bg = "#e8f5ee" if approved else "#fdeaea"
    badge_border = "#28a745" if approved else "#dc3545"
    badge_text = "#1d6b3a" if approved else "#8a1f2a"
    badge_label = "ACCESS GRANTED" if approved else "ACCESS DENIED"
    emoji = "✅" if approved else "❌"
    header_text = "Door Unlocked" if approved else "Access Rejected"
    info_para = (
        "The door has been unlocked successfully."
        if approved else
        "Access has been rejected. The door remains locked."
    )

    # Beautiful HTML card
    html = f"""
            <html>
            <body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fb;padding:24px 12px;">
                <tr>
                <td align="center">
                    <table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;background:#ffffff;border-radius:14px;box-shadow:0 8px 24px rgba(22,34,51,0.08);overflow:hidden;">
                    <tr>
                        <td style="padding:28px 28px 8px 28px;text-align:center;">
                        <div style="font-size:24px;font-weight:700;color:#222;letter-spacing:.2px;">
                            {emoji} Doorbell Decision
                        </div>
                        <div style="margin-top:10px;display:inline-block;padding:8px 14px;border-radius:999px;
                                    background:{badge_bg};border:1px solid {badge_border};color:{badge_text};
                                    font-weight:700;font-size:12px;letter-spacing:.6px;">
                            {badge_label}
                        </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:8px 28px 0 28px;text-align:center;color:#111;">
                        <div style="font-size:20px;font-weight:600;margin-top:8px;">{header_text}</div>
                        <p style="margin:12px 0 0 0;font-size:14px;color:#475467;line-height:1.6;">
                            {info_para}
                        </p>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:18px 28px 0 28px;">
                        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;border-spacing:0 10px;">
                            <tr>
                            <td style="width:180px;padding:12px 14px;background:#f8fafc;border-radius:10px;color:#64748b;font-size:12px;">Time</td>
                            <td style="padding:12px 14px;background:#f8fafc;border-radius:10px;color:#0f172a;font-size:14px;font-weight:600;">
                                {when_str}
                            </td>
                            </tr>
                        </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:6px 28px 24px 28px;text-align:center;color:#94a3b8;font-size:12px;">
                        This is an automated message from your Smart Doorbell System.
                        </td>
                    </tr>
                    </table>
                </td>
                </tr>
            </table>
            </body>
            </html>
            """

    return html

def send_decision_email(action, actor_ip):
    when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Doorbell Decision • {'ALLOW' if action=='allow' else 'DENY'} • {when}"
    html = build_decision_html(action, actor_ip, when)

    # Plain-text fallback
    text = f"""Doorbell Decision
            Decision: {'ALLOW' if action=='allow' else 'DENY'}
            Time: {when}
            Requester IP: {actor_ip or 'Unknown'}
            Server: http://{SERVER_IP}:{SERVER_PORT}
            """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("📧 Decision email sent successfully!")
    except Exception as e:
        print("❌ Decision email sending failed:", e)
        
    return html
  

@app.route("/decision")
def decision():
    action = request.args.get("action")
    actor_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if action == "allow":
        p=client.publish(TOPIC,'{"status":1}')
        print(p)
        show = send_decision_email("allow", actor_ip)
        return show
    elif action == "deny":                                                                     
        p=client.publish(TOPIC,'{"status":0}')
        print(p)
        show = send_decision_email("deny", actor_ip)
        return show
    else:
        return "Unknown action", 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

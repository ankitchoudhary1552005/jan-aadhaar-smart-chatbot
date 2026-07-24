from google import genai
from dotenv import load_dotenv
import os
from openpyxl import Workbook
from flask import Flask, render_template, request, jsonify, redirect, send_file, session
import sqlite3
from datetime import datetime
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

import database
from jan_aadhaar_data import faq

# Load .env file
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

app.secret_key = "jan_aadhaar_chatbot"

client = genai.Client(
    api_key=os.getenv("GMINI_API_KEYG")
)

# -------------------- Save Chat --------------------
def save_chat(user_message, bot_reply):

    username = session.get("username", "Guest")
    chat_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chats(username, user_message, bot_reply, chat_time) VALUES(?, ?, ?, ?)",
        (username, user_message, bot_reply, chat_time)
    )

    conn.commit()
    conn.close()

# -------------------- Chatbot --------------------
def chatbot_response(message):
    message = message.lower().strip()

    # FAQ First
    for question, answer in faq.items():
        if question.lower() in message:
            return answer

    # Gemini AI
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=message
        )

        return response.text

    except Exception as e:
        print("Gemini Error:", e)
        return "Sorry! AI service is currently unavailable."


# -------------------- Login Page --------------------
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def user_login():
    session["username"] = request.form["username"]
    return redirect("/dashboard")

# -------------------- Chat Page --------------------
@app.route("/chat")
def chat():
    username = session.get("username", "Guest")
    return render_template("index.html", username=username)


# -------------------- Chat API --------------------
@app.route("/get", methods=["POST"])
def get_response():
    user_message = request.form["msg"]

    bot_reply = chatbot_response(user_message)

    save_chat(user_message, bot_reply)

    return jsonify({"reply": bot_reply})

@app.route("/dashboard")
def dashboard():

    username = session.get("username", "Guest")

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    # Total Chats
    cursor.execute("SELECT COUNT(*) FROM chats")
    total_chats = cursor.fetchone()[0]

    # Total Users
    cursor.execute("SELECT COUNT(DISTINCT username) FROM chats")
    total_users = cursor.fetchone()[0]

    # FAQ Replies
    cursor.execute("""
        SELECT COUNT(*)
        FROM chats
        WHERE bot_reply LIKE '%Jan Aadhaar%'
    """)
    faq_count = cursor.fetchone()[0]

    # AI Replies
    ai_count = total_chats - faq_count

    conn.close()

    return render_template(
        "dashboard.html",
        username=username,
        total_chats=total_chats,
        total_users=total_users,
        faq_count=faq_count,
        ai_count=ai_count
    )
         
@app.route("/history")
def history():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, user_message, bot_reply, chat_time
        FROM chats
        ORDER BY id DESC
    """)

    chats = cursor.fetchall()
    total = len(chats)

    conn.close()

    return render_template(
        "history.html",
        chats=chats,
        total=total
    )


# -------------------- Delete --------------------
@app.route("/delete/<int:id>")
def delete_chat(id):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chats WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/history")


# -------------------- Clear --------------------
@app.route("/clear")
def clear_history():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chats")

    conn.commit()
    conn.close()

    return redirect("/history")


# -------------------- PDF Download --------------------
@app.route("/download_pdf")
def download_pdf():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT user_message, bot_reply FROM chats")
    chats = cursor.fetchall()

    conn.close()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph("<b>Jan Aadhaar Chat History</b>", styles["Heading1"])
    )

    for user, bot in chats:
        story.append(
            Paragraph(f"<b>User:</b> {user}", styles["BodyText"])
        )
        story.append(
            Paragraph(f"<b>Bot:</b> {bot}", styles["BodyText"])
        )
        story.append(
            Paragraph("<br/>", styles["BodyText"])
        )

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="chat_history.pdf",
        mimetype="application/pdf"
    )

# -------------------- Excel Download --------------------
@app.route("/download_excel")
def download_excel():

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, user_message, bot_reply, chat_time
        FROM chats
    """)

    chats = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Chat History"

    # Header
    ws.append(["Username", "User Message", "Bot Reply", "Date & Time"])

    # Data
    for chat in chats:
        ws.append(chat)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="chat_history.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

#route

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(debug=True)
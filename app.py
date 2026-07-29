from google import genai
from dotenv import load_dotenv
import os
import sqlite3
import io

from datetime import datetime
from openpyxl import Workbook

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    send_file,
    session
)

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import database
from jan_aadhaar_data import faq

# ==============================
# Load Environment Variables
# ==============================
load_dotenv()

app = Flask(__name__)

app.secret_key = "jan_aadhaar_chatbot"

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# ==============================
# Save Chat
# ==============================
def save_chat(user_message, bot_reply):

    username = session.get("username", "Guest")

    chat_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chats
        (username, user_message, bot_reply, chat_time)
        VALUES (?, ?, ?, ?)
    """,
    (
        username,
        user_message,
        bot_reply,
        chat_time
    ))

    conn.commit()
    conn.close()


# ==============================
# Chatbot Response
# ==============================
def chatbot_response(message):

    message = message.lower().strip()

    # FAQ Response
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

        print("Gemini Error :", e)

        return "Sorry! AI service is unavailable."


# ==============================
# Login Page
# ==============================
@app.route("/")
def login():

    return render_template("login.html")


# ==============================
# Login
# ==============================
@app.route("/login", methods=["POST"])
def user_login():

    username = request.form["username"].strip()
    password = request.form["password"]

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        if check_password_hash(user[0], password):

            session["username"] = username

            return redirect("/dashboard")

    return "Invalid Username or Password"


# ==============================
# Signup Page
# ==============================
@app.route("/signup")
def signup():

    return render_template("signup.html")


# ==============================
# Signup
# ==============================
@app.route("/signup", methods=["POST"])
def signup_user():

    username = request.form["username"].strip()

    password = generate_password_hash(
        request.form["password"]
    )

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if user:

        conn.close()

        return "Username already exists!"

    cursor.execute(
        """
        INSERT INTO users(username, password)
        VALUES(?, ?)
        """,
        (
            username,
            password
        )
    )

    conn.commit()
    conn.close()

    return redirect("/")

# ==============================
# Chat Page
# ==============================
@app.route("/chat")
def chat():

    if "username" not in session:
        return redirect("/")

    return render_template(
        "index.html",
        username=session["username"]
    )


# ==============================
# Chat API
# ==============================
@app.route("/get", methods=["POST"])
def get_response():

    if "username" not in session:
        return jsonify({"reply": "Please login first."})

    user_message = request.form["msg"]

    bot_reply = chatbot_response(user_message)

    save_chat(user_message, bot_reply)

    return jsonify({
        "reply": bot_reply
    })


# ==============================
# Dashboard
# ==============================
@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    # Total Chats
    cursor.execute(
        "SELECT COUNT(*) FROM chats WHERE username=?",
        (username,)
    )
    total_chats = cursor.fetchone()[0]

    # Total Registered Users
    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )
    total_users = cursor.fetchone()[0]

    # FAQ Replies
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM chats
        WHERE username=?
        AND bot_reply LIKE '%Jan Aadhaar%'
        """,
        (username,)
    )
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


# ==============================
# History
# ==============================
@app.route("/history")
def history():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               username,
               user_message,
               bot_reply,
               chat_time
        FROM chats
        WHERE username=?
        ORDER BY id DESC
    """, (username,))

    chats = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        chats=chats,
        total=len(chats),
        username=username
    )


# ==============================
# Delete One Chat
# ==============================
@app.route("/delete/<int:id>")
def delete_chat(id):

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM chats WHERE id=? AND username=?",
        (id, username)
    )

    conn.commit()
    conn.close()

    return redirect("/history")


# ==============================
# Clear All History
# ==============================
@app.route("/clear")
def clear_history():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM chats WHERE username=?",
        (username,)
    )

    conn.commit()
    conn.close()

    return redirect("/history")

# ==============================
# Download PDF
# ==============================
@app.route("/download_pdf")
def download_pdf():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_message, bot_reply, chat_time
        FROM chats
        WHERE username=?
        ORDER BY id DESC
    """, (username,))

    chats = cursor.fetchall()
    conn.close()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>Jan Aadhaar Chat History</b>",
            styles["Heading1"]
        )
    )

    for user_msg, bot_reply, chat_time in chats:

        story.append(
            Paragraph(
                f"<b>Date:</b> {chat_time}",
                styles["BodyText"]
            )
        )

        story.append(
            Paragraph(
                f"<b>User:</b> {user_msg}",
                styles["BodyText"]
            )
        )

        story.append(
            Paragraph(
                f"<b>Bot:</b> {bot_reply}",
                styles["BodyText"]
            )
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


# ==============================
# Download Excel
# ==============================
@app.route("/download_excel")
def download_excel():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username,
               user_message,
               bot_reply,
               chat_time
        FROM chats
        WHERE username=?
        ORDER BY id DESC
    """, (username,))

    chats = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Chat History"

    ws.append([
        "Username",
        "User Message",
        "Bot Reply",
        "Date & Time"
    ])

    for row in chats:
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="chat_history.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ==============================
# Logout
# ==============================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==============================
# Run App
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
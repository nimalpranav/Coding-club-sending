from flask import Flask, render_template, request, redirect, session, send_from_directory, abort
import os
from werkzeug.utils import secure_filename

# ================= CONFIG =================
app = Flask(__name__)
app.secret_key = "your_random_secret_key"  # Replace with a strong random secret
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limit uploads to 16MB

# Users database (username -> info)
users = {
    "Nimalpranav": {"gmail": "nimal@example.com", "role": "student"},
    # Add more students here if needed
}

messages = {}

# ================= SECURITY HEADERS =================
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "frame-ancestors 'none';"
    )
    return response

# ================= ROUTES =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        gmail = request.form.get("gmail", "").strip()
        password = request.form.get("password", "").strip()

        # Admin login with Gmail only
        if gmail.lower() == "lakshmipriyasnp@gmail.com":
            session["user"] = "admin"
            session["role"] = "admin"
            return redirect("/admin")

        # Student login with Gmail only
        for username, info in users.items():
            if info.get("gmail", "").lower() == gmail.lower():
                session["user"] = username
                session["role"] = "student"
                return redirect("/student")

        return "❌ Invalid Gmail"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        gmail = request.form.get("gmail", "").strip()
        username = request.form.get("username", "").strip()

        if not gmail or not username:
            return "Please provide both username and Gmail"

        # Check for duplicate Gmail
        if any(info.get("gmail") == gmail for info in users.values()):
            return "User with this Gmail already exists"

        users[username] = {"gmail": gmail, "role": "student"}
        return redirect("/")

    return render_template("register.html")

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    students = [u for u in users if users[u]["role"] == "student"]
    return render_template("admin_dashboard.html", students=students)

@app.route("/send_message", methods=["POST"])
def send_message():
    if session.get("role") != "admin":
        abort(403)
    student = request.form.get("student")
    msg = request.form.get("message")
    if student and msg:
        messages.setdefault(student, []).append(msg)
    return redirect("/admin")

@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role") != "admin":
        abort(403)
    file = request.files.get("file")
    if not file or file.filename == "":
        return redirect("/admin")
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return redirect("/admin")

@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")
    user = session.get("user")
    user_messages = messages.get(user, [])
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template("student_dashboard.html", messages=user_messages, files=files)

@app.route("/download/<filename>")
def download(filename):
    if session.get("role") not in ["admin", "student"]:
        abort(403)
    # Optionally, restrict students to only see uploaded files
    safe_filename = secure_filename(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_filename, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= MAIN =================
if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, render_template_string, request, redirect, session, send_from_directory, abort
import os
from werkzeug.utils import secure_filename

# ================= CONFIG =================
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB limit

# Users
users = {
    "Nimalpranav": {"gmail": "nimal@example.com", "role": "student"},
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

# ================= SINGLE PAGE TEMPLATE =================
PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Flask App</title>
<style>
body { font-family: Arial, sans-serif; background: #f4f6f8; margin:0; padding:0; }
.container { max-width:600px; margin:50px auto; background:white; padding:30px; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,0.1);}
h1 { text-align:center; color:#333; }
input, select, textarea { width:100%; padding:10px; margin:10px 0; border-radius:5px; border:1px solid #ccc; }
button { width:100%; padding:12px; background:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer; }
button:hover { background:#0056b3; }
a { color:#007BFF; text-decoration:none; }
a:hover { text-decoration:underline; }
ul { list-style:none; padding:0; }
li { padding:5px 0; border-bottom:1px solid #eee; }
</style>
</head>
<body>
<div class="container">
{% if page == 'login' %}
    <h1>Login</h1>
    <form method="POST">
        <input type="text" name="gmail" placeholder="Gmail" required>
        <button type="submit">Login</button>
    </form>
    <p>Don't have an account? <a href="/register">Register</a></p>
    {% if error %}<p style="color:red">{{ error }}</p>{% endif %}

{% elif page == 'register' %}
    <h1>Register</h1>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required>
        <input type="text" name="gmail" placeholder="Gmail" required>
        <button type="submit">Register</button>
    </form>
    <p>Already have an account? <a href="/">Login</a></p>
    {% if error %}<p style="color:red">{{ error }}</p>{% endif %}

{% elif page == 'admin' %}
    <h1>Admin Dashboard</h1>
    <p>Logged in as {{ session.user }}</p>
    <form method="POST" action="/send_message">
        <select name="student">
            {% for s in students %}
            <option value="{{ s }}">{{ s }}</option>
            {% endfor %}
        </select>
        <textarea name="message" placeholder="Message"></textarea>
        <button type="submit">Send Message</button>
    </form>
    <form method="POST" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Upload File</button>
    </form>
    <p><a href="/logout">Logout</a></p>

{% elif page == 'student' %}
    <h1>Student Dashboard</h1>
    <p>Logged in as {{ session.user }}</p>
    <h3>Messages:</h3>
    <ul>
        {% for msg in messages %}
            <li>{{ msg }}</li>
        {% endfor %}
    </ul>
    <h3>Files:</h3>
    <ul>
        {% for f in files %}
            <li><a href="/download/{{ f }}">{{ f }}</a></li>
        {% endfor %}
    </ul>
    <p><a href="/logout">Logout</a></p>
{% endif %}
</div>
</body>
</html>
"""

# ================= ROUTES =================
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        gmail = request.form.get("gmail", "").strip()
        if gmail.lower() == "lakshmipriyasnp@gmail.com":  # Admin login
            session["user"] = "admin"
            session["role"] = "admin"
            return redirect("/admin")
        for username, info in users.items():
            if info.get("gmail", "").lower() == gmail.lower():
                session["user"] = username
                session["role"] = "student"
                return redirect("/student")
        error = "Invalid Gmail"
    return render_template_string(PAGE_TEMPLATE, page="login", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username").strip()
        gmail = request.form.get("gmail").strip()
        if not username or not gmail:
            error = "Please fill all fields"
        elif any(info.get("gmail") == gmail for info in users.values()):
            error = "Gmail already exists"
        else:
            users[username] = {"gmail": gmail, "role": "student"}
            return redirect("/")
    return render_template_string(PAGE_TEMPLATE, page="register", error=error)

@app.route("/admin", methods=["GET"])
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    students = [u for u in users if users[u]["role"] == "student"]
    return render_template_string(PAGE_TEMPLATE, page="admin", students=students)

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
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return redirect("/admin")

@app.route("/student", methods=["GET"])
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")
    user = session.get("user")
    user_messages = messages.get(user, [])
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template_string(PAGE_TEMPLATE, page="student", messages=user_messages, files=files)

@app.route("/download/<filename>")
def download(filename):
    if session.get("role") not in ["admin", "student"]:
        abort(403)
    safe_filename = secure_filename(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_filename, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= MAIN =================
if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)

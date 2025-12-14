from flask import (
    Flask, render_template_string, request,
    redirect, session, send_from_directory, abort
)
import os
from werkzeug.utils import secure_filename

# ================= CONFIG =================
app = Flask(__name__)
app.secret_key = "CHANGE_THIS_TO_RANDOM_SECRET"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# ================= USERS =================
# username : gmail + role
users = {
    "Nimalpranav": {"gmail": "sanimalpranav@gmail.com", "role": "student"},
}

messages = {}

ADMIN_GMAIL = "lakshmipriyasnp@gmail.com"

# ================= SECURITY HEADERS =================
@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "img-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    )
    return response

# ================= SINGLE PAGE TEMPLATE =================
PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Secure Portal</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {
  --primary:#4f46e5;
  --secondary:#6366f1;
  --bg:#020617;
  --glass:rgba(255,255,255,.12);
  --border:rgba(255,255,255,.2);
  --text:#e5e7eb;
}
* { box-sizing:border-box; }
body {
  margin:0;
  min-height:100vh;
  font-family:Segoe UI, sans-serif;
  background:linear-gradient(135deg,#020617,#0f172a);
  display:flex;
  justify-content:center;
  align-items:center;
  color:var(--text);
}
.container {
  width:100%;
  max-width:520px;
  padding:35px;
  background:var(--glass);
  backdrop-filter:blur(18px);
  border-radius:18px;
  border:1px solid var(--border);
  box-shadow:0 20px 50px rgba(0,0,0,.6);
}
h1 { text-align:center; margin-bottom:25px; }
input, textarea, select {
  width:100%;
  padding:14px;
  margin:10px 0;
  border-radius:10px;
  border:1px solid var(--border);
  background:rgba(255,255,255,.08);
  color:var(--text);
}
button {
  width:100%;
  padding:14px;
  margin-top:15px;
  border:none;
  border-radius:12px;
  background:linear-gradient(135deg,var(--primary),var(--secondary));
  color:white;
  font-size:16px;
  font-weight:600;
  cursor:pointer;
}
button:hover { opacity:.9; }
a {
  display:block;
  text-align:center;
  margin-top:15px;
  color:#a5b4fc;
  text-decoration:none;
}
.error { color:#f87171; text-align:center; margin-top:10px; }
ul { list-style:none; padding:0; }
li {
  padding:10px;
  background:rgba(255,255,255,.08);
  border-radius:8px;
  margin-bottom:6px;
}
</style>
</head>
<body>
<div class="container">

{% if page == "login" %}
<h1>🔐 Login</h1>
<form method="POST">
  <input name="gmail" placeholder="Enter Gmail" required>
  <button>Login</button>
</form>
<a href="/register">Create Account</a>
{% if error %}<div class="error">{{ error }}</div>{% endif %}

{% elif page == "register" %}
<h1>📝 Register</h1>
<form method="POST">
  <input name="username" placeholder="Username" required>
  <input name="gmail" placeholder="Gmail" required>
  <button>Register</button>
</form>
<a href="/">Back to Login</a>
{% if error %}<div class="error">{{ error }}</div>{% endif %}

{% elif page == "admin" %}
<h1>🛠 Admin Dashboard</h1>

<form method="POST" action="/send_message">
  <select name="student">
    {% for s in students %}
      <option>{{ s }}</option>
    {% endfor %}
  </select>
  <textarea name="message" placeholder="Message"></textarea>
  <button>Send Message</button>
</form>

<form method="POST" action="/upload" enctype="multipart/form-data">
  <input type="file" name="file">
  <button>Upload File</button>
</form>

<a href="/logout">Logout</a>

{% elif page == "student" %}
<h1>🎓 Student Dashboard</h1>

<h3>📩 Messages</h3>
<ul>
{% for msg in messages %}
  <li>{{ msg }}</li>
{% endfor %}
</ul>

<h3>📂 Files</h3>
<ul>
{% for f in files %}
  <li><a href="/download/{{ f }}">{{ f }}</a></li>
{% endfor %}
</ul>

<a href="/logout">Logout</a>
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
        gmail = request.form.get("gmail", "").strip().lower()

        if gmail == ADMIN_GMAIL:
            session["user"] = "admin"
            session["role"] = "admin"
            return redirect("/admin")

        for username, info in users.items():
            if info["gmail"].lower() == gmail:
                session["user"] = username
                session["role"] = "student"
                return redirect("/student")

        error = "Invalid Gmail"

    return render_template_string(PAGE_TEMPLATE, page="login", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        gmail = request.form.get("gmail", "").strip().lower()

        if not username or not gmail:
            error = "All fields required"
        elif any(u["gmail"].lower() == gmail for u in users.values()):
            error = "Gmail already exists"
        else:
            users[username] = {"gmail": gmail, "role": "student"}
            return redirect("/")

    return render_template_string(PAGE_TEMPLATE, page="register", error=error)

@app.route("/admin")
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

@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")
    user = session["user"]
    user_messages = messages.get(user, [])
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template_string(
        PAGE_TEMPLATE, page="student",
        messages=user_messages, files=files
    )

@app.route("/download/<filename>")
def download(filename):
    if session.get("role") not in ["admin", "student"]:
        abort(403)
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        secure_filename(filename),
        as_attachment=True
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= MAIN =================
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_pyfile("config.py")


users = {
    "admin": {"password": "coding club admin", "role": "admin"},
    "Nimalpranav": {"password": "nimalpranav#jan84", "role": "student"},
}

messages = {}


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        if user in users and users[user]["password"] == pwd:
            session["user"] = user
            session["role"] = users[user]["role"]
            
            if users[user]["role"] == "admin":
                return redirect("/admin")
            else:
                return redirect("/student")

        return "Invalid credentials"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        # avoid duplicate
        if user in users:
            return "User already exists"

        users[user] = {"password": pwd, "role": "student"}
        return redirect("/")
    
    return render_template("register.html")

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admin_dashboard.html", students=[u for u in users if users[u]["role"]=="student"])



@app.route("/send_message", methods=["POST"])
def send_message():
    if session.get("role") != "admin":
        return redirect("/")

    student = request.form["student"]
    msg = request.form["message"]

    messages.setdefault(student, []).append(msg)

    return redirect("/admin")



@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role") != "admin":
        return redirect("/")

    file = request.files["file"]
    if not file:
        return redirect("/admin")

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
    return render_template("student_dashboard.html", messages=user_messages, files=files)



@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True,  host='0.0.0.0')

from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os, hashlib, datetime

app = Flask(__name__)
app.secret_key = "supersecret"

DATA_FILE = os.path.join("storage", "data.json")
LOG_DIR = "logs"
STAGES_DIR = os.path.join("storage", "stages")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(STAGES_DIR, exist_ok=True)

admin_password = "454545"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_stage_submission(username, stage, answer):
    stage_file = os.path.join(STAGES_DIR, f"stage{stage}.json")
    stage_data = {}
    if os.path.exists(stage_file):
        with open(stage_file, "r") as f:
            try: stage_data = json.load(f)
            except: stage_data = {}

    if username not in stage_data:
        stage_data[username] = []

    stage_data[username].append({
        "timestamp": str(datetime.datetime.now()),
        "answer": answer
    })

    with open(stage_file, "w") as f:
        json.dump(stage_data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        data = load_data()
        if username in data:
            return "Bu foydalanuvchi allaqachon mavjud"
        data[username] = {
            "password": hash_password(password),
            "score": 0,
            "stage": 1,
            "attempts": {},
            "correct_flags": 0
        }
        save_data(data)
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        data = load_data()
        user = data.get(username)
        if user and user["password"] == hash_password(password):
            session["username"] = username
            return redirect(url_for("ctf_stage", num=user["stage"]))
        return "Login yoki parol noto‘g‘ri"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/stage/<num>", methods=["GET", "POST"])
def ctf_stage(num):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    data = load_data()
    user = data[username]

    if request.method == "POST":
        action = request.form.get("action")
        user["attempts"][num] = user["attempts"].get(num, 0) + 1
        user["last_action"] = str(datetime.datetime.now())

        if action == "submit_flag":
            user_flag = request.form.get("flag_input", "").strip()
            if not user_flag:
                flash("⚠️ Flag maydoni bo'sh bo'lishi mumkin emas!", "warning")
            else:
                save_stage_submission(username, num, user_flag)
                with open(os.path.join(LOG_DIR, f"stage{num}_submissions.txt"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.datetime.now()} | {username} | {user_flag}\n")
                flash("✅ Javobingiz qabul qilindi va saqlandi.", "success")
                if int(num) >= user["stage"]:
                    user["stage"] = int(num) + 1
                save_data(data)
                return redirect(url_for("ctf_stage", num=str(user["stage"])))

        elif action == "skip":
            if int(num) >= user["stage"]:
                user["stage"] = int(num) + 1
            flash("⚠️ Bosqich o'tkazildi.", "info")
            save_data(data)
            return redirect(url_for("ctf_stage", num=str(user["stage"])))

        save_data(data)

    return render_template(f"stage{num}.html", num=num)
@app.route("/stage/7", methods=["GET", "POST"])
def ctf_stage_7():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    data = load_data()
    user = data[username]

    message = ""
    success = False

    if request.method == "POST":
        action = request.form.get("action")
        user["attempts"]["7"] = user["attempts"].get("7", 0) + 1
        user["last_action"] = str(datetime.datetime.now())

        if action == "submit_flag":
            submitted_pass = request.form.get("flag_input", "").strip()
            correct_password = "secret"  # ✅ Parol shu faylda yashiringan bo'ladi
            save_stage_submission(username, "7", submitted_pass)

            log_file = os.path.join(LOG_DIR, "stage7_submissions.txt")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now()} | {username} | {submitted_pass}\n")

            if submitted_pass == correct_password:
                message = "✅ To‘g‘ri parol! Siz muvaffaqiyatli topdingiz."
                success = True
                if 7 >= user["stage"]:
                    user["stage"] = 8
            else:
                message = "❌ Noto‘g‘ri parol. Qayta urinib ko‘ring."

        elif request.args.get("action") == "skip":
            if 7 >= user["stage"]:
                user["stage"] = 8
            save_data(data)
            return redirect(url_for("ctf_stage", num="8"))

        save_data(data)

    return render_template("stage7.html", message=message, success=success)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("admin_pass")
        if password != admin_password:
            return "Admin parol noto‘g‘ri"
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    return '''
    <form method="POST">
        <input type="password" name="admin_pass" placeholder="Admin paroli" required>
        <button type="submit">Kirish</button>
    </form>
    '''

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    data = load_data()
    return render_template("admin.html", data=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)


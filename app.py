from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
import os
import joblib
from datetime import datetime
from models import db, User, Student, History

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# AUTH SETUP
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ML MODEL SETUP
MODEL_PATH = "model/cedar_student_model.pkl"
DATASET = "dataset"
model = joblib.load(MODEL_PATH)

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.resize(th, (300, 150))

def similarity(img1, img2):
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    if des1 is None or des2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, True)
    return len(bf.match(des1, des2))

# ROUTES
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists.")
            return redirect(url_for('signup'))

        new_user = User(email=email, password=generate_password_hash(password, method='scrypt'))
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created! You can now login.")
        return redirect(url_for('login'))
    
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials.")
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('verify_page'))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/verify", methods=["GET"])
@login_required
def verify_page():
    students = sorted([d for d in os.listdir(DATASET) if os.path.isdir(os.path.join(DATASET, d))])
    return render_template("verify.html", students=students)

@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage_students():
    if request.method == "POST":
        student_name = request.form.get("student_name").strip().replace(" ", "_").lower()
        files = request.files.getlist("genuine_signatures")

        if not student_name:
            flash("Student name is required.")
            return redirect(url_for('manage_students'))

        student_dir = os.path.join(DATASET, student_name)
        genuine_dir = os.path.join(student_dir, "genuine")
        os.makedirs(genuine_dir, exist_ok=True)
        os.makedirs(os.path.join(student_dir, "forged"), exist_ok=True)

        for i, file in enumerate(files[:5]):
            if file:
                file.save(os.path.join(genuine_dir, f"genuine_{i+1}.png"))
        
        flash(f"Student '{student_name}' added with {len(files[:5])} signatures.")
        return redirect(url_for('manage_students'))

    students = sorted([d for d in os.listdir(DATASET) if os.path.isdir(os.path.join(DATASET, d))])
    return render_template("manage.html", students=students)

@app.route("/verify", methods=["POST"])
@login_required
def verify():
    student = request.form["student"]
    file = request.files["signature"]

    img_test = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    img_test = preprocess(img_test)

    gpath = os.path.join(DATASET, student, "genuine")
    genuine_sigs = os.listdir(gpath)

    scores = []
    for g in genuine_sigs[:5]:
        ref = preprocess(cv2.imread(os.path.join(gpath, g)))
        scores.append(similarity(img_test, ref))

    avg_score = np.mean(sorted(scores, reverse=True)[:3])
    prediction = model.predict([[avg_score]])[0]
    confidence = model.predict_proba([[avg_score]])[0][prediction] * 100

    THRESHOLD = 110
    result = "GENUINE" if avg_score >= THRESHOLD else "FORGED"
    if result == "FORGED":
        confidence = 100 - confidence

    # SAVE TO DATABASE
    new_record = History(
        student_name=student,
        result=result,
        confidence=round(confidence, 2),
        score=round(avg_score, 2),
        user_id=current_user.id
    )
    db.session.add(new_record)
    db.session.commit()

    return render_template(
        "result.html",
        student=student,
        result=result,
        confidence=round(confidence, 2),
        score=round(avg_score, 2)
    )

@app.route("/history")
@login_required
def show_history():
    history = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).limit(20).all()
    # Format database records for template compatibility
    history_list = []
    for h in history:
        history_list.append({
            "student": h.student_name,
            "result": h.result,
            "confidence": h.confidence,
            "time": h.timestamp.strftime("%d %b %Y %I:%M %p")
        })
    return render_template("history.html", history=history_list)

@app.route("/clear-history")
@login_required
def clear_history():
    History.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for('show_history'))

# OTHER ROUTES
@app.route("/about")
def about(): return render_template("about.html")

@app.route("/how")
def how(): return render_template("howitworks.html")

@app.route("/help")
def help(): return render_template("help.html")

# INITIALIZE DB
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request
import cv2
import numpy as np
import os
import joblib
from datetime import datetime

app = Flask(__name__)

MODEL_PATH = "model/cedar_student_model.pkl"
DATASET = "dataset"

model = joblib.load(MODEL_PATH)

# store last 5 verifications
history = []

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return cv2.resize(th, (300, 150))

def similarity(img1, img2):
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    if des1 is None or des2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, True)
    return len(bf.match(des1, des2))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/how")
def how():
    return render_template("howitworks.html")

@app.route("/help")
def help():
    return render_template("help.html")

# SHOW VERIFY PAGE
@app.route("/verify", methods=["GET"])
def verify_page():
    students = sorted(os.listdir(DATASET))
    return render_template("verify.html", students=students)

# PROCESS VERIFICATION
@app.route("/verify", methods=["POST"])
def verify():
    student = request.form["student"]
    file = request.files["signature"]

    img_test = cv2.imdecode(
        np.frombuffer(file.read(), np.uint8),
        cv2.IMREAD_COLOR
    )
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
    if avg_score < THRESHOLD:
        result = "FORGED"
        confidence = 100 - confidence
    else:
        result = "GENUINE"

    # ✅ SAVE HISTORY HERE (CORRECT PLACE)
    history.append({
    "student": student,
    "result": result,
    "confidence": round(confidence, 2),
    "time": datetime.now().strftime("%d %b %Y %I:%M %p")
})



    if len(history) > 5:
        history.pop(0)

    return render_template(
        "result.html",
        student=student,
        result=result,
        confidence=round(confidence, 2),
        score=round(avg_score, 2)
    )

# SHOW HISTORY
@app.route("/history")
def show_history():
    return render_template("history.html", history=history)
@app.route("/clear-history")
def clear_history():
    history.clear()
    return render_template("history.html", history=history)

if __name__ == "__main__":
    app.run(debug=True)

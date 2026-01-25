import cv2
import os
import numpy as np
import joblib
from sklearn.svm import SVC

DATASET = "dataset"
MODEL_PATH = "model/cedar_student_model.pkl"

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255,
                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.resize(th, (300, 150))

def similarity(img1, img2):
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    if des1 is None or des2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, True)
    return len(bf.match(des1, des2))

X, y = [], []

students = os.listdir(DATASET)

for student in students:
    gpath = os.path.join(DATASET, student, "genuine")
    fpath = os.path.join(DATASET, student, "forged")

    if not os.path.exists(gpath) or not os.path.exists(fpath):
        continue

    genuine = os.listdir(gpath)
    forged = os.listdir(fpath)

    # Genuine–Genuine
    for i in range(len(genuine) - 1):
        img1 = preprocess(cv2.imread(os.path.join(gpath, genuine[i])))
        img2 = preprocess(cv2.imread(os.path.join(gpath, genuine[i + 1])))
        X.append([similarity(img1, img2)])
        y.append(1)

    # Genuine–Forged
    for f in forged[:5]:
        img1 = preprocess(cv2.imread(os.path.join(gpath, genuine[0])))
        img2 = preprocess(cv2.imread(os.path.join(fpath, f)))
        X.append([similarity(img1, img2)])
        y.append(0)

model = SVC(kernel="rbf", probability=True)
model.fit(X, y)

joblib.dump(model, MODEL_PATH)
print("✅ CEDAR student-wise model trained and saved")

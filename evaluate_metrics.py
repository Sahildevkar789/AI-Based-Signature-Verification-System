import cv2, os, joblib, numpy as np

DATASET = "dataset"
MODEL = "model/cedar_student_model.pkl"
THRESHOLD = 110  # SAME threshold used in app

model = joblib.load(MODEL)

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255,
                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.resize(th, (300,150))

def similarity(img1, img2):
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    if des1 is None or des2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, True)
    return len(bf.match(des1, des2))

TP = TN = FP = FN = 0

students = os.listdir(DATASET)

for student in students:
    gpath = os.path.join(DATASET, student, "genuine")
    fpath = os.path.join(DATASET, student, "forged")
    if not os.path.exists(gpath): continue

    genuine = os.listdir(gpath)
    forged = os.listdir(fpath)

    # Test genuine samples
    for i in range(1, min(6, len(genuine))):
        test = preprocess(cv2.imread(os.path.join(gpath, genuine[i])))
        scores = []
        for ref in genuine[:5]:
            ref_img = preprocess(cv2.imread(os.path.join(gpath, ref)))
            scores.append(similarity(test, ref_img))
        avg = np.mean(sorted(scores, reverse=True)[:3])
        pred = model.predict([[avg]])[0]
        is_genuine = (avg >= THRESHOLD)

        if is_genuine:
            TP += 1
        else:
            FN += 1

    # Test forged samples
    for f in forged[:5]:
        test = preprocess(cv2.imread(os.path.join(fpath, f)))
        scores = []
        for ref in genuine[:5]:
            ref_img = preprocess(cv2.imread(os.path.join(gpath, ref)))
            scores.append(similarity(test, ref_img))
        avg = np.mean(sorted(scores, reverse=True)[:3])
        is_genuine = (avg >= THRESHOLD)

        if is_genuine:
            FP += 1
        else:
            TN += 1

accuracy = (TP + TN) / (TP + TN + FP + FN)
far = FP / (FP + TN) if (FP + TN) else 0
frr = FN / (FN + TP) if (FN + TP) else 0

print("📊 Evaluation Results")
print("Accuracy:", round(accuracy*100, 2), "%")
print("FAR:", round(far*100, 2), "%")
print("FRR:", round(frr*100, 2), "%")

import os
import shutil
import re

BASE = "dataset/signatures"
ORG = os.path.join(BASE, "full_org")
FORG = os.path.join(BASE, "full_forg")
OUT = "dataset"

os.makedirs(OUT, exist_ok=True)

def get_user_id(filename):
    # Extract first number from filename
    match = re.search(r"\d+", filename)
    if match:
        return match.group()
    return None

# -------- GENUINE --------
for file in os.listdir(ORG):
    if not file.lower().endswith(".png"):
        continue

    uid = get_user_id(file)
    if uid is None:
        continue

    student = f"student_{uid.zfill(3)}"
    gpath = os.path.join(OUT, student, "genuine")
    fpath = os.path.join(OUT, student, "forged")

    os.makedirs(gpath, exist_ok=True)
    os.makedirs(fpath, exist_ok=True)

    shutil.copy(os.path.join(ORG, file), gpath)

# -------- FORGED --------
for file in os.listdir(FORG):
    if not file.lower().endswith(".png"):
        continue

    uid = get_user_id(file)
    if uid is None:
        continue

    student = f"student_{uid.zfill(3)}"
    fpath = os.path.join(OUT, student, "forged")

    os.makedirs(fpath, exist_ok=True)
    shutil.copy(os.path.join(FORG, file), fpath)

print("✅ CEDAR dataset converted successfully (robust method)")

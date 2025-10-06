# faceunlock.py
import os
import cv2
import numpy as np
import webbrowser
import time
import shutil
from datetime import datetime
from cryptography.fernet import Fernet

# Try importing LBPH
try:
    from cv2.face import LBPHFaceRecognizer_create
except Exception as e:
    raise RuntimeError("OpenCV 'face' module not found. Install opencv-contrib-python.") from e

# === DEFAULT CONFIG (can be overridden via function args) ===
RECOGNIZER_PATH = r"C:/Users/hardy/OneDrive/Desktop/Face/trainer/trainer.yml"
KEY_FILE = "folderkey.key"
ENCRYPTED_FOLDER = r"C:/Users/hardy/OneDrive/Desktop/Hardyapp_encrypted"
UNLOCKED_FOLDER = r"C:/Users/hardy/OneDrive/Desktop/Hardyapp_unlocked"
LOG_IMAGE_FOLDER = os.path.join("static", "facelogs")
LOG_TEXT_FILE = "face_log.txt"
DELETE_AFTER_SECONDS = 3000  # ~50 minutes

os.makedirs(LOG_IMAGE_FOLDER, exist_ok=True)

def _load_fernet(key_file: str) -> Fernet:
    if not os.path.exists(key_file):
        raise FileNotFoundError(
            f"Key file not found: {key_file}\nGenerate it by running encryption once."
        )
    with open(key_file, "rb") as kf:
        key = kf.read()
    return Fernet(key)

def _scan_face_and_verify(recognizer_path: str, show_window: bool = True) -> bool:
    recognizer = LBPHFaceRecognizer_create()
    if not os.path.exists(recognizer_path):
        raise FileNotFoundError(f"Recognizer model not found:\n{recognizer_path}")
    recognizer.read(recognizer_path)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise RuntimeError("Failed to access camera.")

    print("🔍 Scanning for your face… (press 'q' to cancel)")
    access_granted = False

    while True:
        ret, frame = cam.read()
        if not ret:
            print("⚠️ Failed to read from camera.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100)
        )

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            face_id, confidence = recognizer.predict(roi_gray)
            score = round(100 - confidence)

            # Green bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if confidence < 60:
                print(f"✅ Access Granted | Confidence: {score}%")
                access_granted = True
                break
            else:
                print(f"❌ Access Denied | Confidence: {score}%")
                # Save resized face crop (medium size)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                face_crop = frame[y:y + h, x:x + w]
                try:
                    resized = cv2.resize(face_crop, (300, 300))
                    image_path = os.path.join(LOG_IMAGE_FOLDER, f"{timestamp}_rejected.jpg")
                    cv2.imwrite(image_path, resized)
                except Exception as e:
                    print(f"⚠️ Failed to save rejected face image: {e}")

                # Append text log
                try:
                    with open(LOG_TEXT_FILE, "a", encoding="utf-8") as logf:
                        logf.write(f"[{timestamp}] ❌ Access Denied | Confidence: {score}%\n")
                except Exception as e:
                    print(f"⚠️ Failed to write log file: {e}")

        if show_window:
            cv2.imshow("Face Unlock", frame)

        if access_granted:
            break

        if show_window and (cv2.waitKey(1) & 0xFF == ord('q')):
            print("⛔ Cancelled by user.")
            break

    cam.release()
    if show_window:
        cv2.destroyAllWindows()

    return access_granted

def _decrypt_all(fernet: Fernet, encrypted_folder: str, unlocked_folder: str):
    os.makedirs(unlocked_folder, exist_ok=True)

    total = 0
    done = 0
    for root, dirs, files in os.walk(encrypted_folder):
        for file in files:
            if file.endswith(".encrypted"):
                total += 1
                enc_path = os.path.join(root, file)
                rel = os.path.relpath(enc_path, encrypted_folder)
                out_dir = os.path.join(unlocked_folder, os.path.dirname(rel))
                os.makedirs(out_dir, exist_ok=True)

                with open(enc_path, "rb") as ef:
                    enc_data = ef.read()
                try:
                    dec_data = fernet.decrypt(enc_data)
                    original_name = os.path.basename(file).replace(".encrypted", "")
                    out_path = os.path.join(out_dir, original_name)
                    with open(out_path, "wb") as of:
                        of.write(dec_data)
                    done += 1
                except Exception as e:
                    print(f"⚠️ Failed to decrypt {enc_path}: {e}")
    return total, done

def _maybe_open_index(unlocked_folder: str):
    index_path = os.path.join(unlocked_folder, "index.html")
    if os.path.exists(index_path):
        webbrowser.open(index_path)
        return True
    return False

def _schedule_autodelete(unlocked_folder: str, seconds: int):
    print(f"🕒 Auto-deleting '{unlocked_folder}' in {seconds // 60} minutes…")
    try:
        time.sleep(seconds)
        shutil.rmtree(unlocked_folder, ignore_errors=True)
        print("🧹 Unlocked folder deleted for security.")
    except Exception as e:
        print(f"⚠️ Auto-delete failed: {e}")

def face_unlock_and_decrypt(
    recognizer_path: str = RECOGNIZER_PATH,
    key_file: str = KEY_FILE,
    encrypted_folder: str = ENCRYPTED_FOLDER,
    unlocked_folder: str = UNLOCKED_FOLDER,
    log_image_folder: str = LOG_IMAGE_FOLDER,
    log_text_file: str = LOG_TEXT_FILE,
    delete_after_seconds: int = DELETE_AFTER_SECONDS,
    show_window: bool = True
):
    """
    Returns: (ok: bool, message: str)
    """
    global LOG_IMAGE_FOLDER, LOG_TEXT_FILE
    LOG_IMAGE_FOLDER = log_image_folder
    LOG_TEXT_FILE = log_text_file
    os.makedirs(LOG_IMAGE_FOLDER, exist_ok=True)

    # 1) Face verification
    ok = _scan_face_and_verify(recognizer_path=recognizer_path, show_window=show_window)
    if not ok:
        return False, "Access denied or cancelled. No files were unlocked."

    # 2) Decrypt
    fernet = _load_fernet(key_file)
    total, done = _decrypt_all(fernet, encrypted_folder, unlocked_folder)
    print(f"📂 Unlocked folder at: '{unlocked_folder}'")

    # 3) Open index.html if present
    opened = _maybe_open_index(unlocked_folder)
    if not opened:
        print("ℹ️ index.html not found in unlocked folder.")

    # 4) Auto-delete (in a background thread so caller can return)
    import threading
    threading.Thread(target=_schedule_autodelete,
                     args=(unlocked_folder, delete_after_seconds),
                     daemon=True).start()

    return True, f"✅ Decrypted {done}/{total} files into:\n{unlocked_folder}\n(Will auto-delete after {delete_after_seconds // 60} minutes.)"

# --- Run standalone for testing ---
if __name__ == "__main__":
    ok, msg = face_unlock_and_decrypt(
        recognizer_path=RECOGNIZER_PATH,
        key_file=KEY_FILE,
        encrypted_folder=ENCRYPTED_FOLDER,
        unlocked_folder=UNLOCKED_FOLDER,
        log_image_folder=LOG_IMAGE_FOLDER,
        log_text_file=LOG_TEXT_FILE,
        delete_after_seconds=DELETE_AFTER_SECONDS,
        show_window=True
    )
    print(msg)

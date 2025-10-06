import cv2
import numpy as np
import os
from cryptography.fernet import Fernet

# Load trained recognizer
from cv2.face import LBPHFaceRecognizer_create
recognizer = LBPHFaceRecognizer_create()
recognizer.read("trainer/trainer.yml")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Load your encryption key
with open("filekey.key", "rb") as key_file:
    key = key_file.read()
fernet = Fernet(key)

# File paths
encrypted_file = "secret_file.encrypted"
decrypted_file = "unlocked_secret.txt"

cam = cv2.VideoCapture(0)
print("🔍 Scanning for your face...")

access_granted = False

while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
        print(f"Detected face with confidence: {round(100 - confidence)}%")

        if confidence < 60:
            print("✅ Face matched. Decrypting file...")
            with open(encrypted_file, "rb") as ef:
                encrypted_data = ef.read()

            decrypted_data = fernet.decrypt(encrypted_data)
            with open(decrypted_file, "wb") as df:
                df.write(decrypted_data)

            print(f"📂 File unlocked successfully: {decrypted_file}")
            access_granted = True
            break
        else:
            print("❌ Face not recognized. Access denied.")

    cv2.imshow("Face Verification", frame)

    if access_granted or cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()

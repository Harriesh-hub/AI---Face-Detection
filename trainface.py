import cv2
import numpy as np
import os

# === Setup ===
dataset_dir = "dataset"
trainer_dir = "trainer"
os.makedirs(dataset_dir, exist_ok=True)
os.makedirs(trainer_dir, exist_ok=True)

# === Load face detection model ===
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
cam = cv2.VideoCapture(0)

user_id = 1  # Your unique ID
sample_count = 0
total_samples = 40

print("📸 Capturing your face. Look at the camera...")
while True:
    ret, frame = cam.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        sample_count += 1
        face_img = gray[y:y+h, x:x+w]
        filename = f"{dataset_dir}/User.{user_id}.{sample_count}.jpg"
        cv2.imwrite(filename, face_img)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow("Capturing Face (Q to quit)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q') or sample_count >= total_samples:
        break

cam.release()
cv2.destroyAllWindows()
print(f"✅ Captured {sample_count} face images.\n⏳ Now training model...")

# === Training the recognizer ===
from cv2.face import LBPHFaceRecognizer_create
recognizer = LBPHFaceRecognizer_create()

faces = []
ids = []

for filename in os.listdir(dataset_dir):
    if filename.endswith(".jpg"):
        img_path = os.path.join(dataset_dir, filename)
        gray_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        user_id = int(filename.split('.')[1])
        faces.append(gray_img)
        ids.append(user_id)

recognizer.train(faces, np.array(ids))
recognizer.save(f"{trainer_dir}/trainer.yml")

print("🎉 Face model trained and saved as trainer/trainer.yml")

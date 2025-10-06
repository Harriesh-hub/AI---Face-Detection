import cv2
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import datetime
import subprocess

ADMIN_FACE_PATH = "face_data/admin.jpg"
LOGS_PATH = "logs"

os.makedirs("face_data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def capture_admin_face():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            admin_face = gray[y:y + h, x:x + w]
            admin_face = cv2.resize(admin_face, (200, 200))
            cv2.imwrite(ADMIN_FACE_PATH, admin_face)
            cap.release()
            cv2.destroyAllWindows()
            messagebox.showinfo("Success", "Admin face captured!")
            return
        cv2.imshow("Capture Admin Face - Press Q to Cancel", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def recognize_face_and_open_file(filepath):
    if not os.path.exists(ADMIN_FACE_PATH):
        messagebox.showerror("Error", "Admin face not registered!")
        return

    cap = cv2.VideoCapture(0)
    access_granted = False

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y + h, x:x + w]
            face_img = cv2.resize(face_img, (200, 200))
            admin_face = cv2.imread(ADMIN_FACE_PATH, cv2.IMREAD_GRAYSCALE)

            diff = cv2.absdiff(admin_face, face_img)
            score = diff.mean()

            if score < 40:  # You can adjust this threshold
                access_granted = True
                cap.release()
                cv2.destroyAllWindows()
                subprocess.Popen(["explorer", filepath], shell=True)
                return
            else:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                log_path = os.path.join(LOGS_PATH, f"fraud_{timestamp}.jpg")
                face_crop = frame[y:y + h, x:x + w]
                face_crop = cv2.resize(face_crop, (150, 150))
                cv2.imwrite(log_path, face_crop)
                messagebox.showerror("Access Denied", "Face not recognized. Fraud logged.")
                cap.release()
                cv2.destroyAllWindows()
                return

        cv2.imshow("Face Recognition - Press Q to Cancel", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def drag_and_drop(event):
    filepath = event.data.strip("{}")  # Remove brackets from paths with spaces
    if not os.path.isfile(filepath):
        messagebox.showerror("Invalid", "Drop a valid file.")
        return
    btn = messagebox.askyesno("Confirmation", f"Do you want to register face and lock '{os.path.basename(filepath)}'?")
    if btn:
        capture_admin_face()
        shutil.copy(filepath, "face_data/locked_file")
        messagebox.showinfo("Locked", "File is now face-locked.")
    else:
        recognize_face_and_open_file(filepath)

# GUI Setup
root = tk.Tk()
root.title("Face Lock for Files")
root.geometry("500x400")
root.configure(bg="black")

label = tk.Label(root, text="Drag and Drop Your File Here", bg="black", fg="lime", font=("Arial", 18))
label.pack(pady=60)

drop_area = tk.Label(root, text="⬇️ Drop File Here ⬇️", bg="gray20", fg="white", width=40, height=10, relief="groove")
drop_area.pack(pady=20)

# Drag and drop binding (Windows-specific)
try:
    import tkinterdnd2 as tkdnd
    root = tkdnd.TkinterDnD.Tk()
    drop_area = tkdnd.TkinterDnD.Label(root, text="⬇️ Drop File Here ⬇️", bg="gray20", fg="white", width=40, height=10)
    drop_area.pack(pady=60)
    drop_area.drop_target_register(tkdnd.DND_FILES)
    drop_area.dnd_bind("<<Drop>>", drag_and_drop)
except:
    messagebox.showerror("Missing Module", "Install tkinterdnd2: pip install tkinterdnd2")

root.mainloop()

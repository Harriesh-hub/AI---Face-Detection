# gui_app.py
import os
import threading
import time
import random
import tkinter as tk
from tkinter import filedialog, messagebox
from cryptography.fernet import Fernet

# === If faceunlock.py is in the same folder ===
import faceunlock  # uses face_unlock_and_decrypt()

# ----------------------------
# CONFIG (match faceunlock.py)
# ----------------------------
RECOGNIZER_PATH = r"C:/Users/hardy/OneDrive/Desktop/Face/trainer/trainer.yml"
KEY_FILE = "folderkey.key"
ENCRYPTED_FOLDER = r"C:/Users/hardy/OneDrive/Desktop/Hardyapp_encrypted"
UNLOCKED_FOLDER = r"C:/Users/hardy/OneDrive/Desktop/Hardyapp_unlocked"
LOG_IMAGE_FOLDER = os.path.join("static", "facelogs")
LOG_TEXT_FILE = "face_log.txt"
DELETE_AFTER_SECONDS = 3000  # 50 minutes

os.makedirs(LOG_IMAGE_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)

# ----------------------------
# Particle Motion Background
# ----------------------------
PALETTE = [
    "#4B0082",  # indigo
    "#FF0000",  # red
    "#00FFFF",  # cyan
    "#20B2AA",  # seafoam-ish (light sea green)
    "#8A2BE2",  # violet
    "#800080",  # purple
    "#800000",  # maroon
    "#00FF00",  # green
    "#FFFFFF",  # white
]
SPEED_SCALE = 0.8  # ~0.8x feel

class Particle:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.dx = random.choice([-1, 1]) * random.uniform(0.2, 1.0) * SPEED_SCALE
        self.dy = random.choice([-1, 1]) * random.uniform(0.2, 1.0) * SPEED_SCALE
        self.size = random.randint(2, 4)
        self.color = random.choice(PALETTE)
        self.id = canvas.create_oval(self.x, self.y, self.x+self.size, self.y+self.size,
                                     fill=self.color, outline="")

    def move(self, width, height):
        self.x += self.dx
        self.y += self.dy

        if self.x <= 0 or self.x >= width:
            self.dx *= -1
        if self.y <= 0 or self.y >= height:
            self.dy *= -1

        self.canvas.move(self.id, self.dx, self.dy)

def animate_particles(particles, canvas, width, height):
    def loop():
        while True:
            for p in particles:
                p.move(width, height)
            canvas.update()
            time.sleep(0.01)
    threading.Thread(target=loop, daemon=True).start()

# ----------------------------
# Loading Overlay (non-blocking)
# ----------------------------
class Loading:
    def __init__(self, root, message):
        self.top = tk.Toplevel(root)
        self.top.title("Please wait…")
        self.top.configure(bg="#111111")
        self.top.resizable(False, False)
        self.top.geometry("360x140")
        self.top.transient(root)
        self.top.grab_set()

        self.label = tk.Label(self.top, text=message,
                              font=("Segoe UI", 12, "bold"),
                              bg="#111111", fg="#00FFEF")
        self.label.pack(pady=(24, 8))

        self.dots = tk.Label(self.top, text="", font=("Segoe UI", 12),
                             bg="#111111", fg="#00FFEF")
        self.dots.pack()

        self._running = True
        self._animate()

    def _animate(self):
        if not self._running:
            return
        current = self.dots.cget("text")
        current = (current + ".") if len(current) < 3 else ""
        self.dots.config(text=current)
        self.top.after(300, self._animate)

    def update_message(self, msg):
        self.label.config(text=msg)

    def close(self):
        self._running = False
        try:
            self.top.grab_release()
        except:
            pass
        self.top.destroy()

# ----------------------------
# Crypto helpers
# ----------------------------
def ensure_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    with open(KEY_FILE, "rb") as f:
        return Fernet(f.read())

def encrypt_folder(source_folder, encrypted_folder):
    fernet = ensure_key()
    os.makedirs(encrypted_folder, exist_ok=True)

    count_total = 0
    count_done = 0
    files_to_encrypt = []
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            files_to_encrypt.append(os.path.join(root, file))
    count_total = len(files_to_encrypt)

    for fullpath in files_to_encrypt:
        rel = os.path.relpath(fullpath, source_folder)
        out_dir = os.path.join(encrypted_folder, os.path.dirname(rel))
        os.makedirs(out_dir, exist_ok=True)

        with open(fullpath, "rb") as rf:
            raw = rf.read()
        enc = fernet.encrypt(raw)
        outpath = os.path.join(out_dir, os.path.basename(rel) + ".encrypted")
        with open(outpath, "wb") as wf:
            wf.write(enc)
        count_done += 1

    return count_total, count_done

# ----------------------------
# Button Logic (threaded)
# ----------------------------
def encrypt_folder_with_face(root):
    folder = filedialog.askdirectory(title="Select Folder to Encrypt")
    if not folder:
        return

    loading = Loading(root, "Encrypting folder…")
    def worker():
        try:
            total, done = encrypt_folder(folder, ENCRYPTED_FOLDER)
            loading.update_message(f"Finished: {done}/{total} files")
            time.sleep(0.4)
            loading.close()
            messagebox.showinfo("Success",
                                f"✅ Encrypted {done} / {total} files to:\n{ENCRYPTED_FOLDER}\n\nKey saved in: {KEY_FILE}")
        except Exception as e:
            loading.close()
            messagebox.showerror("Error", f"Encryption failed:\n{e}")
    threading.Thread(target=worker, daemon=True).start()

def decrypt_folder_with_face(root):
    loading = Loading(root, "Starting face scan…")
    def worker():
        try:
            ok, msg = faceunlock.face_unlock_and_decrypt(
                recognizer_path=RECOGNIZER_PATH,
                key_file=KEY_FILE,
                encrypted_folder=ENCRYPTED_FOLDER,
                unlocked_folder=UNLOCKED_FOLDER,
                log_image_folder=LOG_IMAGE_FOLDER,
                log_text_file=LOG_TEXT_FILE,
                delete_after_seconds=DELETE_AFTER_SECONDS,
                show_window=True  # show OpenCV window during scan
            )
            loading.close()
            if ok:
                messagebox.showinfo("Decryption", msg)
            else:
                messagebox.showwarning("Access Denied", msg)
        except Exception as e:
            loading.close()
            messagebox.showerror("Error", f"Decryption failed:\n{e}")
    threading.Thread(target=worker, daemon=True).start()

# ----------------------------
# UI wiring
# ----------------------------
def on_enter(e):
    e.widget.config(bg="#00FFEF", fg="#000000")

def on_leave(e):
    e.widget.config(bg="#111111", fg="#FFFFFF")

def create_button(parent, text, cmd):
    btn = tk.Button(parent,
                    text=text,
                    command=cmd,
                    font=("Segoe UI", 14, "bold"),
                    bg="#111111", fg="#FFFFFF",
                    activebackground="#00FFEF", activeforeground="#000000",
                    relief="flat", padx=20, pady=10, cursor="hand2")
    btn.pack(pady=12, ipadx=10, ipady=5, fill="x")
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn

def main():
    WIDTH, HEIGHT = 720, 480
    root = tk.Tk()
    root.title("🔐 Pro Face-Lock Folder Protector")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    root.resizable(False, False)

    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                       highlightthickness=0, bg="#000000")
    canvas.pack(fill="both", expand=True)

    particles = [Particle(canvas, WIDTH, HEIGHT) for _ in range(42)]
    animate_particles(particles, canvas, WIDTH, HEIGHT)

    frame = tk.Frame(canvas, bg="#111111")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    title = tk.Label(frame,
                     text="🔒 Secure Face Lock 🔍",
                     font=("Segoe UI", 24, "bold"),
                     bg="#111111", fg="#00FFEF")
    title.pack(pady=(18, 8))

    subtitle = tk.Label(frame,
                        text="Encrypt with a key • Decrypt only with your face",
                        font=("Segoe UI", 11),
                        bg="#111111", fg="#BBBBBB")
    subtitle.pack(pady=(0, 16))

    create_button(frame, "🛡️ Encrypt Folder (With Face)",
                  lambda: encrypt_folder_with_face(root))
    create_button(frame, "🔓 Decrypt Folder (With Face)",
                  lambda: decrypt_folder_with_face(root))

    root.mainloop()

if __name__ == "__main__":
    main()

import os
from cryptography.fernet import Fernet
import webbrowser

key_file = "folderkey.key"
encrypted_folder = "Hardyapp_encrypted"
unlocked_folder = "Hardyapp_unlocked"

os.makedirs(unlocked_folder, exist_ok=True)

if not os.path.exists(key_file):
    print("❌ No key file found.")
    exit()

with open(key_file, "rb") as kf:
    key = kf.read()

fernet = Fernet(key)

decrypted = False

for file in os.listdir(encrypted_folder):
    if file.endswith(".encrypted"):
        enc_path = os.path.join(encrypted_folder, file)
        with open(enc_path, "rb") as ef:
            enc_data = ef.read()

        try:
            dec_data = fernet.decrypt(enc_data)
            original_name = file.replace(".encrypted", "")
            out_path = os.path.join(unlocked_folder, original_name)
            with open(out_path, "wb") as df:
                df.write(dec_data)
            decrypted = True
            print(f"✅ Decrypted: {original_name}")
        except Exception as e:
            print(f"❌ Failed to decrypt {file}: {e}")

if decrypted:
    index_path = os.path.join(unlocked_folder, "index.html")
    if os.path.exists(index_path):
        webbrowser.open(index_path)
    else:
        print("⚠️ index.html not found in unlocked folder.")
else:
    print("⚠️ No encrypted files found or decryption failed.")

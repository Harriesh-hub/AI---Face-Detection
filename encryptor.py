import os
import sys
from cryptography.fernet import Fernet

if len(sys.argv) < 2:
    print("❌ No file passed for encryption.")
    sys.exit()

file_to_encrypt = sys.argv[1]
if not os.path.isfile(file_to_encrypt):
    print(f"❌ File not found: {file_to_encrypt}")
    sys.exit()

key_path = "folderkey.key"
output_folder = "Hardyapp_encrypted"
os.makedirs(output_folder, exist_ok=True)

# Load or generate key
if not os.path.exists(key_path):
    key = Fernet.generate_key()
    with open(key_path, "wb") as kf:
        kf.write(key)
else:
    with open(key_path, "rb") as kf:
        key = kf.read()

fernet = Fernet(key)

# Encrypt file
with open(file_to_encrypt, "rb") as f:
    data = f.read()
enc_data = fernet.encrypt(data)

filename = os.path.basename(file_to_encrypt)
enc_path = os.path.join(output_folder, filename + ".encrypted")

with open(enc_path, "wb") as ef:
    ef.write(enc_data)

print(f"✅ Encrypted: {enc_path}")

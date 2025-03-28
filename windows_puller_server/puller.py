import os
import csv
import time
import requests
from datetime import datetime
from pydub import AudioSegment

# ----------------------
# Configuration
# ----------------------
TOKEN = "supersecrettoken"  
BASE_URL = "https://tron-ia.com"
DEST_FOLDER = r"C:\programa_jacobo\test"
MANIFEST_URL = f"{BASE_URL}/manifest?token={TOKEN}"
GET_FILE_URL = f"{BASE_URL}/get-audio"
ACK_URL = f"{BASE_URL}/acknowledge-audio?token={TOKEN}"
ACK_LOG = os.path.join(DEST_FOLDER, "ack_log.csv")

# ----------------------
# Utility Functions
# ----------------------

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_ack_log():
    if not os.path.exists(ACK_LOG):
        return set()

    with open(ACK_LOG, "r", encoding="utf-8") as f:
        return {row[0] for row in csv.reader(f) if row}

def log_ack(filename):
    with open(ACK_LOG, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([filename, datetime.now().isoformat()])

def convert_ogg_to_mp3(source_path, target_path):
    try:
        audio = AudioSegment.from_file(source_path, format="ogg")
        audio.export(target_path, format="mp3")
        print(f"Converted to MP3: {target_path}")
    except Exception as e:
        print(f"Failed to convert {source_path} to MP3: {e}")


def convert_to_mp3(source_path, target_path):
    try:
        audio = AudioSegment.from_file(source_path)
        audio.export(target_path, format="mp3")
        print(f"🎧 Converted to MP3: {target_path}")
    except Exception as e:
        print(f"❌ Failed to convert {source_path} to MP3: {e}")


def download_file(filename):
    url = f"{GET_FILE_URL}/{filename}?token={TOKEN}"
    source_path = os.path.join(DEST_FOLDER, filename)
    mp3_path = os.path.join(DEST_FOLDER, filename.rsplit(".", 1)[0] + ".mp3")

    print(f"\n⬇ Downloading {filename}...")

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(source_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Saved to {source_path}")

        # Convert to MP3 (regardless of format)
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in [".ogg", ".mp4"]:
            convert_to_mp3(source_path, mp3_path)
            os.remove(source_path)
            print(f"🗑️ Deleted original file: {source_path}")
        else:
            print(f"⚠️ Unsupported file type: {file_ext} (skipped conversion)")

        return True
    except Exception as e:
        print(f"❌ Failed to download or convert {filename}: {e}")
        return False
        

def send_ack(filename):
    try:
        response = requests.post(ACK_URL, json={"filename": filename})
        if response.status_code == 200:
            print(f"✅ ACK sent for {filename}")
            return True
        else:
            print(f"❌ ACK failed for {filename}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ACK exception for {filename}: {e}")
        return False

# ----------------------
# Main Loop Logic
# ----------------------

def sync_audio_files():
    ensure_folder(DEST_FOLDER)
    acked_files = load_ack_log()

    print("🔄 Fetching manifest...")
    try:
        response = requests.get(MANIFEST_URL)
        response.raise_for_status()
        manifest = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch manifest: {e}")
        return

    files = manifest.get("files", [])
    for entry in files:
        if not entry or "null" not in entry:
            continue

        row = entry["null"]
        if len(row) < 4:
            continue

        filename, received = row[1], row[3].strip().lower()

        if filename in acked_files:
            if received != "true":
                print(f"🔁 Re-ACKing {filename}...")
                if send_ack(filename):
                    log_ack(filename)
            continue

        if received == "true":
            continue  # Already acknowledged, skip

        # Download and ACK
        if download_file(filename):
            if send_ack(filename):
                log_ack(filename)

if __name__ == "__main__":
    while True:
        sync_audio_files()
        time.sleep(60)  # wait 1 min before next run

import os
import csv
import time
import requests
from datetime import datetime
from pydub import AudioSegment
#
#FILENAME SAMPLE: 2025-03-26_hora_17-43-37_EstudiosEspeciales_JR.ogg|
#
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

# Map doctor initials to full names
DOCTOR_NAMES = {
    "JR": "Jacobo Ruiz",
    "VR": "Victor Hugo Ruiz",
    # Add more mappings as needed
}

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

def convert_to_mp3(source_path, target_path, bitrate="192k"):
    try:
        audio = AudioSegment.from_file(source_path)
        audio.export(target_path, format="mp3", bitrate=bitrate, parameters=["-acodec", "libmp3lame", "-b:a", bitrate])
        print(f"🎧 Converted to MP3: {target_path} at {bitrate}")
    except Exception as e:
        print(f"❌ Failed to convert {source_path} to MP3: {e}")


def download_file(filename, urgent):
    url = f"{GET_FILE_URL}/{filename}?token={TOKEN}"

    # Parse the filename
    try:
        parts = filename.split("_")
        date_str = parts[0]  # e.g. '2025-03-26'
        time_str = parts[2]  # e.g. '17-43-37'
        study_type = parts[3]
        doctor_initials = parts[4].split(".")[0]

        # Combine and parse timestamp
        file_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H-%M-%S")
        now = datetime.now()

        # Check if at least 1 minute has passed
        if file_time + timedelta(minutes=1) > now:
            print(f"⏳ Skipping {filename}: too recent (less than 1 minute old).")
            return False

    except (IndexError, ValueError) as e:
        print(f"❌ Invalid filename format or time parsing failed: {filename}, error: {e}")
        return False

    doctor_full_name = DOCTOR_NAMES.get(doctor_initials, doctor_initials)

    # Determine destination folder
    if urgent:
        target_folder = os.path.join(DEST_FOLDER, "URGENTE")
    else:
        target_folder = os.path.join(DEST_FOLDER, study_type, doctor_full_name)

    os.makedirs(target_folder, exist_ok=True)

    source_path = os.path.join(target_folder, filename)
    mp3_path = os.path.join(target_folder, filename.rsplit(".", 1)[0] + ".mp3")

    print(f"\n⬇ Downloading {filename} to {target_folder}...")

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(source_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Saved to {source_path}")

        # Convert to MP3 if needed
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
        if len(row) < 5:
            continue
        # waid, filename, urgent, delete, received
        filename = row[1]
        # they are all booleans
        urgent = row[2].strip().lower() == "true"
        delete = row[3].strip().lower() == "true"
        received = row[4].strip().lower() == "true"

        if filename in acked_files:
            if not received:
                print(f"🔁 Re-ACKing {filename}...")
                if send_ack(filename):
                    log_ack(filename)
            continue

        if received:
            continue  # Already acknowledged, skip

        # Download and ACK
        if download_file(filename, urgent):
            if send_ack(filename):
                log_ack(filename)

if __name__ == "__main__":
    while True:
        sync_audio_files()
        time.sleep(60)  # wait 1 min before next run

import requests
import os
import csv
import subprocess
ACCESS_TOKEN= "EAAZAZAfZBwzNvgBOZBrXU1TqvxUKizp8RRDqUDC9mnZBx6pIF0Puen4otPynkBRx3lxvYEoIRAm3UTG85hQqyj2koLWAVz0RrdSFb92j2M4t45oujgZCAOPcaumPXqjbbqyESGqkjn9bru6aCZAZCCZAkKVP7pOtACTlpnjSSvWYU1A4GvurZCA6kMqTfDx54Q543rQIVFihfcebF5kJJA9wGis6ucNKgZD"

url = "https://api.botpress.cloud/v1/files/file_01JNF4AWK48DD3173SZTQ5MH7H"

headers = {
    "accept": "application/json",
    "x-bot-id": "091bb0a2-e037-4ad6-863d-67a49e2bb373",
    "x-workspace-id": "wkspace_01JNCRZWWNVK7YECRTE59B9ZVQ",
    "authorization": "Bearer bp_pat_y4ZWW3T5Lxsq1ldSQWMMIwrjNvwjikB2gzAm"
}

response = requests.get(url, headers=headers)

# Check if the response was successful
if response.status_code == 200:
    # Parse the JSON response
    response_json = response.json()

    # Extract the file URL
    file_url = response_json["file"]["url"]
    print("File URL OK")

else:
    print("Failed to get file URL. Status code:", response.status_code)


# Make a request to download the file
response = requests.get(file_url)


# Define the folder where you want to save the file
save_folder = "/Users/jacoboruiz/Desktop/audio whatsapp/"  # Change this to your desired folder

# Ensure the folder exists
os.makedirs(save_folder, exist_ok=True)

# Define the full file path
file_name = "downloaded_file.csv"
file_path = os.path.join(save_folder, file_name)


# Check if the request was successful
if response.status_code == 200:
    # Save the file
    with open(file_path, "wb") as file:
        file.write(response.content)
    print("File downloaded successfully as 'downloaded_file.csv'")
else:
    print(f"Failed to download the file. Status code: {response.status_code}")


# Read the CSV file and download audio files
with open(file_path, "r", encoding="utf-8") as csv_file:
    csv_reader = csv.reader(csv_file)
    
    # Skip the header
    next(csv_reader, None)

    for row in csv_reader:
        created_at = row[1]  # Created At column
        doctor_name = row[3]  # Doctor name column
        exam_type = row[4]  # Exam type column
        audio_url = row[5]  # Audio URL column
        
        if audio_url.strip():  # Ensure the URL is not empty
            # Extract the date, hour, and minute (YYYY-MM-DDTHH:MM)
            created_at_trimmed = created_at[:16]  # Keeps only "2025-03-03T22:54"
            created_at_trimmed = created_at_trimmed.replace("T", "_")  # Replace 'T' with '_'

            # Construct the filename as column1_column3_column4.mp3
            audio_filename = f"{row[0]}_{created_at_trimmed}_{doctor_name}_{exam_type}.mp3"

            # Remove spaces from the filename to avoid issues
            audio_filename = audio_filename.replace(" ", "_")

            # Define full file path
            audio_path = os.path.join(save_folder, audio_filename)

            # Download the audio using curl
            curl_command = [
                "curl",
                "-H", f"Authorization: Bearer {ACCESS_TOKEN}",
                "-o", audio_path,
                audio_url
            ]

            # Run the curl command
            subprocess.run(curl_command, check=True)
            print(f"Downloaded: {audio_path}")
import requests
import os
import json
from pathlib import Path

def load_map_file(map_file_path):
    if os.path.exists(map_file_path):
        with open(map_file_path, "r") as map_file:
            return json.load(map_file)
    return {}

def get_activity_history():
    url = 'https://xbl.io/api/v2/activity/history'
    with open('secret_key', 'r') as file:
        api_key = file.read().strip()

    headers = {
        'accept': '*/*',
        'x-authorization': api_key
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('numItems', 0) > 0:
            activity_info = []
            for item in data.get('activityItems', []):
                if item.get('activityItemType') == 'GameDVR':
                    activity_info.append({
                        'clipId': item.get('clipId'),
                        'downloadUri': item.get('downloadUri')
                    })
                elif item.get('activityItemType') == 'Screenshot':
                    activity_info.append({
                        'screenshotId': item.get('screenshotId'),
                        'screenshotUri': item.get('screenshotUri')
                    })
            return activity_info
        else:
            print("No activity items found.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

def download_media(activity_history, map_file_path):
    download_folder = Path("/mnt/ebs/downloaded_media/")
    download_folder.mkdir(exist_ok=True)

    # Load the existing map to check for already processed files
    mapping = load_map_file(map_file_path)

    for item in activity_history:
        if 'clipId' in item:
            file_id = item['clipId']
            url = item['downloadUri']
            file_extension = '.mp4'
        elif 'screenshotId' in item:
            file_id = item['screenshotId']
            url = item['screenshotUri']
            file_extension = '.png'
        else:
            continue

        # Skip downloading if the file is already processed in the map
        if file_id + file_extension in mapping:
            print(f"File {file_id}{file_extension} already processed, skipping download.")
            continue

        file_name = f"{file_id}{file_extension}"
        file_path = download_folder / file_name

        if not file_path.exists():
            print(f"Downloading {file_name}...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded {file_name}")
            else:
                print(f"Failed to download {file_name}")
        else:
            print(f"{file_name} already exists, skipping download")

# Usage
activity_history = get_activity_history()
if activity_history:
    map_file_path = "video_map.json"
    download_media(activity_history, map_file_path)
    
    # Import and run the convertFiles script
    import convertFiles
    
    # Define the directories
    originals_dir = "/mnt/ebs/downloaded_media/"
    converted_dir = "/mnt/ebs/streaming_files/"
    thumbnail_dir = "/mnt/ebs/thumbnails/"
    
    # Process and convert videos, generate thumbnails
    convertFiles.process_videos(originals_dir, converted_dir, thumbnail_dir, map_file_path)
else:
    print("No activity history available for download")

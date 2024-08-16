import requests

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


import os
from pathlib import Path

def download_media(activity_history):
    download_folder = Path("downloaded_media")
    download_folder.mkdir(exist_ok=True)

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
    download_media(activity_history)
else:
    print("No activity history available for download")

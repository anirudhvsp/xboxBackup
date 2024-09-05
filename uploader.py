import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Path to your client secrets file downloaded from Google Developer Console
CLIENT_SECRETS_FILE = "client_secret.json"

# OAuth 2.0 Scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# YouTube API service name and version
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

def get_authenticated_service():
    credentials = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            credentials = Credentials.from_authorized_user_info(json.load(token), SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())
    
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def upload_video(youtube, video_file):
    request_body = {
        "snippet": {
            "title": os.path.splitext(os.path.basename(video_file))[0],
            "description": "Uploaded by script",
            "tags": ["scripted upload", "python"],
            "categoryId": "22"  # You can change this to a different category
        },
        "status": {
            "privacyStatus": "unlisted"  # Make video unlisted
        }
    }
    
    media_file = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    print(f"Upload Complete! Video ID: {response['id']}")
    return f"https://www.youtube.com/watch?v={response['id']}"

def main():
    youtube = get_authenticated_service()
    video_folder = 'downloaded_media'
    output_file = 'uploaded_videos.txt'
    
    with open(output_file, 'w') as file:
        for video in os.listdir(video_folder):
            if video.endswith('.mp4'):  # Adjust for other video formats if needed
                video_path = os.path.join(video_folder, video)
                try:
                    video_url = upload_video(youtube, video_path)
                    file.write(f"{video_url}\n")
                except HttpError as e:
                    print(f"An HTTP error occurred: {e.resp.status} - {e.content}")

if __name__ == "__main__":
    main()

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

def load_map_file(map_file_path):
    if os.path.exists(map_file_path):
        with open(map_file_path, "r") as map_file:
            return json.load(map_file)
    return {}

def save_map_file(map_file_path, mapping):
    with open(map_file_path, "w") as map_file:
        json.dump(mapping, map_file, indent=4)

def convert_to_adaptive_hls(input_file, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    ffmpeg_command = [
        "ffmpeg", "-i", input_file,
        # (ffmpeg command remains the same as before) ...
    ]
    
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Conversion complete: {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")

def generate_thumbnail(input_file, output_dir, thumbnail_name):
    thumbnail_path = os.path.join(output_dir, f"{thumbnail_name}.jpg")
    if not os.path.exists(thumbnail_path):
        print(f"Generating thumbnail for {input_file}...")
        ffmpeg_command = [
            "ffmpeg", "-i", input_file,
            "-ss", "00:00:01",
            "-vframes", "1",
            "-vf", "scale=320:-1",
            thumbnail_path
        ]
        try:
            subprocess.run(ffmpeg_command, check=True)
            print(f"Thumbnail generated: {thumbnail_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating thumbnail: {e}")
    else:
        print(f"Thumbnail already exists: {thumbnail_path}, skipping generation.")

def get_creation_date(file_path):
    return datetime.fromtimestamp(os.path.getctime(file_path))

def process_single_video(input_file, output_dir, thumbnail_dir, new_folder_name, mapping, map_file_path):
    output_folder = os.path.join(output_dir, new_folder_name)
    thumbnail_name = new_folder_name
    input_file_name_cut = input_file.replace("downloaded_media/","")
    
    if input_file_name_cut in mapping:
        print(f"Video {input_file_name_cut} already processed, skipping.")
        return
    
    if not os.path.exists(os.path.join(output_folder, "stream_0", "playlist.m3u8")):
        print(f"Converting video {input_file}...")
        convert_to_adaptive_hls(input_file, output_folder)
    else:
        print(f"Converted version already exists for {input_file}, skipping conversion.")
    
    generate_thumbnail(input_file, thumbnail_dir, thumbnail_name)

    mapping[input_file_name_cut] = new_folder_name
    save_map_file(map_file_path, mapping)

    # Delete the original file after processing
    if os.path.exists(input_file):
        os.remove(input_file)
        print(f"Deleted original file: {input_file}")

def process_videos(input_dir, output_dir, thumbnail_dir, map_file_path):
    # Load the existing map
    mapping = load_map_file(map_file_path)
    
    video_files = [f for f in os.listdir(input_dir) if f.endswith(('.mp4', '.mov', '.mkv'))]
    video_files.sort(key=lambda x: os.path.getctime(os.path.join(input_dir, x)))
    
    date_counts = {}
    
    for video_file in video_files:
        input_file = os.path.join(input_dir, video_file)
        creation_date = get_creation_date(input_file)
        date_str = creation_date.strftime("%Y%m%d")
        
        if date_str not in date_counts:
            date_counts[date_str] = 1
        else:
            date_counts[date_str] += 1
        
        new_folder_name = f"{date_str}_{date_counts[date_str]:03d}"
        
        # Process each video one by one
        process_single_video(input_file, output_dir, thumbnail_dir, new_folder_name, mapping, map_file_path)

if __name__ == "__main__":
    originals_dir = "/mnt/ebs/downloaded_media/"
    converted_dir = "/mnt/ebs/streaming_files/"
    thumbnail_dir = "/mnt/ebs/thumbnails/"
    map_file_path = "video_map.json"

    Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)
    Path(converted_dir).mkdir(parents=True, exist_ok=True)

    process_videos(originals_dir, converted_dir, thumbnail_dir, map_file_path)

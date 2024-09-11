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
        "-filter_complex", "[0:v]split=4[v1][v2][v3][v4]; [v1]scale=w=1280:h=720[v1out]; [v2]scale=w=854:h=480[v2out]; [v3]scale=w=640:h=360[v3out]; [v4]scale=w=426:h=240[v4out]",
        "-map", "[v1out]", "-c:v:0", "libx264", "-preset", "veryfast", "-b:v:0", "2000k", "-maxrate:v:0", "2200k", "-bufsize:v:0", "3000k", "-g", "60",
        "-map", "[v2out]", "-c:v:1", "libx264", "-preset", "veryfast", "-b:v:1", "1000k", "-maxrate:v:1", "1100k", "-bufsize:v:1", "1500k", "-g", "60",
        "-map", "[v3out]", "-c:v:2", "libx264", "-preset", "veryfast", "-b:v:2", "700k", "-maxrate:v:2", "800k", "-bufsize:v:2", "1000k", "-g", "60",
        "-map", "[v4out]", "-c:v:3", "libx264", "-preset", "veryfast", "-b:v:3", "400k", "-maxrate:v:3", "500k", "-bufsize:v:3", "700k", "-g", "60",
        "-map", "a:0", "-c:a", "aac", "-b:a:0", "128k", "-ac", "2",
        "-map", "a:0", "-c:a", "aac", "-b:a:1", "96k", "-ac", "2",
        "-map", "a:0", "-c:a", "aac", "-b:a:2", "64k", "-ac", "2",
        "-map", "a:0", "-c:a", "aac", "-b:a:3", "48k", "-ac", "2",
        "-f", "hls", "-hls_time", "6", "-hls_playlist_type", "vod", "-hls_flags", "independent_segments",
        "-hls_segment_type", "mpegts", "-hls_segment_filename", f"{output_dir}/stream_%v/data%03d.ts",
        "-master_pl_name", "master.m3u8", "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2 v:3,a:3",
        f"{output_dir}/stream_%v/playlist.m3u8"
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
        print(f"Converted version already exists for {input_file}, checking for higher quality stream...")
        if not os.path.exists(os.path.join(output_folder, "stream_3", "playlist.m3u8")):
            print(f"Adding higher quality stream for {input_file}...")
            convert_to_adaptive_hls(input_file, output_folder)
        else:
            print(f"Higher quality stream already exists for {input_file}, skipping conversion.")
    
    generate_thumbnail(input_file, thumbnail_dir, thumbnail_name)

    mapping[input_file_name_cut] = new_folder_name
    save_map_file(map_file_path, mapping)

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
    originals_dir = "downloaded_media/"
    converted_dir = "streaming_files/"
    thumbnail_dir = "thumbnails/"
    map_file_path = "video_map.json"

    Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)
    Path(converted_dir).mkdir(parents=True, exist_ok=True)

    process_videos(originals_dir, converted_dir, thumbnail_dir, map_file_path)

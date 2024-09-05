import os
import subprocess
from pathlib import Path

def convert_to_hls(input_file, output_dir, bitrate="3000k", segment_time=4):
    # Create the output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Define the output paths
    output_file = os.path.join(output_dir, 'stream.m3u8')

    # Check if the conversion has already been done
    if not os.path.exists(output_file):
        print(f"Converting {input_file} to HLS format...")
        
        # Run the FFmpeg command to generate HLS segments
        ffmpeg_command = [
            "ffmpeg", "-i", input_file,
            "-b:v", bitrate,
            "-hls_time", str(segment_time),
            "-hls_list_size", "0",
            "-hls_segment_filename", os.path.join(output_dir, "segment_%03d.ts"),
            "-f", "hls", output_file
        ]
        
        try:
            subprocess.run(ffmpeg_command, check=True)
            print(f"Conversion complete: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error during conversion: {e}")
    else:
        print(f"HLS version already exists for {input_file}, skipping conversion.")

def generate_thumbnail(input_file, output_dir):
    thumbnail_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_file))[0]}.jpg")
    if not os.path.exists(thumbnail_path):
        print(f"Generating thumbnail for {input_file}...")
        ffmpeg_command = [
            "ffmpeg", "-i", input_file,
            "-ss", "00:00:01",  # Take screenshot at 1 second
            "-vframes", "1",
            "-vf", "scale=320:-1",  # Scale to 320px width, maintain aspect ratio
            thumbnail_path
        ]
        try:
            subprocess.run(ffmpeg_command, check=True)
            print(f"Thumbnail generated: {thumbnail_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating thumbnail: {e}")
    else:
        print(f"Thumbnail already exists for {input_file}, skipping generation.")

def process_videos(input_dir, output_dir, thumbnail_dir):
    for video_file in os.listdir(input_dir):
        if video_file.endswith(('.mp4', '.mov', '.mkv')):  # add more formats as needed
            input_file = os.path.join(input_dir, video_file)
            base_name = os.path.splitext(video_file)[0]
            
            # Check for highQuality version
            high_quality_dir = os.path.join(output_dir, base_name, "highQuality")
            if not os.path.exists(os.path.join(high_quality_dir, "stream.m3u8")):
                # Convert the video to HLS with higher bitrate
                convert_to_hls(input_file, high_quality_dir, bitrate="3000k", segment_time=4)
            else:
                print(f"High quality version already exists for {video_file}, skipping conversion.")

            # Check for lowQuality version
            low_quality_dir = os.path.join(output_dir, base_name, "lowQuality")
            if not os.path.exists(os.path.join(low_quality_dir, "stream.m3u8")):
                # Convert the video to HLS with lower bitrate
                convert_to_hls(input_file, low_quality_dir, bitrate="800k", segment_time=4)
            else:
                print(f"Low quality version already exists for {video_file}, skipping conversion.")
            
            # Generate thumbnail
            generate_thumbnail(input_file, thumbnail_dir)

if __name__ == "__main__":
    # Define the directories
    originals_dir = "downloaded_media/"
    converted_dir = "streaming_files/"
    thumbnail_dir = "thumbnails/"

    # Create thumbnail directory if it doesn't exist
    Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)

    # Process and convert videos, generate thumbnails
    process_videos(originals_dir, converted_dir, thumbnail_dir)

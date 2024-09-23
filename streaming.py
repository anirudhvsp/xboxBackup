import os
from flask import Flask, render_template, send_from_directory, send_file, request, make_response
from datetime import datetime
from PIL import Image
from io import BytesIO
import m3u8
from werkzeug.utils import safe_join
from flask import jsonify
import itertools
import random

app = Flask(__name__)

STREAMING_DIR = "/mnt/ebs/streaming_files"
THUMBNAIL_DIR = "/mnt/ebs/thumbnails"
DOWNLOADED_MEDIA_DIR = "/mnt/ebs/downloaded_media"

def get_creation_date(file_path):
    return datetime.fromtimestamp(os.path.getctime(file_path))

def get_video_duration(folder_path):
    m3u8_file = os.path.join(folder_path, 'master.m3u8')
    master_playlist = m3u8.load(m3u8_file)
    
    if master_playlist.playlists:
        # Get the first quality playlist
        quality_playlist_uri = master_playlist.playlists[0].uri
        quality_playlist_path = os.path.join(folder_path, quality_playlist_uri)
        quality_playlist = m3u8.load(quality_playlist_path)
        
        total_duration = 0
        for segment in quality_playlist.segments:
            total_duration += segment.duration
        
        return int(total_duration)
    else:
        return 0  # Return 0 if no quality playlists are found

@app.route('/home')
def index():
    return render_template('index.html')  # Initial load without media

@app.route('/media_page/<int:page>')
def media_page(page):
    all_images = []
    all_videos = []

    # Get videos and sort them by creation date
    for item in os.listdir(STREAMING_DIR):
        if os.path.isdir(os.path.join(STREAMING_DIR, item)) and not item.startswith("test"):
            m3u8_file = os.path.join(STREAMING_DIR, item, 'master.m3u8')
            if not os.path.exists(m3u8_file):
                continue  # Skip this video if master.m3u8 doesn't exist

            thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{item}.jpg")
            if not os.path.exists(thumbnail_path):
                thumbnail_path = os.path.join(THUMBNAIL_DIR, "thumbnail_not_available.jpg")
            duration = get_video_duration(os.path.join(STREAMING_DIR, item))
            duration_formatted = f"{duration // 60:02d}:{duration % 60:02d}"
            all_videos.append({
                'name': item,
                'thumbnail': f"/thumbnails/{os.path.basename(thumbnail_path)}",
                'type': 'stream',
                'creation_date': get_creation_date(os.path.join(STREAMING_DIR, item)),
                'duration' : duration_formatted
            })

    # Get images and sort them by creation date
    for file in os.listdir(DOWNLOADED_MEDIA_DIR):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            all_images.append({
                'name': file,
                'thumbnail': f"/home/compressed_thumbnail/{file}",
                'type': 'image',
                'creation_date': get_creation_date(os.path.join(DOWNLOADED_MEDIA_DIR, file))
            })

    # Sort images and videos by creation date
    all_images.sort(key=lambda x: x['creation_date'], reverse=True)
    all_videos.sort(key=lambda x: x['creation_date'], reverse=True)

    # Pagination logic (unchanged)
    per_page = 24
    start = (page - 1) * per_page
    end = page * per_page

    # Limit to 5-10 images per page
    max_images = min(10, len(all_images))
    displayed_images = all_images[:max_images]

    # Scatter images randomly throughout the list of videos
    scattered_media = all_videos[:]  # Start with all videos

    # Randomly insert images into scattered_media
    for image in displayed_images:
        position = random.randint(0, len(scattered_media))  # Random position in the videos list
        scattered_media.insert(position, image)

    # Select only the items for the current page
    media_page = scattered_media[start:end]

    # Ensure the total media is always paginated correctly
    total_media = len(scattered_media)
    total_pages = (total_media - 1) // per_page + 1

    html_content = render_template('media_page.html', media=media_page, page=page, total_pages=total_pages)
    return html_content
# @app.route('/thumbnails/<path:filename>')
# def serve_thumbnail(filename):
#     return send_from_directory(THUMBNAIL_DIR, filename)

@app.route('/stream/<video_name>')
def stream(video_name):
    if request.headers.get('HX-Request'):
        return render_template('stream.html', video_name=video_name)
    else:
        response = make_response(render_template('stream.html', video_name=video_name))
        response.headers['X-Reset-Body-Padding'] = 'true'
        return response

# @app.route('/static/<video_name>/<path:filename>')
# def video_files(video_name, filename):
#     # Serve the .m3u8 and .ts files
#     return send_from_directory(os.path.join(STREAMING_DIR, video_name), filename)

# Add a new route to serve files from downloaded_media
@app.route('/downloaded_media/<path:filename>')
def serve_downloaded_media(filename):
    safe_path = safe_join(DOWNLOADED_MEDIA_DIR, filename)
    if safe_path and os.path.exists(safe_path):
        return send_from_directory(DOWNLOADED_MEDIA_DIR, filename)
    return "File not found", 404

# # Modify the existing download_video function to handle both videos and images
# @app.route('/download/<media_name>')
# def download_media(media_name):
#     media_path = os.path.join(DOWNLOADED_MEDIA_DIR, media_name)
#     if not os.path.exists(media_path):
#         media_path += '.mp4'  # Try adding .mp4 extension for videos
    
#     if os.path.exists(media_path):
#         return send_file(media_path, as_attachment=True)
#     else:
#         return "Media not found", 404

@app.route('/image/<path:filename>')
def serve_image(filename):
    # Serve the image from the 'downloaded_media' directory
    return send_from_directory(DOWNLOADED_MEDIA_DIR, filename)



@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Add this import at the top of the file if not already present
import os

# Add this new route after the existing routes
@app.route('/test/<folder_name>')
def test_adaptive_streaming(folder_name):

    base_path = os.path.join(STREAMING_DIR, folder_name)
    master_playlist = os.path.join(base_path, 'master.m3u8')

    if not os.path.exists(master_playlist):
        return "Master playlist not found", 404

    return render_template('test_adaptive.html', folder_name=folder_name)

@app.route('/test/<folder_name>/<path:filename>')
def serve_test_files(folder_name, filename):
    return send_from_directory(os.path.join(STREAMING_DIR, folder_name), filename)

import json

def reverse_dict(my_dict):
    # Create a reverse dictionary with values as keys and keys as values
    return {v: k for k, v in my_dict.items()}


# Load video.json mapping
with open('video_map.json') as f:
    video_mapping = json.load(f)
    video_mapping = reverse_dict(video_mapping)



@app.route('/home/download/<video_name>')
def download_media(video_name):
    # Look up the original video file from the JSON mapping
    original_file = video_mapping.get(video_name)
    print(original_file)
    if not original_file:
        return "Original media file not found", 404

    # Construct the path to the original file
    media_path = os.path.join(DOWNLOADED_MEDIA_DIR, original_file)

    if os.path.exists(media_path):
        return send_file(media_path, as_attachment=True)
    else:
        return "Media not found", 404


@app.route('/home/compressed_thumbnail/<path:filename>')
def compressed_thumbnail(filename):
    file_path = os.path.join(DOWNLOADED_MEDIA_DIR, filename)
    if not os.path.exists(file_path):
        return "Image not found", 404

    with Image.open(file_path) as img:
        img.thumbnail((320, 320))  # Resize to a maximum of 320x320
        if img.mode in ('RGBA', 'LA'):
            # Convert RGBA or LA images to RGB
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = background
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)

    return send_file(output, mimetype='image/jpeg')

@app.after_request
def hide_headers(response):
    response.headers['Server'] = ''
    response.headers.pop('X-Powered-By', None)
    return response



@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

def get_next_video(current_video):
    all_videos = [item for item in os.listdir(STREAMING_DIR) if os.path.isdir(os.path.join(STREAMING_DIR, item)) and not item.startswith("test")]
    current_index = all_videos.index(current_video)
    next_index = (current_index + 1) % len(all_videos)
    return all_videos[next_index]

def get_previous_video(current_video):
    all_videos = [item for item in os.listdir(STREAMING_DIR) if os.path.isdir(os.path.join(STREAMING_DIR, item)) and not item.startswith("test")]
    current_index = all_videos.index(current_video)
    previous_index = (current_index - 1) % len(all_videos)
    return all_videos[previous_index]

def get_video_info(video_id):
    video_path = os.path.join(STREAMING_DIR, video_id)
    if os.path.isdir(video_path):
        thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{video_id}.jpg")
        if not os.path.exists(thumbnail_path):
            thumbnail_path = os.path.join(THUMBNAIL_DIR, "thumbnail_not_available.jpg")
        duration = get_video_duration(video_path)
        duration_formatted = f"{duration // 60:02d}:{duration % 60:02d}"
        return {
            'id': video_id,
            'name': video_id,
            'thumbnail': f"/thumbnails/{os.path.basename(thumbnail_path)}",
            'type': 'stream',
            'creation_date': get_creation_date(video_path),
            'duration': duration_formatted
        }
    return None

@app.route('/video_component/<video_id>')
def video_component(video_id):
    video_info = get_video_info(video_id)
    if video_info:
        return render_template('video_component.html', video=video_info)
    return "Video not found", 404

@app.route('/xbox_stream/<video_id>')
def xbox_stream(video_id):
    prev_video = get_previous_video(video_id)
    next_video = get_next_video(video_id)
    video_info = get_video_info(video_id)  # Assuming you want to pass the video info

    return render_template('xbox_stream.html', 
                           video_name=video_id, 
                           prev_video_id=prev_video, 
                           next_video_id=next_video, 
                           video=video_info)
@app.route('/xbox_stream/next/<current_video_id>')
def xbox_next_video(current_video_id):
    next_video = get_next_video(current_video_id)
    return jsonify(next_video)

@app.route('/xbox_stream/previous/<current_video_id>')
def xbox_previous_video(current_video_id):
    previous_video = get_previous_video(current_video_id)
    return jsonify(previous_video)







@app.route('/brainrot/<video_name>')
def tiktok_stream(video_name):
    prev_video = get_previous_video(video_name)
    next_video = get_next_video(video_name)
    return render_template('tiktok_stream.html', video_name=video_name, prev_video=prev_video, next_video=next_video)

@app.route('/brainrot/next/<current_video>')
def next_tiktok_video(current_video):
    # Logic to get the next video
    next_video = get_next_video(current_video)
    return jsonify({'next_video': next_video})

@app.route('/brainrot/previous/<current_video>')
def previous_tiktok_video(current_video):
    previous_video = get_previous_video(current_video)
    return jsonify({'previous_video': previous_video})

if __name__ == '__main__':
    app.run(debug=False)






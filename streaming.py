import os
from flask import Flask, render_template, send_from_directory, send_file, request
from datetime import datetime
from PIL import Image
from io import BytesIO

app = Flask(__name__)

STREAMING_DIR = "/mnt/ebs/streaming_files"
THUMBNAIL_DIR = "/mnt/ebs/thumbnails"
DOWNLOADED_MEDIA_DIR = "/mnt/ebs/downloaded_media"

def get_creation_date(file_path):
    return datetime.fromtimestamp(os.path.getctime(file_path))


@app.route('/home')
def index():
    return render_template('index.html')  # Initial load without media

@app.route('/media_page/<int:page>')
def media_page(page):
    all_media = []

    # Get videos and images, and sort them by creation date
    for item in os.listdir(STREAMING_DIR):
        if os.path.isdir(os.path.join(STREAMING_DIR, item)) and not item.startswith("test"):
            thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{item}.jpg")
            if not os.path.exists(thumbnail_path):
                thumbnail_path = os.path.join(THUMBNAIL_DIR, "thumbnail_not_available.jpg")
            all_media.append({
                'name': item,
                'thumbnail': f"/thumbnails/{os.path.basename(thumbnail_path)}",
                'type': 'stream',
                'creation_date': get_creation_date(os.path.join(STREAMING_DIR, item))
            })

    for file in os.listdir(DOWNLOADED_MEDIA_DIR):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            all_media.append({
                'name': file,
                'thumbnail': f"/home/compressed_thumbnail/{file}",
                'type': 'image',
                'creation_date': get_creation_date(os.path.join(DOWNLOADED_MEDIA_DIR, file))
            })

    # Sort all media by creation date
    all_media.sort(key=lambda x: x['creation_date'], reverse=True)

    # Pagination logic (unchanged)
    per_page = 18
    start = (page - 1) * per_page
    end = page * per_page
    total_media = len(all_media)
    total_pages = (total_media - 1) // per_page + 1

    media_page = all_media[start:end]

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
        return render_template('stream.html', video_name=video_name), 200, {'HX-Push': f'/stream/{video_name}'}

# @app.route('/static/<video_name>/<path:filename>')
# def video_files(video_name, filename):
#     # Serve the .m3u8 and .ts files
#     return send_from_directory(os.path.join(STREAMING_DIR, video_name), filename)

# Add a new route to serve files from downloaded_media
@app.route('/downloaded_media/<path:filename>')
def serve_downloaded_media(filename):
    return send_from_directory(DOWNLOADED_MEDIA_DIR, filename)

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




if __name__ == '__main__':
    app.run(debug=True)






import os
from flask import Flask, render_template, send_from_directory, send_file

app = Flask(__name__)

STREAMING_DIR = "streaming_files"
THUMBNAIL_DIR = "thumbnails"
DOWNLOADED_MEDIA_DIR = "downloaded_media"

@app.route('/')
def index():
    return render_template('index.html')  # Initial load without media

@app.route('/media_page/<int:page>')
def media_page(page):
    videos = []
    images = []
    
    # Get videos and images as before
    for video in os.listdir(STREAMING_DIR):
        if os.path.isdir(os.path.join(STREAMING_DIR, video)):
            thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{video}.jpg")
            if not os.path.exists(thumbnail_path):
                video_path = os.path.join(STREAMING_DIR, video, "index.m3u8")
                subprocess.run(['ffmpeg', '-i', video_path, '-ss', '00:00:01', '-vframes', '1', thumbnail_path])
            videos.append({'name': video, 'thumbnail': f"/thumbnails/{video}.jpg", 'type': 'video'})
    
    for file in os.listdir(DOWNLOADED_MEDIA_DIR):
        if file.lower().endswith('.png'):
            images.append({'name': file, 'thumbnail': f"/downloaded_media/{file}", 'type': 'image'})
    
    all_media = videos + images
    all_media.sort(key=lambda x: os.path.getmtime(os.path.join(STREAMING_DIR if x['type'] == 'video' else DOWNLOADED_MEDIA_DIR, x['name'])), reverse=True)

    # Pagination logic for infinite scrolling
    per_page = 10  # Number of media items per scroll page
    start = (page - 1) * per_page
    end = page * per_page
    media_page = all_media[start:end]
    total_media = len(all_media)
    return render_template('media_page.html', media=media_page, current_page=page, total_pages=total_media)

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory(THUMBNAIL_DIR, filename)

@app.route('/stream/<video_name>')
def stream(video_name):
    # Serve the HLS manifest file (.m3u8)
    video_dir = os.path.join(STREAMING_DIR, video_name)
    if not os.path.exists(video_dir):
        return "Video not found", 404
    return render_template('stream.html', video_name=video_name)

@app.route('/youtube/<video_id>')
def youtube(video_id):
    # Use yt-dlp to get the video URL
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        stream_url = info.get('url')
    print(stream_url)
    # Redirect to the stream page with the YouTube stream URL
    return render_template('youtube.html', stream_url=stream_url)

@app.route('/static/<video_name>/<path:filename>')
def video_files(video_name, filename):
    # Serve the .m3u8 and .ts files
    return send_from_directory(os.path.join(STREAMING_DIR, video_name), filename)

# Add a new route to serve files from downloaded_media
@app.route('/downloaded_media/<path:filename>')
def serve_downloaded_media(filename):
    return send_from_directory(DOWNLOADED_MEDIA_DIR, filename)

# Modify the existing download_video function to handle both videos and images
@app.route('/download/<media_name>')
def download_media(media_name):
    media_path = os.path.join(DOWNLOADED_MEDIA_DIR, media_name)
    if not os.path.exists(media_path):
        media_path += '.mp4'  # Try adding .mp4 extension for videos
    
    if os.path.exists(media_path):
        return send_file(media_path, as_attachment=True)
    else:
        return "Media not found", 404

if __name__ == '__main__':
    app.run(debug=True)

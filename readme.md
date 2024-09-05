# Xbox Media Downloader

This project utilizes the Xbox Live API (xbl.io) and Windows Task Scheduler to automatically download media (game clips and screenshots) from Xbox servers to your local drive or cloud storage. This ensures you have a permanent copy of your media without worrying about Xbox deleting files after a certain period.

## Components

1. `getClips.py`: Python script that interacts with the Xbox Live API to fetch and download media.
2. `runClipDownloader.bat`: Batch script to run the Python script and log its execution.

## Functionality

### getClips.py

- Fetches activity history from the Xbox Live API.
- Identifies game clips and screenshots in the activity feed.
- Downloads new media files to a local folder named "downloaded_media".
- Skips downloading files that already exist locally.

### runClipDownloader.bat

- Executes the Python script (`getClips.py`).
- Logs the execution time and results to a log file (`logfile.log`).
- Captures and reports any errors that occur during execution.

## Setup

1. Ensure Python is installed on your system.
2. Install required Python packages: `requests`
3. Create a file named `secret_key` in the same directory as the scripts and add your Xbox Live API key.
4. Set up a scheduled task in Windows Task Scheduler to run `runClipDownloader.bat` at your desired frequency.

## Usage

Once set up, the system will automatically run according to your scheduled task settings. It will download any new media from your Xbox Live account to your local machine, ensuring you have a backup of all your game clips and screenshots.

This automated process allows you to maintain a local or cloud-based archive of your Xbox media without manual intervention, protecting your memories from potential deletion on Xbox servers.

## Update: Streaming Functionality

This project now includes a web-based streaming interface for viewing your downloaded media.

### New Features:
- Web interface to browse and stream your game clips and screenshots
- Automatic thumbnail generation for video files
- Support for both video streaming and image viewing
- Download option for all media files

### Additional Dependencies:
- Flask: Web framework for Python
- ffmpeg: Required for thumbnail generation and video processing

### Setup for Streaming:
1. Install Flask: `pip install flask`
2. Install ffmpeg: Download and install from [ffmpeg.org](https://ffmpeg.org/)
3. Run `streaming.py` to start the web server
4. Access the interface through your web browser at `http://localhost:5000`

This new functionality allows you to easily view and manage your Xbox media through a user-friendly web interface, enhancing the overall utility of the Xbox Media Downloader.

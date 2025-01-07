import os
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor


# Step 1: Get video URLs from the playlist
def get_video_urls(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # Extract video URLs without downloading
        'skip_download': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        return [(entry['url'], entry['title']) for entry in info['entries']] if 'entries' in info else []


# Step 2: Download a single video
def download_video(video_url, video_title, output_dir):
    # Check if the file already exists
    output_path = os.path.join(output_dir, f"{video_title}.mp4")
    if os.path.exists(output_path):
        print(f"Skipping {video_title} (already downloaded)")
        return

    # yt-dlp options to limit resolution to 1080p
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',  # Limit resolution to 1080p
        'merge_output_format': 'mp4',  # Ensure output is in MP4 format
        'outtmpl': output_path,  # Save with title as filename
        'quiet': False,  # Show progress
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading: {video_title}")
            ydl.download([video_url])
            print(f"Finished downloading: {video_title}")
    except Exception as e:
        print(f"Failed to download {video_title}: {e}")


# Step 3: Download videos in parallel using ThreadPoolExecutor
def download_videos_parallel(video_urls, output_dir, max_parallel_downloads=4):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with ThreadPoolExecutor(max_workers=max_parallel_downloads) as executor:
        futures = [
            executor.submit(download_video, url, title, output_dir)
            for url, title in video_urls
        ]
        for future in futures:
            future.result()  # Wait for all tasks to complete


if __name__ == "__main__":
    PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLLtEq7B9ZIoAdgFWSUVeymH2YKVU-7kNZ"
    DOWNLOADS_FOLDER = "downloads"  # Folder to save downloaded videos

    # Step 1: Get video URLs from the playlist
    print("Fetching video URLs from playlist...")
    video_urls = get_video_urls(PLAYLIST_URL)

    print(f"Found {len(video_urls)} videos in the playlist.")

    # Step 2: Download videos in parallel
    print("Downloading videos...")
    download_videos_parallel(video_urls, DOWNLOADS_FOLDER, max_parallel_downloads=8)

import yt_dlp
import asyncio

async def get_video_info(url: str, cookies_path: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
        'cookies': cookies_path,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def start_download(url: str, format_id: str, outtmpl: str, cookies_path: str, task_id: str):
    ydl_opts = {
        'format': format_id,
        'outtmpl': outtmpl,
        'cookies': cookies_path,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-c', 'copy'],
        'continuedl': True,
        'retries': 10,
        'fragment_retries': 10,
    }

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

    # download مکمل → file serve کر سکتے ہو یا notify
    print(f"Download complete for task {task_id}")
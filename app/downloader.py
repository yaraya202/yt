import yt_dlp
import asyncio

async def get_video_info(url: str, cookies_path: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
        'cookies': cookies_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def start_download(url: str, format_id: str, outtmpl: str, cookies_path: str, task_id: str):
    ydl_opts = {
        'format': format_id,
        'outtmpl': outtmpl,
        'cookies': cookies_path,
        'merge_output_format': 'mp4',           # mp4 میں merge
        'postprocessor_args': ['-c', 'copy'],   # تیز merge (re-encode نہیں)
        'continuedl': True,
        'retries': 10,
        'fragment_retries': 10,
        # GPU accelerate اگر server پر NVIDIA ہو تو
        # 'postprocessor_args': {'merger+ffmpeg': ['-hwaccel', 'cuda', '-c:v', 'copy', '-c:a', 'copy']}
    }

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

    # download مکمل → file serve کر سکتے ہو یا notify
    print(f"Download complete for task {task_id}")
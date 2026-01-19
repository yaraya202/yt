from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import yt_dlp
import os
import asyncio
import uuid
from pathlib import Path
try:
    from .downloader import get_video_info, start_download
except ImportError:
    from downloader import get_video_info, start_download

app = FastAPI(title="YouTube Video + Audio Downloader")
templates = Jinja2Templates(directory="templates")  # templates فولڈر بنا لو

COOKIES_PATH = Path("cookies.txt")
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# اگر cookies.txt نہ ہو تو error
if not COOKIES_PATH.exists():
    raise RuntimeError("cookies.txt file missing! Please create it.")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/get-info")
async def info(url: str = Form(...)):
    try:
        info = await get_video_info(url, str(COOKIES_PATH))
        formats = []
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                label = f"{f.get('height', 'Audio')}p" if f.get('height') else "Audio only"
                if f.get('ext') == 'mp4':
                    label += " (mp4)"
                formats.append({
                    "format_id": f['format_id'],
                    "label": label,
                    "filesize": f.get('filesize') or f.get('filesize_approx'),
                    "ext": f['ext']
                })
        return {"title": info['title'], "formats": formats[:15]}  # top 15 دکھاؤ
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.post("/download")
async def download(url: str = Form(...), format_id: str = Form(...)):
    task_id = str(uuid.uuid4())
    output_path = DOWNLOAD_DIR / f"{task_id}.%(ext)s"

    asyncio.create_task(start_download(url, format_id, str(output_path), str(COOKIES_PATH), task_id))

    return RedirectResponse(f"/progress/{task_id}")

# مزید endpoints: progress check, file serve وغیرہ بنا سکتے ہو
# /progress/{task_id} → status دکھانے کے لیے websocket یا polling
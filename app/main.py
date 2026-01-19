from fastapi import FastAPI, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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
templates = Jinja2Templates(directory="templates")

COOKIES_PATH = Path("cookies.txt")
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Store download status
download_tasks = {}

if not COOKIES_PATH.exists():
    # Create empty cookies.txt if not exists to avoid crash, but warn
    COOKIES_PATH.touch()
    print("Warning: cookies.txt created but is empty. Restricted videos might fail.")

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
                height = f.get('height')
                ext = f.get('ext')
                filesize = f.get('filesize') or f.get('filesize_approx') or 0
                
                label = f"{height}p" if height else "Audio only"
                label += f" ({ext})"
                
                formats.append({
                    "format_id": f['format_id'],
                    "label": label,
                    "filesize": filesize,
                    "ext": ext
                })
        
        # Sort: Video first (high to low), then Audio
        formats.sort(key=lambda x: (0 if "p" in x['label'] else 1, -int(x['label'].split('p')[0]) if "p" in x['label'] else 0))
        
        return {
            "title": info.get('title', 'Unknown Title'),
            "thumbnail": info.get('thumbnail'),
            "duration": info.get('duration'),
            "formats": formats[:20]
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@app.post("/download")
async def download(background_tasks: BackgroundTasks, url: str = Form(...), format_id: str = Form(...)):
    task_id = str(uuid.uuid4())
    # We use a placeholder for extension which yt-dlp will fill
    outtmpl = str(DOWNLOAD_DIR / f"{task_id}.%(ext)s")
    
    download_tasks[task_id] = {"status": "starting", "file_path": None}
    
    background_tasks.add_task(run_download, url, format_id, outtmpl, task_id)
    
    return {"task_id": task_id}

async def run_download(url: str, format_id: str, outtmpl: str, task_id: str):
    try:
        download_tasks[task_id]["status"] = "downloading"
        await start_download(url, format_id, outtmpl, str(COOKIES_PATH), task_id)
        
        # Find the actual file (yt-dlp might have changed extension)
        files = list(DOWNLOAD_DIR.glob(f"{task_id}.*"))
        if files:
            download_tasks[task_id]["status"] = "completed"
            download_tasks[task_id]["file_path"] = str(files[0])
        else:
            download_tasks[task_id]["status"] = "error"
    except Exception as e:
        print(f"Download error: {e}")
        download_tasks[task_id]["status"] = "error"

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in download_tasks:
        return JSONResponse(status_code=404, content={"detail": "Task not found"})
    return download_tasks[task_id]

@app.get("/get-file/{task_id}")
async def get_file(task_id: str):
    if task_id not in download_tasks or download_tasks[task_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="File not ready")
    
    file_path = download_tasks[task_id]["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(file_path, filename=os.path.basename(file_path))

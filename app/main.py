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
            # Include formats that have either video or audio
            # and specifically look for 'audio only' if vcodec is none
            vcodec = f.get('vcodec')
            acodec = f.get('acodec')
            
            if vcodec != 'none' or acodec != 'none':
                height = f.get('height')
                ext = f.get('ext')
                filesize = f.get('filesize') or f.get('filesize_approx') or 0
                
                if vcodec != 'none':
                    label = f"{height}p" if height else "Video"
                else:
                    label = "Audio only"
                
                label += f" ({ext})"
                
                formats.append({
                    "format_id": f['format_id'],
                    "label": label,
                    "filesize": filesize,
                    "ext": ext,
                    "is_audio": vcodec == 'none'
                })
        
        # Sort: Video first (high to low), then Audio
        def sort_key(x):
            if not x['is_audio']:
                # Video formats
                try:
                    h = int(x['label'].split('p')[0])
                except:
                    h = 0
                return (0, -h)
            else:
                # Audio formats
                return (1, 0)

        formats.sort(key=sort_key)
        
        return {
            "title": info.get('title', 'Unknown Title'),
            "thumbnail": info.get('thumbnail'),
            "duration": info.get('duration'),
            "formats": formats[:30] # Increase to show more options
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@app.post("/download")
async def download(background_tasks: BackgroundTasks, url: str = Form(...), format_id: str = Form(...), title: str = Form(...)):
    task_id = str(uuid.uuid4())
    # We use a placeholder for extension which yt-dlp will fill
    outtmpl = str(DOWNLOAD_DIR / f"{task_id}.%(ext)s")
    
    download_tasks[task_id] = {"status": "starting", "file_path": None, "title": title}
    
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
    
    file_info = download_tasks[task_id]
    file_path = file_info["file_path"]
    original_title = file_info["title"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Get extension from the actual file
    ext = Path(file_path).suffix
    # Clean filename: remove special characters
    safe_title = "".join([c for c in original_title if c.isalnum() or c in (' ', '.', '-', '_')]).strip()
    filename = f"{safe_title}{ext}"
    
    return FileResponse(file_path, filename=filename)

# YouTube Video/Audio Downloader

## Overview

A web-based YouTube video and audio downloader built with FastAPI. Users can paste a YouTube URL, view available format options (video quality/audio), and download their preferred format. The application uses yt-dlp for extraction and downloading, with cookie-based authentication to handle age-restricted or region-locked content.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **FastAPI** serves as the web framework, chosen for its async support and automatic API documentation
- **Jinja2** templates render the frontend HTML
- **yt-dlp** handles YouTube video extraction and downloading (successor to youtube-dl with better maintenance)

### Application Structure
```
app/
├── main.py        # FastAPI routes and app initialization
├── downloader.py  # yt-dlp wrapper functions for async operations
└── utils.py       # Helper functions (file size formatting, cleanup)
templates/
└── index.html     # Frontend UI with vanilla JavaScript
downloads/         # Temporary storage for downloaded files
cookies.txt        # YouTube authentication cookies (required)
```

### Key Design Decisions

1. **Async Download Processing**: Downloads run in a thread executor to avoid blocking the async event loop while yt-dlp (synchronous) processes files

2. **Cookie-Based Authentication**: Uses Netscape-format cookies.txt for YouTube authentication, enabling access to restricted content

3. **Format Selection**: Extracts available formats from YouTube and presents top 15 options to users, supporting both video and audio-only downloads

4. **MP4 Output**: Forces merge output to MP4 format with copy codec (no re-encoding) for faster processing

### Incomplete Implementation
The `/download` endpoint in `main.py` is incomplete - needs to be finished to actually trigger downloads and serve files to users.

## External Dependencies

### Python Packages
- **fastapi**: Web framework
- **uvicorn**: ASGI server to run FastAPI
- **yt-dlp**: YouTube video extraction and download
- **python-multipart**: Form data parsing for file uploads
- **jinja2**: HTML templating
- **aiofiles**: Async file operations

### External Services
- **YouTube**: Primary video source (requires valid cookies.txt for authentication)
- **FFmpeg**: Required by yt-dlp for merging video/audio streams (must be installed on system)

### File Dependencies
- **cookies.txt**: Netscape-format cookie file for YouTube authentication - application will crash if missing
- **downloads/**: Directory created automatically for storing downloaded files
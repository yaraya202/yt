# app/utils.py (optional ابھی)
import os
from pathlib import Path

def format_size(bytes_size):
    if bytes_size is None:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"

def cleanup_old_files(directory="downloads", max_age_minutes=60):
    # cron job یا background task کے لیے
    pass
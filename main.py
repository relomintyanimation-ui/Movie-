import os
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import yt_dlp

app = FastAPI()

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/{url:path}")
async def download_video(url: str, background_tasks: BackgroundTasks):
    clean_url = url
    
    # URL theek karne ka logic
    if clean_url.startswith("http:/") and not clean_url.startswith("http://"):
        clean_url = clean_url.replace("http:/", "http://", 1)
    elif clean_url.startswith("https:/") and not clean_url.startswith("https://"):
        clean_url = clean_url.replace("https:/", "https://", 1)
        
    if not clean_url.startswith("http"):
        # Agar user ne sirf 11 character ki YouTube ID daali hai
        if len(clean_url) == 11 and " " not in clean_url:
            clean_url = f"https://www.youtube.com/watch?v={clean_url}"
        else:
            clean_url = "https://" + clean_url

    file_id = str(uuid.uuid4())
    filepath = f"{file_id}.mp4"
    
    # yt-dlp Settings (IPv4 Force Fix ke sath)
    ydl_opts = {
        'outtmpl': filepath,
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'source_address': '0.0.0.0', # Yeh line DNS Network error (Errno -5) ko fix karegi
    }
    
    try:
        # Video Download Start
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            title = info.get('title', 'downloaded_video').replace('/', '_').replace('\\', '_')
            
        background_tasks.add_task(remove_file, filepath)
        
        return FileResponse(
            path=filepath, 
            media_type='video/mp4', 
            filename=f"{title}.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

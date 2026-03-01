import os
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import yt_dlp

app = FastAPI()

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/{url:path}")
async def download_video(url: str, background_tasks: BackgroundTasks):
    clean_url = url
    
    # URL ko theek karne ka logic
    if clean_url.startswith("http:/") and not clean_url.startswith("http://"):
        clean_url = clean_url.replace("http:/", "http://", 1)
    elif clean_url.startswith("https:/") and not clean_url.startswith("https://"):
        clean_url = clean_url.replace("https:/", "https://", 1)
        
    if not clean_url.startswith("http"):
        if len(clean_url) == 11 and " " not in clean_url:
            clean_url = f"https://www.youtube.com/watch?v={clean_url}"
        else:
            clean_url = "https://" + clean_url

    # SMART TRICK: YouTube links ke liye Error bypass karega aur SSYouTube par bhej dega
    if "youtube.com" in clean_url or "youtu.be" in clean_url:
        clean_url = clean_url.replace("youtube.com", "ssyoutube.com").replace("youtu.be/", "ssyoutube.com/watch?v=")
        return RedirectResponse(url=clean_url)

    # Insta, FB, Drive jaise baaki sabhi platforms ke liye Fast Download Code
    file_id = str(uuid.uuid4())
    filepath = f"{file_id}.mp4"
    
    ydl_opts = {
        'outtmpl': filepath,
        'format': 'b',  # Bina merge kiye fast download ke liye
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    
    try:
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

import os
import uuid
import asyncio
import urllib.request
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from contextlib import asynccontextmanager
import yt_dlp

# BACKGROUND TASK: Yeh function har 5 minute mein Render ko jagayega
async def keep_awake():
    while True:
        await asyncio.sleep(300)  # 5 minute (300 second) ka wait
        try:
            # Render automatically apne URL ka pata laga leta hai
            server_url = os.environ.get("RENDER_EXTERNAL_URL")
            if server_url:
                urllib.request.urlopen(f"{server_url}/ping")
                print("Server ne khud ko jaga liya!")
        except Exception as e:
            print(f"Jagane mein error: {e}")

# Server start hote hi jagane wala system chalu
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(keep_awake())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

# HIDDEN ROUTE: Yeh sirf server ko jagane ke kaam aayega
@app.get("/ping")
async def ping():
    return {"status": "awake"}

# MAIN DOWNLOADER: Dashboard hat gaya, direct link daalo aur download karo!
@app.get("/{url:path}")
async def download_video(url: str, background_tasks: BackgroundTasks):
    clean_url = url
    
    # Agar galti se system ping/favicon maange, toh ignore karo
    if clean_url in ["ping", "favicon.ico"]:
        return {"status": "ignored"}

    if clean_url.startswith("http:/") and not clean_url.startswith("http://"):
        clean_url = clean_url.replace("http:/", "http://", 1)
    elif clean_url.startswith("https:/") and not clean_url.startswith("https://"):
        clean_url = clean_url.replace("https:/", "https://", 1)
        
    if not clean_url.startswith("http"):
        if len(clean_url) == 11 and " " not in clean_url:
            clean_url = f"https://www.youtube.com/watch?v={clean_url}"
        else:
            clean_url = "https://" + clean_url

    # SMART TRICK: YouTube links ke liye Error bypass (Redirect)
    if "youtube.com" in clean_url or "youtu.be" in clean_url:
        clean_url = clean_url.replace("youtube.com", "ssyoutube.com").replace("youtu.be/", "ssyoutube.com/watch?v=")
        return RedirectResponse(url=clean_url)

    # Insta, FB, Drive jaise baaki sabhi platforms ke liye Fast Download Code
    file_id = str(uuid.uuid4())
    filepath = f"{file_id}.mp4"
    
    ydl_opts = {
        'outtmpl': filepath,
        'format': 'b',  # Fast speed ke liye
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

# Error bachane wali line (Jab Render server chalaye)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

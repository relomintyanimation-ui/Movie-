import os
import uuid
import asyncio
import urllib.request
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from contextlib import asynccontextmanager
import yt_dlp

# BACKGROUND TASK: Har 5 minute mein Render ko jagayega
async def keep_awake():
    while True:
        await asyncio.sleep(300) 
        try:
            server_url = os.environ.get("RENDER_EXTERNAL_URL")
            if server_url:
                urllib.request.urlopen(f"{server_url}/ping")
                print("Server ne khud ko jaga liya!")
        except Exception as e:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(keep_awake())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

# HIDDEN ROUTE: Server ko jagane ke liye
@app.get("/ping")
async def ping():
    return {"status": "awake"}

@app.get("/{url:path}")
async def download_video(url: str, background_tasks: BackgroundTasks):
    clean_url = url
    
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

    # SECRET TRICK: YouTube links ke liye (Direct MP4 Download, No Dashboard)
    if "youtube.com" in clean_url or "youtu.be" in clean_url:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {"url": clean_url}
        try:
            # Secret API jo bina dashboard ke direct link deti hai
            response = requests.post("https://api.cobalt.tools/api/json", json=data, headers=headers)
            if response.status_code == 200:
                res_json = response.json()
                direct_mp4_url = res_json.get("url")
                if direct_mp4_url:
                    # Seedha MP4 file par redirect (Download turant start hoga)
                    return RedirectResponse(url=direct_mp4_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Direct download extract nahi ho paya. YouTube ne block kiya.")

    # Insta, FB, Drive jaise platforms ke liye Fast Download Code
    file_id = str(uuid.uuid4())
    filepath = f"{file_id}.mp4"
    
    ydl_opts = {
        'outtmpl': filepath,
        'format': 'b',  
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
            
        background_tasks.add_task(remove_file, filepath)
        
        return FileResponse(
            path=filepath, 
            media_type='video/mp4', 
            filename=f"{title}.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

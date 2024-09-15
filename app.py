from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pytubefix import YouTube
import os
import threading
import time


app = FastAPI()
 
# Configurer CORS pour autoriser toutes les origines (à utiliser avec prudence en production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autoriser toutes les origines
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser toutes les méthodes HTTP
    allow_headers=["*"],  # Autoriser tous les en-têtes
)

# Dossier où les vidéos seront téléchargées
DOWNLOAD_FOLDER = 'public/videos'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Fonction pour supprimer une vidéo après 1 heure
def delete_file_after_timeout(file_path: str, timeout: int = 3600):
    time.sleep(timeout)  # Attendre pendant 1 heure (3600 secondes)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File {file_path} has been deleted")

# class DownloadRequest(BaseModel):
#     url: str

@app.get('/')
async def hello_world():
    return {'message': 'Hello, little World!'}

class Item(BaseModel):
    url: str

@app.post('/download')
async def download_video(item: Item, request: Request):
    domain = request.base_url
    print('debug domain', domain)
    path = request.url.path
    try:
        youtube_url = item.url
        print('debug', item)
        
        # Télécharger la vidéo avec pytube
        yt = YouTube(youtube_url)
        print('yt.streams', yt.streams)
        video = yt.streams.get_highest_resolution()
        print('video', video)
        file_path = video.download(DOWNLOAD_FOLDER)
        
        # Obtenir le nom du fichier
        file_name = os.path.basename(file_path)
        print('debug', file_name)
        
        # Lancer un thread pour supprimer la vidéo après 1 heure
        thread = threading.Thread(target=delete_file_after_timeout, args=(file_path,))
        thread.start()
        print('debug', thread)
        
        # Construire l'URL publique
        public_url = f"{request.base_url}videos/{file_name}"
        print('debug', request.base_url)
        
        return JSONResponse(content={"message": "Download successful", "url": public_url})
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/videos/{filename}')
async def serve_video(filename: str):
    print('filename', filename)
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")

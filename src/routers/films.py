import os, re, asyncio, time, cloudinary
# import httpx
from fastapi import APIRouter, UploadFile, File, BackgroundTasks

from ..utils.image_utils import *
from ..utils.film_title_extractor import extract_film_title_llm
from typing import List
from ..services.tmdb_service import TMDBService
from ..services.llm_service import GeminiFilmTitleExtractor
from ..config import settings
import yt_dlp

router = APIRouter()
tmdb_service = TMDBService()

MAX_CONCURRENT = 100
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

gemini = GeminiFilmTitleExtractor(api_key=settings.gemini_api_key)

@router.post("/analyze")
async def analyze_image(
    files: List[UploadFile] = File(...), 
    background_tasks: BackgroundTasks = None
    ):
    async with semaphore:
        uploaded_urls = []
        start_time = time.time()
        #read file before passing to cloudinary
        for file in files:
            content = await file.read()
            
            #send to cloudinary
            result = cloudinary.uploader.upload(content, folder="film_uploads", resource_type="image")
            
            #get the cloudinary url back
            uploaded_urls.append(result["secure_url"])

        
        print("Uploaded image URLs:", uploaded_urls)

        # ✅ Use LLM to identify the film/show
        film_title = await gemini.extract_film_title(uploaded_urls)
        # print("Extracted film title:", film_title)

        #send to tmdb 
        tmdb_results = await tmdb_service.search_movie(film_title)
        
        if not tmdb_results:
            tmdb_results = await tmdb_service.search_tvshow(film_title)
        
        print("tmdb_results", tmdb_results)
        
        if background_tasks:
            for url in uploaded_urls:
                public_id = "film_uploads/" + url.split("/")[-1].split(".")[0]
                print("Deleting upload with public_id:", public_id)
                background_tasks.add_task(delete_upload, public_id)

        # await delete_upload(result["public_id"])
        end_time = time.time()

        elapsed_time = round(end_time - start_time, 3)
        print(f"\n\n Total time: {elapsed_time} seconds")
        
        # parse and map the film data 
        if tmdb_results:
            film = tmdb_service.tmdb_to_film(tmdb_results[0])
            return film.model_dump()
        return {"error": "No results from the Movie database"}
      
  
@router.post("/analyze_social")
async def analyze_social_media(url: str):
    async with semaphore:
        start_time = time.time()
        # Extract media URLs with yt-dlp
        ydl_opts = {"skip_download": True, "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        media_urls = []
        if 'url' in info:
            media_urls.append(info['url'])
        if 'thumbnails' in info:
            media_urls.extend([t['url'] for t in info['thumbnails']])
        
        # Extract only image URLs
        # image_urls = [url for url in media_urls if any(ext in url for ext in [".jpg", ".jpeg", ".png"])]
        

        frames_and_images = await extract_images_from_media(media_urls)
        # print("frames_and_images", frames_and_images)

        # Pass media URLs to GeminiFilmTitleExtractor
        film_title = await gemini.extract_film_title(frames_and_images)
        print("Extracted film title:", film_title)
        
        #send to tmdb 
        tmdb_results = await tmdb_service.search_movie(film_title)
        
        if not tmdb_results:
            tmdb_results = await tmdb_service.search_tvshow(film_title)
        
        print("tmdb_results", tmdb_results)

        end_time = time.time()

        elapsed_time = round(end_time - start_time, 3)
        print(f"\n\n Total time: {elapsed_time} seconds")
        
        # parse and map the film data 
        if tmdb_results:
            film = tmdb_service.tmdb_to_film(tmdb_results[0])
            return film.model_dump()
        return {"error": "No results from the Movie database"}
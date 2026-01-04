import os, re, asyncio, time, cloudinary
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, status
from ..utils.image_utils import *
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
    files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None
):
    async with semaphore:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided"
            )

        uploaded_urls = []
        start_time = time.time()

        try:
            for file in files:
                content = await file.read()
                resource_type = (
                    "video" if file.content_type.startswith("video/") else "image"
                )

                result = cloudinary.uploader.upload(
                    content, folder="film_uploads", resource_type=resource_type
                )
                uploaded_urls.append(result["secure_url"])

                if background_tasks:
                    background_tasks.add_task(
                        delete_upload, result["public_id"], resource_type
                    )

            film_title = await gemini.extract_film_title(uploaded_urls)
            if not film_title:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="AI could not identify a film from the provided media",
                )

            tmdb_results = await tmdb_service.search_movie(
                film_title
            ) or await tmdb_service.search_tvshow(film_title)

            if not tmdb_results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No matches found in TMDB for '{film_title}'",
                )

            end_time = time.time()
            print(f"\n\n Total time: {round(end_time - start_time, 3)} seconds")

            film = tmdb_service.tmdb_to_film(tmdb_results[0])
            return film.model_dump()

        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )


@router.post("/analyze_social")
async def analyze_social_media(url: str):
    async with semaphore:
        start_time = time.time()

        try:
            ydl_opts = {"skip_download": True, "quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            media_urls = []
            if "url" in info:
                media_urls.append(info["url"])
            if "thumbnails" in info:
                media_urls.extend(t["url"] for t in info["thumbnails"])

            if not media_urls:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to extract media content from the provided URL",
                )

            film_title = await gemini.extract_film_title(media_urls)
            if not film_title:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="AI could not identify a film from the social media content",
                )

            tmdb_results = await tmdb_service.search_movie(
                film_title
            ) or await tmdb_service.search_tvshow(film_title)

            if not tmdb_results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No matches found in TMDB for '{film_title}'",
                )

            end_time = time.time()
            print(f"\n\n Total time: {round(end_time - start_time, 3)} seconds")

            film = tmdb_service.tmdb_to_film(tmdb_results[0])
            return film.model_dump()

        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

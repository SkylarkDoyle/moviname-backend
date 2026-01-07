import asyncio
import base64
import aiohttp
import functools
import json
from typing import List, Optional, Dict
from google import genai
from google.genai.types import Content, Part, GenerateContentConfig
from ..config import settings

# -----------------------------
# Gemini Client Wrapper (Async)
# -----------------------------


class GeminiFilmTitleExtractor:
    def __init__(self, api_key: str, model: str = settings.gemini_model):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.cache: Dict[str, str] = {}

    # -----------------------------
    # Public Method
    # -----------------------------
    async def extract_film_title(self, image_urls: List[str]) -> str:
        """Main entry: extract film title using Gemini Multimodal."""

        cache_key = "|".join(image_urls)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Build content with robust system prompt
        system_instruction = (
            "You are a film expert AI. Your task is to identify the official title of the movie or TV show "
            "shown in the provided image(s) or video frame(s).\n"
            "Return a JSON object with the following schema:\n"
            "```json\n"
            '{ "title": "string", "confidence_score": float, "reasoning": "string" }\n'
            "```\n"
            "Rules:\n"
            "1. 'title' must be the official title from TMDB/IMDb.\n"
            "2. If unsure (< 0.8 confidence) or unrelated, set 'title' to 'UNKNOWN'.\n"
            "3. Ignore social media UI overlays.\n"
        )
        parts: List[Part] = [Part.from_text(text=system_instruction)]

        for url in image_urls:
            part = await self._load_image_part(url)
            parts.append(part)

        # Retry wrapper
        response_text = await self._run_with_retries(
            lambda: self._gemini_request(parts)
        )

        try:
            # Clean up potential markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            film_title = data.get("title", "UNKNOWN")
        except json.JSONDecodeError:
            # Fallback if valid JSON isn't returned
            print(f"JSON Decode Error. Raw text: {response_text}")
            film_title = "UNKNOWN"

        self.cache[cache_key] = film_title
        return film_title

    # -----------------------------
    # Internal — Gemini API call
    # -----------------------------
    async def _gemini_request(self, parts: List[Part]) -> str:
        """Execute sync Gemini call inside async thread."""
        content = Content(role="user", parts=parts)

        def _call():
            response = self.client.models.generate_content(
                model=self.model,
                contents=[content],
                config=GenerateContentConfig(response_mime_type="application/json"),
            )
            return response.text

        return await asyncio.to_thread(_call)

    # -----------------------------
    # Image loading helpers
    # -----------------------------
    async def _load_image_part(self, media_url: str) -> Part:
        """Loads an image or video from URL/Base64 and returns a Gemini Part."""

        # Base64 image case (unchanged)
        if media_url.startswith("data:image/"):
            return self._decode_base64_image(media_url)

        # Video case (mp4 or webm)
        if any(ext in media_url for ext in [".mp4", ".webm"]):
            return await self._fetch_video_part(media_url)

        # Default → treat as image
        return await self._fetch_image_from_url(media_url)

    async def _fetch_video_part(self, url: str) -> Part:
        """Download full video file and return a Gemini Part."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Failed to download video: {url}")
                video_bytes = await resp.read()

        # Gemini supports video/mp4, video/webm
        mime_type = "video/mp4" if ".mp4" in url else "video/webm"

        return Part.from_bytes(data=video_bytes, mime_type=mime_type)

    def _decode_base64_image(self, data_uri: str) -> Part:
        """Parse data:image/...;base64,xxxxx"""
        header, b64 = data_uri.split(",", 1)
        mime_type = header.split(";")[0].replace("data:", "")
        img_bytes = base64.b64decode(b64)

        return Part.from_bytes(data=img_bytes, mime_type=mime_type)

    async def _fetch_image_from_url(self, url: str) -> Part:
        """Download image via aiohttp and return a Part."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Failed to download image: {url}")
                data = await resp.read()

        # Assume JPEG if unknown (Gemini accepts generic)
        return Part.from_bytes(data=data, mime_type="image/jpeg")

    # -----------------------------
    # Retry Logic
    # -----------------------------
    async def _run_with_retries(self, func, retries: int = 3, backoff: float = 1.0):
        for attempt in range(1, retries + 1):
            try:
                return await func()
            except Exception as e:
                if attempt == retries:
                    raise RuntimeError(f"Gemini extraction failed: {e}") from e

                await asyncio.sleep(backoff * attempt)


# -------------------------------------
# Usage Example
# -------------------------------------
# extractor = GeminiFilmTitleExtractor(api_key="YOUR_API_KEY")
# title = await extractor.extract_film_title(["https://example.com/poster.jpg"])
# print(title)

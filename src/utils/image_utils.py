import io, os
from PIL import Image
import cloudinary.uploader
import aiohttp
import base64
import io
from typing import List
# import av  # PyAV

def preprocess_image(path: str, max_size=(512, 512), quality=80) -> str:
    """
      Resize and compress an image, overwriting the original path
      Returns the path to the processed image
    """
    img = Image.open(path)
    img.thumbnail(max_size) #resize to fit within max_size while preserving aspect ratio
    
    # ensure rgb (drop alpha channel if present) 
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    #overwrite compressed version
    img.save(path, format="JPEG", quality=quality, optimize=True)
    return path

    

async def delete_upload(public_id: str, resource_type: str = "image"):
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        print("delete result", result)
        return {"message": "Media deleted successfully", "result": result}
    except Exception as e:
        return Exception(f"Error deleting media: {e}")
# async def extract_images_from_media(media_urls: List[str], frame_every: int = 30) -> List[str]:
#     """
#     Given yt-dlp media URLs, return a list of image URLs or video frames as Base64 data URIs.
#     Video frames are extracted in memory using PyAV (no disk writes).
#     """
#     # Separate videos and images
#     video_urls = [url for url in media_urls if ".mp4" in url]
#     image_urls = [url for url in media_urls if any(ext in url for ext in [".jpg", ".jpeg", ".png"])]

#     frames_b64 = []

#     if video_urls:
#         # Only process the first video
#         video_url = video_urls[0]

#         # Download video bytes
#         async with aiohttp.ClientSession() as session:
#             async with session.get(video_url) as resp:
#                 if resp.status != 200:
#                     raise RuntimeError(f"Failed to download video: {video_url}")
#                 video_bytes = await resp.read()

#         # Extract frames using PyAV
#         container = av.open(io.BytesIO(video_bytes))
#         for i, frame in enumerate(container.decode(video=0)):
#             if i % frame_every != 0:
#                 continue
#             img = frame.to_image()  # PIL.Image
#             buffer = io.BytesIO()
#             img.save(buffer, format="JPEG")
#             b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
#             data_uri = f"data:image/jpeg;base64,{b64_str}"
#             frames_b64.append(data_uri)

#     # Return frames + original image URLs
#     return frames_b64 + image_urls

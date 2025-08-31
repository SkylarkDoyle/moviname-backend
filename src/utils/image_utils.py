import io, os
from PIL import Image
import cloudinary.uploader

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


async def delete_upload(public_id: str):
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        print("delete result", result)
        return {"message": "Image deleted successfully", "result": result}
    except Exception as e:
        return Exception(f"Error deleting image: {e}")
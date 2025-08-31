from pydantic_settings import BaseSettings
import cloudinary

class Settings(BaseSettings):
    tmdb_api_key: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    hf_token: str
    
    class Config:
        env_file = ".env"
        
settings = Settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret
)
     

   
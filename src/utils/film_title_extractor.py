import re 
from huggingface_hub import InferenceClient
from ..config import settings
from typing import List
 

# Initialize HuggingFace Inference client
hf_client = InferenceClient(
    provider="novita",  # ⚡ GLM-4.5V is served via Novita provider
    api_key=settings.hf_token,
)


async def extract_film_title_llm(image_urls: List[str]) -> str:
    """
    Extract film title using GLM-4.5V (Hugging Face Inference API).
    """
    
    content = [{"type": "text", "text": "Only return the film title."}]
    for url in image_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})
        
    completion = hf_client.chat.completions.create(
        model="zai-org/GLM-4.5V",
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    raw_text = completion.choices[0].message["content"]
    
    # ✅ Remove special box tokens if present
    film_title = re.sub(r"<\|.*?\|>", "", raw_text).strip()

    return film_title 
    

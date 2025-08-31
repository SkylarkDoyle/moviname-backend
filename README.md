# 🎬 moviname (Backend)

This is the **FastAPI backend** for **moviname**, an API that identifies movies or TV shows from a screenshot, video frame(s), or GIF.

---

## 🧩 How It Works
- **Cloudinary** → temporary storage for uploaded images (auto-deleted after processing)
- **HuggingFace Vision LLM (GLM-4.5V)** → analyzes the screenshot(s) and predicts the film/show title
- **TMDB API** → fetches detailed metadata about the movie/show
- **Pydantic Schemas** → ensures structured, consistent JSON responses
- **Async Queue (Semaphore)** → limits to **3 concurrent requests** for fairness

---

## 🚀 Features
- Upload an **image, video, or GIF**
- For videos → extract multiple frames automatically
- Use an **LLM** to guess the film/show title(s) from the screenshot(s)
- Search **TMDB Movies + TV Shows**
- Return rich metadata:
  - ✅ Title  
  - ✅ Overview  
  - ✅ Release Date  
  - ✅ Poster + Backdrop  
  - ✅ Rating
- Optimized with async requests + automatic Cloudinary cleanup
- Supports multiple images in one request (e.g., extracted video frames)

---

## ⚡ Tech Stack
- **Python 3.10+**
- **FastAPI**
- **httpx**
- **Pydantic**
- **Cloudinary SDK**
- **HuggingFace Inference (GLM-4.5V)**

---

## 🛠 Setup

### 1️⃣ Clone the repo
```bash
git clone https://github.com/SkylarkDoyle/moviname-backend.git
```

### 2️⃣ Setup environment & dependencies with uv
```bash
uv sync
```

### 3️⃣ Configure environment
Create a .env file in the backend root:
```bash 
TMDB_API_KEY=your_tmdb_api_key
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

### ▶️ Running the API
```bash
uv run main.py
```

## 📝 API Endpoints
- `POST /analyze` → Upload an image and get metadata
- `GET /docs` → Interactive API docs


## 🙏 Acknowledgements
- [TMDB API](https://www.themoviedb.org/documentation/api)
- [Cloudinary](https://cloudinary.com/documentation)


FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including wget, unzip) and ffmpeg
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
# CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Run the application
CMD ["uv", "run", "main.py"]
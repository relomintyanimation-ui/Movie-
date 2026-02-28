# Python ka base image
FROM python:3.9.13-slim

# System update karna aur FFmpeg install karna (Video/Audio merge ke liye zaroori)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Working directory set karna
WORKDIR /app

# Requirements file ko copy karna aur install karna
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Aapke main.py code ko copy karna
COPY . .

# Hugging Face ke default port ko expose karna
EXPOSE 7860

# Server start karne ka command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

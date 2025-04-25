from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
#from os import path as os_path
#open os_path=os.path("backend/analyzer.py")
#from analyzer import run_analysis


app = FastAPI()

# Allow frontend to access the backend
app.add_middleware(
    CORSMiddleware)

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from datetime import datetime
import joblib
from sklearn.cluster import KMeans
import cv2

app = FastAPI()

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://https://football-analysis-fhub.vercel.app.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load model once
model = joblib.load(r"D:\fifa\team_classifier.sav")  # Replace with actual model path

# Team color classifier
def classify_team_colors(detections):
    jersey_colors = []
    coords = []
    for d in detections:
        if d['class'] == 'player':
            x, y, w, h = int(d['x']), int(d['y']), int(d['width']), int(d['height'])
            coords.append((x, y, w, h))
            jersey_colors.append((d['color']['r'], d['color']['g'], d['color']['b']))

    labels = [-1] * len(detections)
    if len(jersey_colors) >= 2:
        kmeans = KMeans(n_clusters=2, random_state=0).fit(jersey_colors)
        for idx, d in enumerate(detections):
            if d['class'] == 'player':
                labels[idx] = int(kmeans.labels_[idx])

    return labels

# Video analysis
def run_analysis(input_path: str, output_dir: str) -> str:
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = os.path.join(output_dir, f"result_{timestamp}.mp4")
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        result = model.predict(frame)  # Modify this based on your model’s actual method
        detections = result.get("predictions", [])
        labels = classify_team_colors(detections)

        for i, pred in enumerate(detections):
            x, y = int(pred['x'] - pred['width'] / 2), int(pred['y'] - pred['height'] / 2)
            w, h = int(pred['width']), int(pred['height'])
            label = pred['class']
            conf = pred['confidence']
            color = (0, 255, 0) if labels[i] == 0 else (255, 0, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{label} {conf:.2f} T{labels[i]}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        out.write(frame)

    cap.release()
    out.release()
    return output_path

# Web interface (index)
@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Upload & process
@app.post("/upload")
async def analyze_video(file: UploadFile = File(...)):
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    output_path = run_analysis(input_path, OUTPUT_DIR)
    return FileResponse(output_path, media_type="video/mp4", filename=os.path.basename(output_path))
    allow_origins=["*"],  # Allow all origins for simplicity, you may want to restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],


UPLOAD_DIR = "/tmp/uploads"  # Use the /tmp directory for Vercel deployments
OUTPUT_DIR = "/tmp/outputs"  # Use the /tmp directory for Vercel deployments
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/api/analyze")
async def analyze_video(file: UploadFile = File(...)):
    # Handle file upload
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file to the server
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Perform the analysis (your custom logic here)
    output_path = run_analysis(input_path, OUTPUT_DIR)

    # Return the analysis result video
    return FileResponse(output_path, media_type="video/mp4", filename=os.path.basename(output_path))

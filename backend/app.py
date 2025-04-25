from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from analyzer import run_analysis

app = FastAPI()

# Allow frontend to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, you may want to restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# analyzer.py
import cv2
import os
from datetime import datetime
from roboflow import Roboflow
import numpy as np
from sklearn.cluster import KMeans

# Load the Roboflow model (initialize once)
#rf = Roboflow(api_key=os.getenv("vmsJ0NWzacPKCysW55Br"))
rf = Roboflow(api_key="vmsJ0NWzacPKCysW55Br")
#vmsJ0NWzacPKCysW55Br
project = rf.workspace().project("/football-field-detection-f07vi/14")  # replace with your project slug
model = project.version(1).model

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

        result = model.predict(frame, confidence=40, overlap=30).json()
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
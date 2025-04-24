from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
import base64
import supervision as sv
import numpy as np
import tempfile, cv2, os
from joblib import load 

PLAYER_DETECTION_MODEL = load(r'D:\ahahahah\team_classifier.sav')

app = FastAPI()

@app.post("/")
async def receive_video(request: Request):
    data = await request.json()
    filename = data['filename']
    filedata = base64.b64decode(data['filedata'])

    with open(filename, 'wb') as f:
        f.write(filedata)
    return {"status": "success"}

@app.post("/analyze_football_video")
async def analyze_football_video(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No selected file"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(await file.read())
        video_path = tmp.name

    try:
        frame = next(sv.get_video_frames_generator(video_path))

        # Detection and tracking logic
        result = PLAYER_DETECTION_MODEL.infer(frame, confidence=0.3)[0]
        detections = sv.Detections.from_inference(result)
        tracker = sv.ByteTrack()
        tracker.reset()

        ball_detections = detections[detections.class_id == 0]
        ball_detections.xyxy = sv.pad_boxes(ball_detections.xyxy, px=10)

        all_detections = detections[detections.class_id != 0]
        all_detections = all_detections.with_nms(threshold=0.5, class_agnostic=True)
        all_detections = tracker.update_with_detections(all_detections)

        goalkeepers = all_detections[all_detections.class_id == 1]
        players = all_detections[all_detections.class_id == 2]
        referees = all_detections[all_detections.class_id == 3]

        player_crops = [sv.crop_image(frame, xyxy) for xyxy in players.xyxy]
        players.class_id = team_classifier.predict(player_crops)

        goalkeepers.class_id = resolve_goalkeepers_team_id(players, goalkeepers)
        referees.class_id -= 1

        all_detections = sv.Detections.merge([players, goalkeepers, referees])
        players = sv.Detections.merge([players, goalkeepers])  # for projection

        field_result = FIELD_DETECTION_MODEL.infer(frame, confidence=0.3)[0]
        keypoints = sv.KeyPoints.from_inference(field_result)
        filter_mask = keypoints.confidence[0] > 0.5
        frame_points = keypoints.xy[0][filter_mask]
        pitch_points = np.array(CONFIG.vertices)[filter_mask]

        transformer = ViewTransformer(source=frame_points, target=pitch_points)

        pitch_ball_xy = transformer.transform_points(ball_detections.get_anchors_coordinates(sv.Position.BOTTOM_CENTER))
        pitch_players_xy = transformer.transform_points(players.get_anchors_coordinates(sv.Position.BOTTOM_CENTER))
        pitch_ref_xy = transformer.transform_points(referees.get_anchors_coordinates(sv.Position.BOTTOM_CENTER))

        image = draw_pitch(
            config=CONFIG,
            background_color=sv.Color.WHITE,
            line_color=sv.Color.BLACK
        )
        image = draw_pitch_voronoi_diagram_2(
            config=CONFIG,
            team_1_xy=pitch_players_xy[players.class_id == 0],
            team_2_xy=pitch_players_xy[players.class_id == 1],
            team_1_color=sv.Color.from_hex('00BFFF'),
            team_2_color=sv.Color.from_hex('FF1493'),
            pitch=image)
        image = draw_points_on_pitch(CONFIG, pitch_ball_xy, face_color=sv.Color.WHITE, edge_color=sv.Color.WHITE, radius=8, thickness=1, pitch=image)
        image = draw_points_on_pitch(CONFIG, pitch_players_xy[players.class_id == 0], face_color=sv.Color.from_hex('00BFFF'), edge_color=sv.Color.WHITE, radius=16, thickness=1, pitch=image)
        image = draw_points_on_pitch(CONFIG, pitch_players_xy[players.class_id == 1], face_color=sv.Color.from_hex('FF1493'), edge_color=sv.Color.WHITE, radius=16, thickness=1, pitch=image)

        _, buffer = cv2.imencode('.jpg', image)
        encoded_image = base64.b64encode(buffer).decode('utf-8')

        return {"voronoi_image_base64": encoded_image}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(video_path)

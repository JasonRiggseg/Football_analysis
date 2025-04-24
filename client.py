import requests
import base64

# Target endpoint must handle base64 encoded string, not multipart file
#url = "http://localhost:8000"

url = "https://fe96-34-125-199-135.ngrok-free.app/"
# Read video and encode as base64
video_file_path = r"D:\ahahahah\121364_0.mp4"

try:
    with open(video_file_path, "rb") as f:
        encoded_video = base64.b64encode(f.read()).decode("utf-8")

    # Prepare JSON payload
    payload = {"filename": "121364_0.mp4", "filedata": encoded_video}

    # Send as JSON
    response = requests.post(url, json=payload, timeout=10)

    # Handle response
    if response.status_code == 200:
        result = response.json()
        base64_image = result.get("voronoi_image_base64")

        if base64_image:
            with open("output_voronoi.jpg", "wb") as img_file:
                img_file.write(base64.b64decode(base64_image))
            print("Image saved as output_voronoi.jpg")
        else:
            print("Error: No image returned in the response")
    else:
        print(f"Error {response.status_code}: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

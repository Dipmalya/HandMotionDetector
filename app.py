from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import base64
import cv2
import numpy as np
import re
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# use eventlet or gevent when running; this example uses eventlet in instructions
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

prev_gray = None
prev_centroid = None
lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

def decode_b64_image(data_url):
    # expected "data:image/jpeg;base64,...."
    header, encoded = data_url.split(',', 1)
    data = base64.b64decode(encoded)
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

@socketio.on('frame')
def handle_frame(msg):
    global prev_gray, prev_centroid
    data_url = msg.get('image', '')
    if not data_url:
        return
    try:
        img = decode_b64_image(data_url)
    except Exception as e:
        emit('movement', {'text': 'error: invalid image', 'score': 0})
        return

    # resize to reduce CPU
    height, width = img.shape[:2]
    if max(height, width) > 640:
        scale = 640.0 / max(height, width)
        img = cv2.resize(img, (int(width*scale), int(height*scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    with lock:
        if prev_gray is None:
            prev_gray = gray
            emit('movement', {'text': 'No movement (initializing)', 'score': 0})
            return

        # Frame difference
        frame_delta = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        # dilate to fill holes
        thresh = cv2.dilate(thresh, None, iterations=2)

        # find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_area = 0
        motion_centroid = None
        for c in contours:
            area = cv2.contourArea(c)
            if area < 500:  # filter small noise
                continue
            motion_area += area
            M = cv2.moments(c)
            if M['m00'] != 0:
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                motion_centroid = (cx, cy) if (motion_centroid is None) else ( (motion_centroid[0]+cx)//2, (motion_centroid[1]+cy)//2 )

        # movement intensity
        score = int(motion_area)  # raw area -> you can scale/normalize
        if score < 1000:
            text = "No significant movement"
        elif score < 5000:
            text = "Small movement detected"
        else:
            text = "Large movement detected"

        # try to get direction if centroid available
        direction = ""
        if motion_centroid is not None and prev_centroid is not None:
            dx = motion_centroid[0] - prev_centroid[0]
            dy = motion_centroid[1] - prev_centroid[1]
            # simple thresholds
            if abs(dx) > 15:
                direction += "Right" if dx > 0 else "Left"
            if abs(dy) > 15:
                if direction:
                    direction += "-"
                direction += "Down" if dy > 0 else "Up"
            if direction:
                text += " — Direction: " + direction

        prev_gray = gray
        prev_centroid = motion_centroid

    # emit a plain text message and numeric score back to client
    emit('movement', {'text': text, 'score': score})


if __name__ == '__main__':
    # When running locally: install requirements and run with:
    #    pip install -r requirements.txt
    #    python app.py
    # Recommended: run with eventlet for Socket.IO:
    #    pip install eventlet
    #    python app.py
    #
    # The following runs on 0.0.0.0:5000
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
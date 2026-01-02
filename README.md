# HandMotionDetector

What this does
--------------
- A minimal Flask web app that opens the user's webcam in the browser,
  sends periodic frames to the server, and the server uses OpenCV to
  detect movement and returns a short text description such as:
  "No significant movement", "Small movement detected", or "Large movement detected".
  The server also attempts to output a simple direction string (Left/Right/Up/Down).

Files
-----
- app.py               -- Flask + Socket.IO server (motion logic using OpenCV)
- templates/index.html -- web UI (captures webcam, sends frames, shows movement text)
- requirements.txt     -- Python packages used

How to run (locally)
--------------------
1. Create and activate a virtual environment (recommended):
     python -m venv venv
     source venv/bin/activate   # Linux/macOS
     venv\Scripts\activate    # Windows PowerShell

2. Install dependencies:
     pip install -r requirements.txt

3. Run the server:
     python app.py

   If you see issues with Socket.IO, try explicitly installing eventlet:
     pip install eventlet

4. Open your browser at:
     http://localhost:5000

Notes and caveats
-----------------
- This is a demonstration. It sends image frames to the server for processing.
  For production / privacy-sensitive apps, perform processing on the client
  (in-browser) or ensure encrypted transport and proper privacy policy.
- Motion detection is simple frame-differencing; it will be sensitive to
  lighting changes and camera noise. Tune parameters (thresholds, blur size,
  min area) for your environment.
- If you want purely client-side detection (no frames sent), you can port
  the OpenCV logic to JavaScript (e.g. using tracking.js, OpenCV.js, or custom canvas processing).
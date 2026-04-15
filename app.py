import os
import time
import webbrowser
from threading import Timer
os.environ["FLASK_SOCKETIO_ASYNC_MODE"] = "threading"
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0" # Fixes MSMF deadlocks on external USB cams
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import sys
from unittest.mock import MagicMock
# Prevent mediapipe from pulling in the full tensorflow
mock_tf = MagicMock()
sys.modules['tensorflow'] = mock_tf
sys.modules['tensorflow.tools'] = MagicMock()
sys.modules['tensorflow.tools.docs'] = MagicMock()

import cv2
import numpy as np
import mediapipe as mp
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
# Resilient MediaPipe solutions import for PyInstaller
try:
    import mediapipe.solutions.hands as mp_hands
    import mediapipe.solutions.drawing_utils as mp_draw
except ImportError:
    try:
        import mediapipe.python.solutions.hands as mp_hands
        import mediapipe.python.solutions.drawing_utils as mp_draw
    except ImportError:
        # Fallback to direct attribute access if imports fail
        mp_hands = mp.solutions.hands
        mp_draw = mp.solutions.drawing_utils

import joblib
from collections import deque, Counter

import uuid
import sys
import time
import threading
from deep_translator import GoogleTranslator
# from word_suggester import WordSuggester

app = Flask(__name__)

# Initialize SocketIO robustly. In frozen builds some async backends may be
# unavailable which causes ValueError: Invalid async_mode specified. We:
# 1) try explicit 'threading', 2) let SocketIO autodetect, 3) fall back to a
# dummy SocketIO shim that preserves decorator/emit calls (no real websockets).
socketio = None
try:
    socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')
    print("DEBUG: SocketIO initialized with async_mode=threading", flush=True)
except Exception as e1:
    print(f"DEBUG: threading async_mode failed: {e1}", flush=True)
    try:
        socketio = SocketIO(app, cors_allowed_origins='*')
        print("DEBUG: SocketIO initialized with autodetected async_mode", flush=True)
    except Exception as e2:
        print(f"WARNING: SocketIO initialization failed ({e2}). Using dummy fallback.", flush=True)

        class _DummySocketIO:
            def __init__(self):
                self._handlers = {}

            def on(self, event):
                def decorator(f):
                    self._handlers.setdefault(event, []).append(f)
                    return f
                return decorator

            def emit(self, event, data=None, *args, **kwargs):
                print(f"DUMMY SOCKET EMIT: {event} {data}")

            def run(self, app, *args, **kwargs):
                # Fall back to Flask's built-in server when SocketIO can't initialize
                print("DUMMY SOCKET: running Flask built-in server (no websockets)", flush=True)
                app.run(*args, **kwargs)

        socketio = _DummySocketIO()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==============================
# ML MODELS & LOGIC
# ==============================
class SignLanguageSystem:
    def __init__(self):
        # Load Models
        print("DEBUG: Loading models...", flush=True)
        self.static_model = joblib.load(resource_path("isl_alphabet_model.pkl"), mmap_mode=None)
        print("DEBUG: Static model loaded.", flush=True)
        self.dynamic_model = None
        
        # Human-readable labels 
        try:
            label_map = joblib.load(resource_path("label_map.pkl"))
            self.STATIC_LABELS = [None] * len(label_map)
            for label, idx in label_map.items():
                # Make labels readable: "HELLO_HI" -> "HELLO HI"
                readable_label = label.replace("_", " ") if isinstance(label, str) else label
                self.STATIC_LABELS[idx] = readable_label
            print(f"DEBUG: Loaded {len(self.STATIC_LABELS)} labels from label_map.pkl", flush=True)
        except Exception as e:
            print(f"DEBUG: Could not load label_map.pkl ({e}). Falling back to default A-Z.", flush=True)
            self.STATIC_LABELS = [chr(i) for i in range(65, 91)] + ["HELLO", "THANK YOU"]
            
        self.DYNAMIC_LABELS = ["HELLO", "THANK YOU"]
        
        # Mediapipe
        self.mp_hands = mp_hands
        self.mp_draw = mp_draw
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Constants
        self.MOTION_THRESHOLD = 0.15
        self.STATIC_FRAMES = 12
        self.DYNAMIC_FRAMES = 30
        
        # State
        self.prev_keypoints = None
        self.stable_count = 0
        self.static_locked = False
        self.dynamic_sequence = deque(maxlen=self.DYNAMIC_FRAMES)
        
        self.sentence = ""
        self.display_sign = ""
        self.can_add_space = False
        self.language = "en"
        self.target_sentence = ""

        # # Word suggester
        # try:
        #     self.suggester = WordSuggester()
        # except Exception:
        #     self.suggester = None
        
        # Camera Initialization with multiple index retry
        print("DEBUG: Starting camera initialization...", flush=True)
        self.camera = None
        count = 0
        failsafe = False # This flag works the opposite way, so if it is False means the failsafe
                    # has been triggered (cries fathomically), basically if we cannot find the camera
                    # we set the cap to failsafe, of index 0

        #Three tries to find a working camera index, then it defaults to 0, as a failsafe.
        while(count < 3 and not failsafe):
            print(f"DEBUG: Trial {count+1}...", flush=True)
            # If index 1 opens your laptop camera, your USB camera might be 0 or 2. 
            # We prefer checking index 1 first as it's the standard for the first external USB camera.
            for index in [1, 2, 0]:
                print(f"DEBUG: Trying camera index {index}...", flush=True)
                if sys.platform == "win32":
                    temp_cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                else:
                    temp_cap = cv2.VideoCapture(index)
                if temp_cap.isOpened():
                    cap = temp_cap
                    # Give the camera a few frames to 'warm up'
                    valid_frame = False
                    for _ in range(5):
                        ret, frame = cap.read()
                        if ret and frame is not None and np.sum(frame) > 0:
                            valid_frame = True
                            break
                        time.sleep(0.1) # short delay between attempts
                        
                    # Check if it actually returned a frame with content
                    if valid_frame:
                        print(f"DEBUG: Successfully opened and read non-blank frame from camera at index {index}", flush=True)
                        self.camera = cap
                        count = 3  # Exit outer retry loop
                        break
                    else:
                        print(f"DEBUG: Camera {index} failed to return a valid frame after warm-up.", flush=True)
                    cap.release()
                else:
                    print(f"DEBUG: Could not open camera {index}", flush=True)
            
            if(count+1 == 3):
                # Still set to 0 as fallback, even if it might fail later
                if sys.platform == "win32":
                    self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                else:
                    self.camera = cv2.VideoCapture(0)
                failsafe = True
                print("WARNING: Failed to initialize camera after multiple attempts. Entering failsafe mode with index 0 (may not work).", flush=True)
                break

            if self.camera is None:
                print("WARNING: No cameras found at indices 0, 1, or 2.", flush=True)
                print("DEBUG: Retrying in a bit...", flush=True)
                time.sleep(3)  # Wait before retrying to allow any system camera initialization issues to resolve
                count+=1
            else:
                print("DEBUG: Camera successfully initialized.", flush=True)
                break

    def smart_refine(self, text):
        """Simple refinement to make detections more readable"""
        if not text: return ""
        # Remove multiple spaces, capitalize first letter, add period
        refined = " ".join(text.split())
        if refined:
            refined = refined.capitalize()
            if not refined.endswith("."):
                refined += "."
        return refined

    def translate_sentence(self):
        """Translates the sentence based on chosen language"""
        refined_en = self.smart_refine(self.sentence)
        if self.language == "hi":
            try:
                self.target_sentence = GoogleTranslator(source='auto', target='hindi').translate(refined_en)
            except:
                self.target_sentence = refined_en + " (Translation Error)"
        else:
            self.target_sentence = refined_en

    # @socketio.on('apply_suggestion')
    # def handle_apply_suggestion(data):
    #     word = data.get('word')
    #     if word:
    #         try:
    #             system.apply_suggestion(word)
    #             # Immediately push update and suggestions
    #             socketio.emit('update_status', {'sign': system.display_sign, 'sentence': system.target_sentence})
    #             token = system.get_current_token()
    #             suggestions = system.get_suggestions(token) if token else []
    #             socketio.emit('suggestions', {'prefix': token, 'suggestions': suggestions})
    #         except Exception as e:
    #             print("Suggestion apply error:", e)

    def extract_keypoints(self, results):
        """Simple append extraction (expected by static model)"""
        points = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                base_x = hand_landmarks.landmark[0].x
                base_y = hand_landmarks.landmark[0].y
                base_z = hand_landmarks.landmark[0].z
                for lm in hand_landmarks.landmark:
                    points.extend([lm.x - base_x, lm.y - base_y, lm.z - base_z])
        while len(points) < 126:
            points.extend([0, 0, 0])
        return np.array(points[:126])

    def extract_handed_keypoints(self, results):
        """Handedness-aware extraction (expected by dynamic model and better for motion)"""
        left = np.zeros(63)
        right = np.zeros(63)
        if results.multi_hand_landmarks and results.multi_handedness:
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                label = results.multi_handedness[i].classification[0].label
                points = []
                for lm in hand_landmarks.landmark:
                    points.extend([lm.x, lm.y, lm.z])
                if label == "Left":
                    left = np.array(points)
                else:
                    right = np.array(points)
        return np.concatenate([left, right])

    def process_frame(self):
        try:
            success, frame = self.camera.read()
            if not success:
                return None

            # Extract landmarks on the un-mirrored frame to preserve trained x-coordinates
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)
            
            # Draw
            if results.multi_hand_landmarks:
                for hl in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, hl, self.mp_hands.HAND_CONNECTIONS)
            
            # Logic
            if not results.multi_hand_landmarks:
                if self.can_add_space:
                    if self.sentence and not self.sentence.endswith(" "):
                        self.update_sentence(" ")
                    self.can_add_space = False
                self.prev_keypoints = None
                self.stable_count = 0
                self.static_locked = False
                self.display_sign = ""
                # Clear dynamic sequence immediately when hands are not detected to prevent cross-motion buildup
                self.dynamic_sequence.clear()
            else:
                # Use handed keypoints for motion and dynamic sequence
                handed_keypoints = self.extract_handed_keypoints(results)
                
                motion = 0
                if self.prev_keypoints is not None:
                    motion = np.linalg.norm(handed_keypoints - self.prev_keypoints)
                self.prev_keypoints = handed_keypoints

                # Dynamic Recognition
                # Increased threshold from 0.05 to 0.20 to avoid hand jitter or slow transitions building up the dynamic sequence
                if motion > 0.20:
                    self.stable_count = 0
                    self.static_locked = False
                    self.dynamic_sequence.append(handed_keypoints)
                    
                    if len(self.dynamic_sequence) == self.DYNAMIC_FRAMES:
                        if self.dynamic_model is None:
                            try:
                                import onnxruntime as ort
                                self.dynamic_model = ort.InferenceSession(resource_path("dynamic_sign_model.onnx"))
                                self.input_name = self.dynamic_model.get_inputs()[0].name
                            except Exception as e:
                                print(f"DEBUG: Dynamic model load fail: {e}", flush=True)
                        
                        if self.dynamic_model:
                            X = np.array(self.dynamic_sequence, dtype=np.float32).reshape(1, self.DYNAMIC_FRAMES, 126)
                            try:
                                pred = self.dynamic_model.run(None, {self.input_name: X})[0][0]
                                confidence = np.max(pred)
                                label_idx = np.argmax(pred)
                                
                                # Be extremely strict with confidence since the ONNX model is binary and 
                                # will output high probability even for garbage transition data.
                                if confidence > 0.999:
                                    self.display_sign = self.DYNAMIC_LABELS[label_idx]
                                    self.update_sentence(self.display_sign + " ")
                                    self.can_add_space = True
                                    self.dynamic_sequence.clear()
                                else:
                                    # Clear entirely to force the user to start the motion over, 
                                    # avoiding consecutive false-positive hits during transitions.
                                    self.dynamic_sequence.clear()
                            except Exception as e:
                                print(f"DEBUG: Dynamic pred fail: {e}", flush=True)
                
                # Static Recognition
                else:
                    self.stable_count += 1
                    if self.stable_count >= self.STATIC_FRAMES and not self.static_locked:
                        # Use simple append keypoints for static model
                        static_keypoints = self.extract_keypoints(results)
                        X = static_keypoints.reshape(1, -1)
                        try:
                            pred = self.static_model.predict(X)[0]
                            if 0 <= pred < len(self.STATIC_LABELS):
                                predicted_sign = self.STATIC_LABELS[pred]
                                
                                # Enforce Option 2 (True Dynamic): Do not allow the Static Model to hijack dynamic phrases
                                # If the static model predicts "HELLO", ignore it so the dynamic ONNX/ViT has time to process the movement!
                                if predicted_sign is not None and predicted_sign.upper() in [d.upper() for d in self.DYNAMIC_LABELS]:
                                    pass  # Suppress and wait
                                elif predicted_sign is not None:
                                    self.display_sign = predicted_sign
                                    self.update_sentence(self.display_sign)
                                    self.can_add_space = True
                                    self.static_locked = True
                                    self.dynamic_sequence.clear()
                        except Exception as e:
                            print(f"DEBUG: Static pred fail: {e}", flush=True)

            # Send updates (wrapped for stability)
            try:
                socketio.emit('update_status', {
                    'sign': self.display_sign, 
                    'sentence': self.target_sentence or self.sentence
                })
            except Exception as e:
                # Silently fail if socket is not ready/connected
                pass
            
            # Flip frame horizontally for natural visual display right before returning
           # frame = cv2.flip(frame, 1)
            return frame

        except Exception as e:
            print(f"CRITICAL ERROR in process_frame: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Emit word suggestions for the current partial token
        # try:
        #     token = self.get_current_token()
        #     suggestions = self.get_suggestions(token) if token and self.suggester else []
        #     socketio.emit('suggestions', {'prefix': token, 'suggestions': suggestions})
        # except Exception:
        #     pass
        
        return frame

    def update_sentence(self, new_text):
        self.sentence += new_text
        self.translate_sentence() # Update translation immediately

    def get_current_token(self):
        # Return current partial token (characters after last space)
        if not self.sentence:
            return ""
        if self.sentence.endswith(" "):
            return ""
        parts = self.sentence.rstrip().split(" ")
        return parts[-1] if parts else ""

    # def get_suggestions(self, prefix):
    #     if not self.suggester or not prefix:
    #         return []
    #     return self.suggester.suggest(prefix)

    # def apply_suggestion(self, word: str):
    #     # Replace current partial token with selected suggestion and add a space
    #     if not word:
    #         return
    #     if self.sentence.endswith(" ") or not self.sentence:
    #         self.sentence = (self.sentence + word + " ").lstrip()
    #     else:
    #         parts = self.sentence.rstrip().split(" ")
    #         if parts:
    #             parts[-1] = word
    #             self.sentence = " ".join(parts) + " "
    #         else:
    #             self.sentence = word + " "
    #     self.translate_sentence()

    def clear(self):
        self.sentence = ""
        self.target_sentence = ""
    
    def backspace(self):
        # Remove a single character from the end of the sentence
        if not self.sentence:
            return
        self.sentence = self.sentence[:-1]
        self.translate_sentence()  # Update translation immediately

# Global Instance
system = SignLanguageSystem()

# ==============================
# ROUTES
# ==============================
@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    while True:
        frame = system.process_frame()
        if frame is None:
            # Try to reconnect or just wait
            print("Warning: Camera frame read failed. Retrying...")
            time.sleep(3)
            continue
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Add slight delay to reduce CPU usage and release GIL
        time.sleep(0.01)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ==============================
# SOCKET EVENTS
# ==============================
@socketio.on('command')
def handle_command(data):
    cmd = data.get('action')
    if cmd == 'clear':
        system.clear()
    elif cmd == 'backspace':
        system.backspace()
    elif cmd == 'speak':
        # Hook up TTS here if needed, or do it frontend side
        pass

@socketio.on('set_language')
def handle_set_language(data):
    system.language = data.get('language', 'en')
    system.translate_sentence()
    # Force update
    socketio.emit('update_status', {'sign': system.display_sign, 'sentence': system.target_sentence})

@socketio.on('translate_now')
def handle_translate_now(data):
    text = data.get('text')
    target_lang = data.get('target', 'hi')
    if text:
        try:
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            socketio.emit('stt_translation', {'translated': translated})
        except Exception as e:
            print(f"Translation Error: {e}")
            socketio.emit('stt_translation', {'translated': text + " (Translation Error)"})

def open_browser():
    """Automatically open the browser to the app's URL."""
    webbrowser.open_new("http://127.0.0.1:5000")

def _start_socketio_server():
    """Run SocketIO server (usable from a background thread)."""
    socketio.run(app, debug=False, port=5000, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    # Prefer launching inside an Edge WebView2 window when pywebview is available.
    try:
        import webview
        WEBVIEW_AVAILABLE = True
    except Exception:
        WEBVIEW_AVAILABLE = False

    if WEBVIEW_AVAILABLE:
        print("DEBUG: pywebview is available. Attempting to launch...", flush=True)
        # Start the Flask/SocketIO server in a background thread, then start the WebView
        server_thread = threading.Thread(target=_start_socketio_server, daemon=True)
        server_thread.start()

        # Give the server a moment to start (matches previous 1.5s browser delay)
        time.sleep(1.0) 

        try:
            # Try to create an Edge Chromium (WebView2) window. If the user's system
            # does not have WebView2 runtime installed or the backend is unavailable,
            # pywebview will raise and we'll fall back to opening the system browser.
            print("DEBUG: Creating webview window...", flush=True)
            webview.create_window("SignBridge", "http://127.0.0.1:5000", width=1024, height=768)
            # Request the Edge Chromium gui backend explicitly for WebView2.
            print("DEBUG: Starting webview with edgechromium backend...", flush=True)
            webview.start(gui='edgechromium')
        except Exception as e:
            import traceback
            print(f"ERROR: WebView start failed: {e}", flush=True)
            traceback.print_exc()
            print("DEBUG: Falling back to external browser.", flush=True)
            webbrowser.open_new("http://127.0.0.1:5000")
            # If user closes browser, keep server running until process exit.
            server_thread.join()

    else:
        print("WARNING: pywebview NOT found. Cascading to browser launch.", flush=True)
        # No pywebview available — open the external browser after a short delay
        Timer(0.8, open_browser).start()
        _start_socketio_server()

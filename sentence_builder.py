import cv2
import sys
import numpy as np
from collections import deque
import mediapipe as mp
import joblib
from tensorflow.keras.models import load_model
from gtts import gTTS
from playsound import playsound
import uuid
import os
import time

# ==============================
# LOAD MODELS
# ==============================
static_model = joblib.load("isl_alphabet_model.pkl")
dynamic_model = load_model("dynamic_sign_model.h5")

STATIC_LABELS = [chr(i) for i in range(65, 91)]  # A-Z
DYNAMIC_LABELS = ["HELLO", "THANK YOU"]

# ==============================
# MEDIAPIPE
# ==============================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ==============================
# PARAMETERS
# ==============================
MOTION_THRESHOLD = 0.05  # motion norm to detect movement
STATIC_FRAMES = 6        # frames of stability to accept static gesture
DYNAMIC_FRAMES = 30      # frames for dynamic gesture sequence

# ==============================
# STATE VARIABLES
# ==============================
prev_keypoints = None
stable_count = 0

sentence = ""
display_sign = ""

# Static control
static_locked = False

# Dynamic control
dynamic_sequence = deque(maxlen=DYNAMIC_FRAMES)

# ==============================
# TTS FUNCTION
# ==============================
def speak_sentence_online(text):
    if not text.strip():
        return
    filename = f"tts_{uuid.uuid4()}.mp3"
    gTTS(text=text, lang="en").save(filename)
    playsound(filename)
    os.remove(filename)

# ==============================
# BACKSPACE FUNCTION
# ==============================
def backspace_sentence(text):
    if not text:
        return text
    if text.endswith(" "):
        return text[:-1]
    parts = text.rstrip().split(" ")
    if len(parts) > 1:
        return " ".join(parts[:-1]) + " "
    return text[:-1]

# ==============================
# KEYPOINT EXTRACTION
# ==============================
def extract_keypoints(results):
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

# ==============================
# WEBCAM
# ==============================
cap = None
# Try index 1 first, then 0, then 2. Index 1 often works better for integrated cams when virtual cams exist.
for index in [1, 0, 2]:
    # Use DirectShow on Windows for better compatibility
    temp_cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if np.any([s in sys.platform for s in ["win32", "cygwin"]]) else cv2.VideoCapture(index)
    
    if temp_cap.isOpened():
        ret, frame = temp_cap.read()
        # Check if frame is valid and not entirely black (blank)
        if ret and frame is not None and np.sum(frame) > 0:
            print(f"🎥 Webcam started at index {index} | Press Q to quit")
            cap = temp_cap
            break
        temp_cap.release()

if cap is None:
    print("❌ Error: Could not open any functioning camera at index 0, 1, or 2.")
    # Final fallback attempt
    cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hl in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)

    if not results.multi_hand_landmarks:
        prev_keypoints = None
        stable_count = 0
        static_locked = False
        dynamic_sequence.clear()
        display_sign = ""
    else:
        keypoints = extract_keypoints(results)
        motion = 0
        if prev_keypoints is not None:
            motion = np.linalg.norm(keypoints - prev_keypoints)
        prev_keypoints = keypoints

        # ==============================
        # DYNAMIC GESTURE (motion detected)
        # ==============================
        if motion > MOTION_THRESHOLD:
            stable_count = 0
            static_locked = False
            dynamic_sequence.append(keypoints)

            if len(dynamic_sequence) == DYNAMIC_FRAMES:
                X = np.array(dynamic_sequence).reshape(1, DYNAMIC_FRAMES, 126)
                try:
                    pred = dynamic_model.predict(X, verbose=0)[0]
                    confidence = np.max(pred)
                    label_index = np.argmax(pred)

                    if confidence > 0.75:
                        display_sign = DYNAMIC_LABELS[label_index]
                        sentence += display_sign + " "
                        dynamic_sequence.clear()  # Reset after successful prediction
                except Exception as e:
                    print("Dynamic prediction error:", e)
                # Removed dynamic_sequence.clear() to allow sliding window

        # ==============================
        # STATIC GESTURE (motion stable)
        # ==============================
        else:
            # Removed dynamic_sequence.clear() to allow brief pauses
            stable_count += 1
            if stable_count >= STATIC_FRAMES and not static_locked:
                X = keypoints.reshape(1, -1)
                try:
                    pred = static_model.predict(X)[0]
                    if 0 <= pred < len(STATIC_LABELS):
                        display_sign = STATIC_LABELS[pred]
                        sentence += display_sign
                        static_locked = True
                        dynamic_sequence.clear() # Reset dynamic buffer on static confirm
                except Exception as e:
                    print("Static prediction error:", e)
                stable_count = 0

    # ==============================
    # UI
    # ==============================
    cv2.putText(frame, f"Sign: {display_sign}", (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    cv2.rectangle(frame, (20, 95), (620, 145), (0, 0, 0), -1)
    cv2.putText(frame, f"Sentence: {sentence[-40:]}", (30, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

    cv2.imshow("ISL Sentence Builder", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        speak_sentence_online(sentence)
    elif key == ord('c'):
        sentence = ""
    elif key == ord('b'):
        sentence = backspace_sentence(sentence)

cap.release()
cv2.destroyAllWindows()

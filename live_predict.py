import cv2
import mediapipe as mp
import numpy as np
import joblib
import sys

# Load trained model
model = joblib.load("isl_alphabet_model.pkl")

# Label mapping (0–25 → A–Z)
labels = [chr(i) for i in range(65, 91)]

# Mediapipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = None
# Try index 1 first, then 0, then 2. Index 1 often works better for integrated cams when virtual cams exist.
for index in [1, 0, 2]:
    # Use DirectShow on Windows for better compatibility
    temp_cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if np.any([s in sys.platform for s in ["win32", "cygwin"]]) else cv2.VideoCapture(index)
    
    if temp_cap.isOpened():
        ret, frame = temp_cap.read()
        # Check if frame is valid and not entirely black (blank)
        if ret and frame is not None and np.sum(frame) > 0:
            print(f"🎥 Webcam started at index {index}. Press Esc to quit.")
            cap = temp_cap
            break
        temp_cap.release()

if cap is None:
    print("❌ Error: Could not open any functioning camera at index 0, 1, or 2.")
    # Final fallback attempt
    cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    landmark_list = []

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            for lm in hand_landmarks.landmark:
                landmark_list.extend([lm.x, lm.y, lm.z])

        # Ensure exactly 126 values (2 hands)
        if len(landmark_list) == 126:
            X = np.array(landmark_list).reshape(1, -1)
            pred = model.predict(X)[0]
            letter = labels[pred]

            cv2.putText(
                frame,
                f"Sign: {letter}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                3
            )

    cv2.imshow("ISL Alphabet Recognition", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

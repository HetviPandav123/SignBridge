import cv2
import sys
import numpy as np
import mediapipe as mp

# MediaPipe modules
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Initialize Hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,                 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Open webcam
cap = None
# Try index 1 first, then 0, then 2. Index 1 often works better for integrated cams when virtual cams exist.
for index in [1, 0, 2]:
    # Use DirectShow on Windows for better compatibility
    temp_cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if np.any([s in sys.platform for s in ["win32", "cygwin"]]) else cv2.VideoCapture(index)
    
    if temp_cap.isOpened():
        ret, frame = temp_cap.read()
        # Check if frame is valid and not entirely black (blank)
        if ret and frame is not None and np.sum(frame) > 0:
            print(f"🎥 Webcam started at index {index}. Press Q to quit.")
            cap = temp_cap
            break
        temp_cap.release()

if cap is None:
    print("❌ Error: Could not open any functioning camera at index 0, 1, or 2.")
    # Final fallback attempt
    cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)  # Mirror view
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    # If hands detected
    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):

            # Draw landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2)
            )

            # Identify Left / Right hand
            hand_label = results.multi_handedness[idx].classification[0].label

            # Wrist landmark for text position
            wrist = hand_landmarks.landmark[0]
            h, w, _ = frame.shape
            cx, cy = int(wrist.x * w), int(wrist.y * h)

            cv2.putText(
                frame,
                hand_label,
                (cx - 30, cy - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

    cv2.imshow("Two Hand Tracking", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()

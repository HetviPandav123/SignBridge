import cv2
import sys
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
from collections import deque
from collections import Counter

pred_buffer = deque(maxlen=10)

# ==============================
# LOAD TRAINED DYNAMIC MODEL
# ==============================
model = load_model("dynamic_sign_model.h5")
labels = ["hello", "thank_you"]   # update if you have more

# ==============================
# MEDIAPIPE HANDS
# ==============================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ==============================
# SEQUENCE BUFFER
# ==============================
SEQUENCE_LENGTH = 30
sequence = deque(maxlen=SEQUENCE_LENGTH)

# ==============================
# EXTRACT 126 KEYPOINTS
# ==============================
def extract_keypoints(results):
    left_hand = np.zeros(63)
    right_hand = np.zeros(63)

    if results.multi_hand_landmarks and results.multi_handedness:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            label = results.multi_handedness[idx].classification[0].label

            hand = []
            for lm in hand_landmarks.landmark:
                hand.extend([lm.x, lm.y, lm.z])

            if label == "Left":
                left_hand = np.array(hand)
            else:
                right_hand = np.array(hand)

    return np.concatenate([left_hand, right_hand])

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
            print(f"🎥 Webcam started at index {index} | Press Esc to quit")
            cap = temp_cap
            break
        temp_cap.release()

if cap is None:
    print("❌ Error: Could not open any functioning camera at index 0, 1, or 2.")
    # Final fallback attempt
    cap = cv2.VideoCapture(0)

last_prediction = ""
confidence_threshold = 0.75

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Draw landmarks
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    # Extract keypoints
    if results.multi_hand_landmarks:
        keypoints = extract_keypoints(results)
        sequence.append(keypoints)


    # Predict when sequence is full
    if len(sequence) == SEQUENCE_LENGTH:
        input_data = np.expand_dims(sequence, axis=0)
        predictions = model.predict(input_data, verbose=0)[0]

        confidence = np.max(predictions)
        predicted_label = labels[np.argmax(predictions)]

        if confidence > 0.6:   # lowered threshold for real-time detection
            pred_buffer.append(predicted_label)
            # Most frequent prediction in buffer = stable prediction
            last_prediction = Counter(pred_buffer).most_common(1)[0][0]

    # Display result
    cv2.putText(
        frame,
        f"Sign: {last_prediction}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 255, 0),
        3
    )

    cv2.imshow("Dynamic Sign Recognition", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

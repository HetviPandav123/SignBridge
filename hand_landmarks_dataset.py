import cv2
import mediapipe as mp
import csv
import os
import time

# ---------------- CONFIG ----------------
SIGN_NAME = "C"          # Change to B, C, D...
DATASET_DIR = "dataset"
CAPTURE_DELAY = 0.5      # seconds
# ----------------------------------------
 
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

# Create folder
sign_path = os.path.join(DATASET_DIR, SIGN_NAME)
os.makedirs(sign_path, exist_ok=True)

csv_path = os.path.join(sign_path, "data.csv")
file_exists = os.path.isfile(csv_path)

with open(csv_path, mode="a", newline="") as f:
    writer = csv.writer(f)

    # Write header once
    if not file_exists:
        header = []
        for hand in ["L", "R"]:
            for i in range(21):
                header.extend([f"{hand}_{i}_x", f"{hand}_{i}_y", f"{hand}_{i}_z"])
        writer.writerow(header)

    last_capture_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        row = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )
                for lm in hand_landmarks.landmark:
                    row.extend([lm.x, lm.y, lm.z])

            # Auto capture every 1 second
            current_time = time.time()
            if current_time - last_capture_time >= CAPTURE_DELAY:
                while len(row) < 126:
                    row.extend([0, 0, 0])

                writer.writerow(row)
                print(f"✔ Auto-saved sample for {SIGN_NAME}")
                last_capture_time = current_time

        cv2.putText(
            frame,
            f"Auto capturing: {SIGN_NAME}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow("Auto Dataset Collection", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

cap.release()
cv2.destroyAllWindows()

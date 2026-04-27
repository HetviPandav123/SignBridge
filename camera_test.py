import cv2

def test_camera_indices():
    index = 0
    arr = []
    while index < 5:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Camera found at index {index}")
                arr.append(index)
            else:
                print(f"Camera at index {index} is opened but can't read frame (maybe in use?)")
            cap.release()
        else:
            print(f"No camera found at index {index}")
        index += 1
    return arr

if __name__ == "__main__":
    available = test_camera_indices()
    if not available:
        print("No accessible cameras found.")
    else:
        print(f"Available indices: {available}")

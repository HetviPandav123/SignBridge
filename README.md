## 🧏‍♀️ SignBridge — Indian Sign Language Smart Communication System

---

SignBridge is a real-time Indian Sign Language (ISL) to Text communication system that converts static and dynamic hand gestures into readable sentences, with live translation support, using Computer Vision + Machine Learning.

---

## 🎯 Project Features

- ✅ Works as a single-click executable (SignBridge.exe)
- 🖐️ Real-time hand tracking using MediaPipe
- 🔤 Static ISL alphabet recognition (A–Z)
- 🎥 Dynamic word recognition (e.g. Hello, Thank You)
- 🧠 Intelligent motion-based switching between static & dynamic signs
- 📝 Automatic sentence building with spacing logic
- 🌐 Live translation (English ↔ Hindi)
- 🖥️ Web-based UI served locally via Flask
- 🔄 Real-time frontend updates using Socket.IO
- ⚡ Optimized for performance & deployment (PyInstaller-ready)

---

## 🧠 How the System Works (Core Logic)

### Motion-Based Intelligence
- Low motion (stable hand) → Static sign detection (letters)
- Continuous motion → Dynamic sign detection (words)
- Prevents repeated predictions using locking & cooldown logic

### Smart Sentence Builder
- Automatically adds letters and words
- Inserts spaces intelligently
- Supports clearing & backspacing
- Refines output into readable sentences

---

## 🕶️ Smart Glasses Prototype (Basic Version)

https://github.com/user-attachments/assets/a26603fc-08d6-4ab4-ac14-63908bd6c44b

To extend SignBridge beyond a software system, a **basic prototype of smart glasses** was implemented.

### 🔧 Prototype Setup
- External webcam mounted to simulate camera input
- Headphones used for:
  - Speaker (audio output)
  - Microphone (future voice interaction support)
- Connected to the system running SignBridge

### ⚙️ Working
- Webcam captures real-time hand gestures
- SignBridge processes gestures → converts to text
- Output is converted into speech via headphones
- Simulates how future smart glasses will:
  - Detect signs using built-in camera sensors
  - Convert them into real-time speech for non-sign users

### 🚀 Future Scope
- Integration of embedded camera sensors
- Built-in mic + speaker inside glasses
- Fully portable, wearable communication device

---

## 🔄 Data Enhancement & Model Improvement

To improve model accuracy and robustness, additional data was collected and the model was retrained.

### 📸 New Data Collection (Different Angles)
- Data was re-collected with multiple hand orientations and angles
- Included variations such as:
  - Slight rotations of hand
  - Different distances from camera
  - Lighting condition changes
- Helps the model generalize better in real-world scenarios

### 🧾 Updated Dataset
- New samples appended to existing dataset (data.csv)
- Maintained same 126 landmark feature format
- Balanced dataset across all alphabets

### 🧠 Model Retraining
- Old + new dataset merged
- Model retrained using Scikit-learn
- Improvements:
  - Better accuracy
  - More stable real-time detection
  - Reduced misclassification for similar signs

---

## 🛠️ Tech Stack

### Core Technologies
- Python
- OpenCV
- MediaPipe
- NumPy, Pandas
- Scikit-learn
- TensorFlow / Keras (for dynamic signs)
- gTTS (Text-to-Speech)
- ONNX Runtime

### Backend
- Flask
- Flask-SocketIO

### Frontend
- HTML / CSS / JavaScript
- WebSockets

### Deployment
- PyInstaller
- Git LFS

---

## 📂 Project Structure

sign-language-smart-communication/
│
├── app.py
├── templates/
│   └── index.html
├── static/
│   └── assets/
│
├── isl_alphabet_model.pkl
├── dynamic_sign_model.onnx
│
├── dist/
│   └── SignBridge.exe
│
├── .gitattributes
├── .gitignore
├── README.md

---

## 🖥️ User Interface

- Live camera feed
- Displays:
  - Current detected sign
  - Constructed sentence
  - Translated sentence

---

## ✋ Static Sign Recognition (A–Z)

### Dataset
- Each alphabet (A–Z) has its own folder
- Data stored as data.csv
- Each row contains 126 features (21 landmarks × 3 × 2 hands)

### Training
- All CSV files are merged
- Labels assigned per alphabet
- Model trained using Scikit-learn

Saved as: isl_alphabet_model.pkl

https://github.com/user-attachments/assets/71d4b8d2-443e-41b3-a5e7-9cc44beda388

---

## 🎥 Dynamic Sign Recognition (Hello, Thank You etc.)

### Dataset Creation
- Short videos recorded for each word
- MediaPipe extracts landmarks per frame
- Each frame → 126 features
- Frames combined into fixed-length sequences
- Saved as .npy files

Example shape: (sequence_length, 126)

### Training
- .npy sequences loaded
- Labels assigned (hello / thank_you)
- Sequence-based model (LSTM)

Saved as: dynamic_sign_model.h5, dynamic_sign_model.pkl

https://github.com/user-attachments/assets/52a8b8ed-b645-4b15-99c0-eb7084307ea5

---

## 🔄 Real-Time Logic

- Low motion → Static model (letters)
- High motion → Dynamic model (words)
- Static letters form sentences
- Dynamic words are displayed/spoken directly

---

## 🔊 Text-to-Speech

- Uses Google Text-to-Speech (gTTS)
- Press S to speak the sentence
- Temporary audio files auto-deleted

https://github.com/user-attachments/assets/0291d2be-7cc2-4521-8bce-1b288516b94a

---

## ⌨️ Controls

| Key |       Action     |
|-----|------------------|
| q   | Quit application |
| s   | Speak sentence   |
| b   | Backspace        |
| c   | Clear sentence   |

---

## 🚀 Running the Application

### 🔹 Option 1: End User (Recommended)

- Download SignBridge.exe from dist
- Double-click to run
- Start signing ✋
- No Python installation required

### 🔹 Option 2: Developer Mode

pip install -r requirements.txt  
python app.py  

---

## 📦 Large Files & Git LFS

This repository uses Git LFS for:
- .exe files
- ML model files

### Clone Properly

git lfs install  
git clone https://github.com/HetviPandav123/sign-language-smart-communication.git  
git lfs pull  

---

## 🧠 Outcome

This system enables real-time ISL to speech translation, improving communication accessibility for the hearing-impaired and mute community.

https://github.com/user-attachments/assets/2aa04f1a-f1bb-475b-97be-cfdde3c278d2

---

## 👩‍💻 Author

Hetvi Pandav  
BE – Artificial Intelligence & Machine Learning  

---

⭐ If you found this project useful, feel free to star the repository!

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
- New samples appended to existing dataset (`data.csv`)  
- Maintained same **126 landmark feature format**  
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

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# DATASET_PATH = "dataset" # Use this if training on the manually collected dataset
DATASET_PATH = "dataset" # Use this if training on the auto-processed ISL dataset
MODEL_PATH = "isl_alphabet_model.pkl"
LABEL_MAP_PATH = "label_map.pkl"

X, y = [], []

LABELS = sorted(os.listdir(DATASET_PATH))
label_map = {label: idx for idx, label in enumerate(LABELS)}

EXPECTED_FEATURES = None

for label in LABELS:
    csv_path = os.path.join(DATASET_PATH, label, "data.csv")

    if not os.path.exists(csv_path):
        print(f"⚠ Missing {csv_path}")
        continue

    print(f"📄 Loading {label}")

    df = pd.read_csv(
        csv_path,
        engine="python",
        on_bad_lines="skip"
    )

    for _, row in df.iterrows():
        # Skip header rows accidentally stored as data
        if isinstance(row.iloc[0], str):
            continue

        row_values = row.values

        # Convert safely
        try:
            row_values = row_values.astype(float)
        except:
            continue

        # Lock feature length once
        if EXPECTED_FEATURES is None:
            EXPECTED_FEATURES = len(row_values)
            print(f"✅ Feature length set to {EXPECTED_FEATURES}")

        # Skip corrupted rows
        if len(row_values) != EXPECTED_FEATURES:
            continue

        X.append(row_values)
        y.append(label_map[label])

# ==============================
# FINAL DATASET CHECK
# ==============================
X = np.array(X)
y = np.array(y)

print("\n📊 FINAL DATASET")
print("X shape:", X.shape)
print("y shape:", y.shape)
print("Unique classes:", len(np.unique(y)))

if len(np.unique(y)) < 2:
    raise ValueError("❌ Dataset has only one class!")

# ==============================
# TRAIN
# ==============================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)

print("\n🚀 Training model...")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"🎯 Accuracy: {accuracy * 100:.2f}%")

joblib.dump(model, MODEL_PATH)
joblib.dump(label_map, LABEL_MAP_PATH)

print("💾 Model & label map saved")
print("🧠 Classes learned:", len(label_map))

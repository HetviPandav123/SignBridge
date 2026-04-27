import os
import pandas as pd

DATASET_DIR = "dataset"
OUTPUT_FILE = "final_dataset.csv"


all_data = []

labels = sorted(os.listdir(DATASET_DIR))  # A-Z



for label_index, label_name in enumerate(labels):
    folder_path = os.path.join(DATASET_DIR, label_name)
    csv_path = os.path.join(folder_path, "data.csv")

    if not os.path.exists(csv_path):
        continue

    df = pd.read_csv(
    csv_path,
    header=None,
    engine="python",
    on_bad_lines="skip"
)


    cleaned_rows = []

    for _, row in df.iterrows():
        values = row.values.tolist()

        # FIX row length
        if len(values) > 126:
            values = values[:126]
        elif len(values) < 126:
            values.extend([0.0] * (126 - len(values)))

        cleaned_rows.append(values)

    clean_df = pd.DataFrame(cleaned_rows)
    clean_df["label"] = label_index
    clean_df["letter"] = label_name

    all_data.append(clean_df)

final_df = pd.concat(all_data, ignore_index=True)
final_df.to_csv(OUTPUT_FILE, index=False)

print("✅ Dataset merged & cleaned successfully")
print("Total samples:", len(final_df))
print("Saved as:", OUTPUT_FILE)

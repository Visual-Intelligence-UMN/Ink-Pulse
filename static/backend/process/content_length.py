import json
import os
from collections import Counter

script_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.dirname(os.path.dirname(script_dir))

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

def convert_format(dataset_name):
    note_dir = os.path.join(static_dir, "dataset", f"{dataset_name}", "length.json")
    data = load_json(note_dir)
    bin_counts = Counter()
    bin_size = 500
    for length in data:
        bin_start = int(length // bin_size) * bin_size
        bin_end = bin_start + bin_size
        bin_label = f"{bin_start}-{bin_end}"
        bin_counts[bin_label] += 1
    bin_counts = sorted(bin_counts.items(), key=lambda x: int(x[0].split("-")[0]))

    print(dict(bin_counts))
    
    save_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "length_summary.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(bin_counts, f, ensure_ascii=False, indent=4)

def main(dataset_name):
    note_dir = os.path.join(static_dir, "dataset", f"{dataset_name}", "similarity_results")
    length = []
    for file_name in os.listdir(note_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(note_dir, file_name)
            data = load_json(file_path)
            name = file_name.split('_')[0]
            sentence = data[-1]["sentence"] * 3000
            length.append({
                "session_id": name,
                "sentence": sentence
            })
    save_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "length.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(length, f, ensure_ascii=False, indent=4)
    convert_format(dataset_name)
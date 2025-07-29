import json
import os
from collections import Counter

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "similarity_results")
    length = []
    for file_name in os.listdir(note_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(note_dir, file_name)
            name = file_name.split('_')[0]
            data = load_json(file_path)
            sentence = data[0]["sentence"] * 3000
            length.append(sentence)
    save_path = os.path.join(static_dir, "chi2022-coauthor-v1.0", "length.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(length, f, ensure_ascii=False, indent=4)

def convert_format():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "length.json")
    data = load_json(note_dir)
    bin_counts = Counter()
    bin_size = 500
    for _, length in data:
        bin_start = int(length // bin_size) * bin_size
        bin_end = bin_start + bin_size
        bin_label = f"{bin_start}-{bin_end}"
        bin_counts[bin_label] += 1
    bin_counts = sorted(bin_counts.items(), key=lambda x: int(x[0].split("-")[0]))

    print(dict(bin_counts))
    
    save_path = os.path.join(static_dir, "chi2022-coauthor-v1.0", "length_summary.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(bin_counts, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":    
    main()
    # convert_format()
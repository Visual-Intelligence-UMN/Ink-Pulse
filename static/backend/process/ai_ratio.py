import json
import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.dirname(os.path.dirname(script_dir))

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data
            
def change_format(dataset_name):
    note_dir = os.path.join(static_dir, "dataset", f"{dataset_name}", "percentage.json")
    data = load_json(note_dir)
    df = pd.DataFrame(data, columns=["id", "ai_ratio", "human_ratio"])
    bins = [i/10 for i in range(11)]
    labels = [f"{int(b*100)}–{int((b+0.1)*100)}%" for b in bins[:-1]]
    df["ai_bin"] = pd.cut(df["ai_ratio"], bins=bins, labels=labels, include_lowest=True)
    bin_counts = df["ai_bin"].value_counts().sort_index()
    bin_counts = bin_counts.to_dict()
    print(bin_counts)
    
    save_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "percentage_summary.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(bin_counts, f, ensure_ascii=False, indent=4)

def main(dataset_name):
    note_dir = os.path.join(static_dir, "dataset", f"{dataset_name}", "coauthor-json")
    summary = []
    for file_name in os.listdir(note_dir):
        ai_num = 0
        human_num = 0
        session_id = os.path.splitext(file_name)[0]
        if file_name.endswith(".jsonl"):
            file_path = os.path.join(note_dir, file_name)
            data = load_json(file_path)
            for d in data["info"]:
                if d["name"] == "text-insert":
                    if d["eventSource"] == "api":
                        ai_num += d["count"]
                    else:
                        human_num += d["count"]
            all = ai_num + human_num
            summary.append([session_id, ai_num / all, human_num / all])
    save_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "percentage.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)
    change_format(dataset_name)
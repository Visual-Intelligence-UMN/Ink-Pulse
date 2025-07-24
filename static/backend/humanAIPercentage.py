import json
import os
import pandas as pd

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "coauthor-json")
    summary = []
    for file_name in os.listdir(note_dir):
        ai_num = 0
        human_num = 0
        session_id = os.path.splitext(file_name)[0]
        if file_name.endswith(".jsonl"):
            file_path = os.path.join(note_dir, file_name)
            data = load_json(file_path)
            for d in data["info"]:
                if d["eventSource"] == "api":
                    ai_num += 1
                else:
                    human_num += 1
            all = ai_num + human_num
            summary.append([session_id, ai_num / all, human_num / all])
    save_path = os.path.join(static_dir, "chi2022-coauthor-v1.0", "percentage.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)
            
def change_format():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "percentage.json")
    data = load_json(note_dir)
    df = pd.DataFrame(data, columns=["id", "ai_ratio", "human_ratio"])
    bins = [i/10 for i in range(11)]
    labels = [f"{int(b*100)}–{int((b+0.1)*100)}%" for b in bins[:-1]]
    df["ai_bin"] = pd.cut(df["ai_ratio"], bins=bins, labels=labels, include_lowest=True)
    bin_counts = df["ai_bin"].value_counts().sort_index()
    bin_counts = bin_counts.to_dict()
    print(bin_counts)
    
    save_path = os.path.join(static_dir, "chi2022-coauthor-v1.0", "percentage_summary.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(bin_counts, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":    
    main()
    change_format()
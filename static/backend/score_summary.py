import json
import os

dataset_name = "argumentative"

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", f"eval_results-{dataset_name}")
    num_dic = {}
    num = []
    for file_name in os.listdir(note_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(note_dir, file_name)
            data = load_json(file_path)
            num.append(data[0])
    for n in num:
        if n in num_dic:
            num_dic[n] += 1
        else:
            num_dic[n] = 1
    print(num_dic)
    save_path = os.path.join(static_dir, "chi2022-coauthor-v1.0", f"score_summary-{dataset_name}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(num_dic, f, ensure_ascii=False, indent=4)
            
if __name__ == "__main__":    
    main()
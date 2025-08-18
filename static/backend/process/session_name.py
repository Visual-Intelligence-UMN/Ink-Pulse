import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.dirname(os.path.dirname(script_dir))

def write_json(json_path, dataset_name):
    name = []
    for file_name in os.listdir(json_path):
        name.append(file_name)
    new_file_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "session_name.json")
    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(name, f, ensure_ascii=False, indent=4)
    print(f"Data written to {new_file_path}")

def main(dataset_name):
    json_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "similarity_results")
    write_json(json_path, dataset_name)
import os
import json

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        data = json.loads(content)
    if not isinstance(data, list) or len(data) == 0 or not all(isinstance(item, dict) for item in data):
        print(f"Invalid structure in file {file_path}")
        return
    
    for event in data:
        if event["start_progress"] > event["end_progress"]:
            t = event["start_progress"]
            event["start_progress"] = event["end_progress"]
            event["end_progress"] = t

    # for i, event in enumerate(data):
    #     if i == 0:
    #         event["height"] = event["end_progress"] - event["start_progress"]
    #         event["norm_vector"] = 0
    #     else:
    #         height = event["end_progress"] - event["start_progress"]
    #         if height < 0:
    #             height = 0
    #         event["height"] = height
    #         event["norm_vector"] = event["residual_vector_norm"] / len(event["sentence"])
    # max_norm_vector = max(event["norm_vector"] for event in data)
    # for event in data:
    #     event["max_norm_vector"] = max_norm_vector

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False,  indent=4)

def process_files(base_path):
    for filename in os.listdir(base_path):
        if filename.endswith('.jsonl'):
            file_path = os.path.join(base_path, filename)
            read_file(file_path)
            print(f"Updated height in file: {filename}")

script_dir = os.path.dirname(os.path.abspath(__file__)) 
static_dir = os.path.dirname(script_dir)
json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-json")
process_files(json_path)
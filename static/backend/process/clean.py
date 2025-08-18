import json
import re
import os

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

# If you want to keep explanation for the score, can use this function
# def clean_eval(data):
#     cleaned = []
#     for item in data:
#         eval_str = item.get("Evaluation", "")
#         json_match = re.search(r'\{[\s\S]*?\}', eval_str)
#         if json_match:
#             eval_data = json.loads(json_match.group(0))
#             cleaned.append(eval_data)
#     return cleaned

# Clean evaluation file
def clean_eval(data):
    scores = [item["Score"] for item in data]
    return scores

# Clean similarity file
def clean(data):
    for entry in data:
        length = len(entry["sentence"])
        entry.pop("residual_vector", None)
        entry["sentence"] = length / 3000
    return data 

def main(dataset_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(os.path.dirname(script_dir))
    eval_dir = os.path.join(static_dir, "dataset", f"{dataset_name}", "eval_results")
    similarity_dir = os.path.join(static_dir, "dataset", f"{dataset_name}", "similarity_results")

    for file_name in os.listdir(eval_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(eval_dir, file_name)
            cleaned_data = clean_eval(load_json(file_path))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

    for file_name in os.listdir(similarity_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(similarity_dir, file_name)
            cleaned_data = clean(load_json(file_path))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
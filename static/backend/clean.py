import json
import re
import os

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data
# clean code for Evaluation content
# def clean(data):
#     cleaned = []
#     for item in data:
#         eval_str = item.get("Evaluation", "")
#         json_match = re.search(r'\{[\s\S]*?\}', eval_str)
#         if json_match:
#             eval_data = json.loads(json_match.group(0))
#             cleaned.append(eval_data)
#     return cleaned

# def clean(data):
#     cleaned = []
#     for item in data:
#         score = item.get("idea_score", 0) + item.get("coherence_score", 0)
#         cleaned.append(score)
#     return cleaned

def clean(data):
    return [d for d in data if d["residual_vector_norm"] != 0]


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    # note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "eval_results")
    note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "similarity_results")
    for file_name in os.listdir(note_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(note_dir, file_name)
            cleaned_data = clean(load_json(file_path))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":    
    # main()
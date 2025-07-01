import os
import json
import numpy as np
from scipy.stats import norm
import re
import math

def sentence(text):
    if not re.search(r'[.!?]$', text):
        text = re.sub(r'[^.!?]+$', '', text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(sentences)

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        data = json.loads(content)
    if not isinstance(data, list) or len(data) == 0 or not all(isinstance(item, dict) for item in data):
        print(f"Invalid structure in file {file_path}")
        return
    for i, event in enumerate(data):
        if i == 0:
            event["residual_vector_norm"] = 0
        else:
            prev_sentence = data[i - 1]["sentence"].strip()
            curr_sentence = event["sentence"].strip()
            prev_sen_num = sentence(prev_sentence)
            curr_sen_num = sentence(curr_sentence)

            delta = curr_sen_num - prev_sen_num
            delta = delta if delta > 0 else 1
            char_diff = abs(len(curr_sentence) - len(prev_sentence))

            scale_factor = math.sqrt(delta)

            if abs(char_diff) <= 10:
                event["residual_vector_norm"] = 0
            else:
                event["residual_vector_norm"] = event["residual_vector"] / scale_factor

    values = [e["residual_vector_norm"] for e in data]
    if len(values) == 0:
        for e in data:
            e["residual_vector_norm"] = 0
    elif len(values) == 1:
        for e in data:
            if e["residual_vector_norm"] != 0:
                e["residual_vector_norm"] = 1
            else:
                e["residual_vector_norm"] = 0
    else:
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val
        range_val = range_val if range_val > 0 else 1
        for e in data:
            val = e["residual_vector_norm"]
            if val != 0:
                norm_val = (val - min_val) / range_val
                e["residual_vector_norm"] = norm_val
            else:
                e["residual_vector_norm"] = 0

    # values = [e["residual_vector_norm"] for e in data if e["residual_vector_norm"] != 0]
    
    # if len(values) == 0:
    #     for e in data:
    #         e["residual_vector_norm"] = 0
    # elif len(values) == 1:
    #     for e in data:
    #         if e["residual_vector_norm"] != 0:
    #             e["residual_vector_norm"] = 1
    #         else:
    #             e["residual_vector_norm"] = 0
    # else:
    #     log_values = np.log1p(values)
    #     mean_val = np.mean(log_values)
    #     std_val = np.std(log_values)
    #     if std_val == 0:
    #         for e in data:
    #             if e["residual_vector_norm"] != 0:
    #                 e["residual_vector_norm"] = 1
    #             else:
    #                 e["residual_vector_norm"] = 0
    #     else:
    #         def normalize_residual(val):
    #             log_val = np.log1p(val)
    #             z = (log_val - mean_val) / std_val
    #             return norm.cdf(z)
    #         for e in data:
    #             val = e["residual_vector_norm"]
    #             if val != 0:
    #                 e["residual_vector_norm"] = normalize_residual(val)
    #             else:
    #                 e["residual_vector_norm"] = 0

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def delete_sentence(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        data = json.loads(content)
    if data and "sentence" in data[-1]:
        length = len(data[-1]["sentence"]) / 3000
    else:
        length = 0.0
    for item in data:
        item["sentence"] = length
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def process_files(base_path):
    for filename in os.listdir(base_path):
        if filename.endswith('.json'):
            file_path = os.path.join(base_path, filename)
            # read_file(file_path)
            delete_sentence(file_path)
            print(f"Update file: {filename}")

def write_json(json_path):
    name = []
    for file_name in os.listdir(json_path):
        name.append(file_name)
    new_file_path = os.path.join(static_dir, "session_name.json")
    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(name, f, ensure_ascii=False, indent=4)
    print(f"Data written to {new_file_path}")
        
script_dir = os.path.dirname(os.path.abspath(__file__)) 
static_dir = os.path.dirname(script_dir)
json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/similarity_results")
process_files(json_path)
# write_json(json_path)
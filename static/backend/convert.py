# import json
# import os
# import pandas as pd
# from collections import Counter
# from datetime import datetime
# import random
# random.seed(23)
# import csv
# import numpy as np

# def path_exists(path):
#     if not os.path.exists(path):
#       os.makedirs(path)
#       print(f"Create folder in {path}")
#     else:
#       print(f"Folder already exist in {path}.")

# dataset_name = "argumentative"

# script_dir = os.path.dirname(os.path.abspath(__file__))
# static_dir = os.path.dirname(script_dir)
# csv_path = f"{dataset_name}.csv"

# import_data_dir = os.path.join(static_dir, "import_dataset")
# json_path = os.path.join(static_dir, "import_dataset", f"{dataset_name}")
# session_id_collection = []
# for filename in os.listdir(json_path):
#     filename = filename.removesuffix(".jsonl")
#     session_id_collection.append(filename)

# topic_dir = os.path.join(import_data_dir, f"{dataset_name}.csv")

# new_path = os.path.join(static_dir, "dataset", f"{dataset_name}")
# path_exists(new_path)

# new_json_path = os.path.join(static_dir, f"dataset/{dataset_name}/json")
# path_exists(new_json_path)

# new_sentence_path = os.path.join(static_dir, f"dataset/{dataset_name}/sentence")
# path_exists(new_sentence_path)

# new_sentence_results_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "sentence_results")
# path_exists(new_sentence_results_path)

# eval_path = os.path.join(static_dir, "dataset", f"{dataset_name}", "eval_results")

# fine_file_path = os.path.join(static_dir, "dataset", f"{dataset_name}", f"fine.json")

# judge_score = []
# topic_df = pd.read_csv(topic_dir)
# for file_name in os.listdir(eval_path):
#     if file_name.endswith(".json"):
#         file_path = os.path.join(eval_path, file_name)
#         session_id = os.path.splitext(file_name)[0]
#         session = topic_df[topic_df["session_id"] == session_id]
#         with open(file_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         if not session.empty:
#             judge_score.append({
#                 "session_id": session_id,
#                 "judge_score": data
#             })

# def clean_judge_score(data):
#     judge = data.get("judge_score", {})
#     score = judge.get("score", judge.get("Score", None)) if isinstance(judge, dict) else judge
#     data["judge_score"] = score[0]

#     return data

# judge_score = [clean_judge_score(score) for score in judge_score]

# def load_json(file_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     return data

# for filename in os.listdir(new_sentence_results_path):
#     if filename.endswith('_similarity.json'):
#         new_filename = filename.replace('_similarity.json', '.json')
#         old_file = os.path.join(new_sentence_results_path, filename)
#         new_file = os.path.join(new_sentence_results_path, new_filename)
#         os.rename(old_file, new_file)

# length = []
# def calculate_length(path):
#   for file_name in os.listdir(path):
#       session_id = os.path.splitext(file_name)[0]
#       if file_name.endswith(".json"):
#           file_path = os.path.join(path, file_name)
#           data = load_json(file_path)
#           sentence = data[-1]["sentence"] * 3000
#           length.append({
#               "session_id": session_id,
#               "length": round(sentence, 2)
#           })
#   return length

# calculate_length(new_sentence_results_path)

# AI_ratio = []
# def calculate_AI_ratio(path):
#   for file_name in os.listdir(path):
#       ai_num = 0
#       human_num = 0
#       session_id = os.path.splitext(file_name)[0]
#       if file_name.endswith(".jsonl"):
#           file_path = os.path.join(path, file_name)
#           data = load_json(file_path)
#           for d in data["info"]:
#               if d["name"] == "text-insert":
#                   if d["eventSource"] == "api":
#                       ai_num += d["count"]
#                   else:
#                       human_num += d["count"]
#           all = ai_num + human_num
#           AI_ratio.append({
#               "session_id": session_id,
#               "AI_ratio": ai_num / all
#           })
#   return AI_ratio

# calculate_AI_ratio(new_json_path)

# sum_semantic_score = []
# def calculate_sum_semantic_score(path):
#   for file_name in os.listdir(path):
#       session_id = os.path.splitext(file_name)[0]
#       if file_name.endswith(".json"):
#           file_path = os.path.join(path, file_name)
#           data = load_json(file_path)
#           score = 0
#           for d in data:
#             score += d["residual_vector_norm"]
#           sum_semantic_score.append({
#               "session_id": session_id,
#               "sum_semantic_score": score
#           })
#   return sum_semantic_score

# calculate_sum_semantic_score(new_sentence_results_path)

# prompt_code = []
# def find_prompt_code(csv_path):
#     with open(csv_path, mode='r', encoding='utf-8') as file:
#         csv_reader = csv.DictReader(file)
#         for row in csv_reader:
#             session_id = row.get('session_id')
#             topic = row.get('prompt_code')
#             if session_id and topic:
#                 prompt_code.append({
#                     "session_id": session_id,
#                     "prompt_code": topic
#                 })
    
#     return prompt_code

# find_prompt_code(csv_path)

# feature_names = ['prompt_code', 'judge_score', 'length', 'AI_ratio', 'sum_semantic_score']

# def merge_2_csv_json(feature_names):
#   data_lists = {
#      'prompt_code': prompt_code,
#       'judge_score': judge_score,
#       'length': length,
#       'AI_ratio': AI_ratio,
#       'sum_semantic_score': sum_semantic_score,
#   }

#   dfs = [pd.DataFrame(data_lists[feature]) for feature in feature_names]
#   df = dfs[0]
#   for other_df in dfs[1:]:
#       df = df.merge(other_df, on='session_id', how='outer')
#   output_path_csv = os.path.join(static_dir, f"dataset/{dataset_name}", "fine.csv")
#   df.to_csv(output_path_csv, index=False)
#   output_path_json = os.path.join(static_dir, f"dataset/{dataset_name}", "fine.json")
#   data = df.to_dict(orient='records')
#   with open(output_path_json, "w", encoding="utf-8") as f:
#       json.dump(data, f, ensure_ascii=False, indent=4)
# merge_2_csv_json(feature_names)

# import pandas as pd
# import json
# import os
# import csv

# dataset_name = "creative"

# script_dir = os.path.dirname(os.path.abspath(__file__))
# static_dir = os.path.dirname(script_dir)
# csv_path = os.path.join(static_dir, "import_dataset", f"{dataset_name}.csv")

# prompt_code = []

# def find_prompt_code(csv_path):
#     with open(csv_path, mode='r', encoding='utf-8') as file:
#         csv_reader = csv.DictReader(file)
#         for row in csv_reader:
#             session_id = row.get('session_id')
#             topic = row.get('prompt_code')
#             if session_id and topic:
#                 prompt_code.append({
#                     "session_id": session_id,
#                     "prompt_code": topic
#                 })
#     return prompt_code

# def load_existing_data():
#     with open(os.path.join(static_dir, f"dataset/{dataset_name}", "fine.json"), "r", encoding="utf-8") as f:
#         fine_json_data = json.load(f)
#     fine_csv_path = os.path.join(static_dir, f"dataset/{dataset_name}", "fine.csv")
#     fine_csv_data = pd.read_csv(fine_csv_path)

#     return fine_json_data, fine_csv_data

# def merge_with_prompt_code(fine_json_data, fine_csv_data, prompt_code):
#     prompt_code_dict = {item['session_id']: item['prompt_code'] for item in prompt_code}

#     for item in fine_json_data:
#         session_id = item.get("session_id")
#         if session_id in prompt_code_dict:
#             item["prompt_code"] = prompt_code_dict[session_id]
#     fine_csv_data['prompt_code'] = fine_csv_data['session_id'].map(prompt_code_dict)

#     return fine_json_data, fine_csv_data

# def save_merged_data(fine_json_data, fine_csv_data):
#     output_path_json = os.path.join(static_dir, f"dataset/{dataset_name}", "fine.json")
#     with open(output_path_json, "w", encoding="utf-8") as f:
#         json.dump(fine_json_data, f, ensure_ascii=False, indent=4)

#     output_path_csv = os.path.join(static_dir, f"dataset/{dataset_name}", "fine.csv")
#     fine_csv_data.to_csv(output_path_csv, index=False)

# def update_fine_files():
#     prompt_code_data = find_prompt_code(csv_path)
#     fine_json_data, fine_csv_data = load_existing_data()
#     fine_json_data, fine_csv_data = merge_with_prompt_code(fine_json_data, fine_csv_data, prompt_code_data)
#     save_merged_data(fine_json_data, fine_csv_data)

# update_fine_files()


import os
import json
from datetime import datetime

def convert_and_calculate(data):
    info = data["info"]
    total_length = len(data['text'][0])
    for i in info:
        i['progress'] = len(i['current_text']) / total_length
        i.pop('current_text', None)
        
    return data


def write_json(data, file_path, session):
    actual_session = session+'.jsonl'
    new_file_path = os.path.join(file_path, actual_session)
    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data written to {new_file_path}")

info_data = []
sentence_data = []
def get_data(dataset_name, session_id_collection, static_dir, is_json):
    if is_json:
        json_path = os.path.join(static_dir, f"dataset/{dataset_name}/json")
    else:
        json_path = os.path.join(static_dir, f"dataset/{dataset_name}/segment")
    for session in session_id_collection:
        extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': [], 'snapshots': []}
        file_path = os.path.join(static_dir, "import_dataset", f"{dataset_name}")
        actual_session = session + '.jsonl'
        new_file_path = os.path.join(file_path, actual_session)
        with open(new_file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                cleaned_line = line.replace('\0', '')
                if cleaned_line.strip():
                    json_data = json.loads(cleaned_line)
                    if line_number == 1:
                        init_text = json_data.get('currentDoc', '')
                        init_timestamp = json_data.get('eventTimestamp')
                        init_time = datetime.fromtimestamp(init_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    event_num = json_data.get('eventNum')
                    event_name = json_data.get('eventName')
                    event_source = json_data.get('eventSource')
                    event_timestamp = json_data.get('eventTimestamp')
                    event_time = datetime.fromtimestamp(event_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    last_event_time = event_time
                    text_delta = json_data.get('textDelta', {})
                    current_suggestions = json_data.get('currentSuggestions', {})
                    entry = {'eventNum': event_num, 'eventName': event_name, 'eventSource': event_source, 'event_time': event_time, 'textDelta': text_delta, 'currentSuggestions': current_suggestions}
                    extracted_data['json'].append(entry)
        extracted_data['init_time'].append(init_time)
        extracted_data['init_text'].append(init_text)
        text = ''.join(extracted_data['init_text'])
        previous_event_name = None
        if text != "" and text != "\n":
            extracted_data['snapshots'].append({
                'text': text,
                'eventName': '',
                'eventSource': 'api',
                'event_time': init_time,
                'eventNum': 0
            })
        for entry in extracted_data['json']:
            text_delta = entry.get('textDelta', {})
            if not isinstance(text_delta, dict):
                if isinstance(text_delta, str) and text_delta.strip():
                    try:
                        text_delta = json.loads(text_delta)
                    except json.JSONDecodeError:
                        text_delta = {}
                else:
                    text_delta = {}
            ops = text_delta.get('ops', [])
            event_name = entry.get('eventName')
            event_source = entry.get('eventSource', 'unknown')
            event_time = entry.get('event_time')
            event_num = entry.get('eventNum')
            pos = entry.get('currentCursor', 0)
            for op in ops:
                if 'retain' in op:
                    pos += op['retain']
                elif 'insert' in op:
                    inserts = op['insert']
                    if not isinstance(inserts, str):
                        # print(f"skip image insert: {inserts}")
                        continue
                    source = event_source
                    if previous_event_name == "suggestion-close" and len(inserts) > 5:
                        source = "api"
                    text = text[:pos] + inserts + text[pos:]
                    extracted_data['info'].append({
                        'id': event_num,
                        'name': 'text-insert',
                        'text': inserts,
                        'eventSource': source,
                        'event_time': event_time,
                        'count': len(inserts),
                        'pos': pos,
                        'current_text': text,
                    })
                    pos += len(inserts)
                elif 'delete' in op:
                    delete_count = op['delete']
                    deleted_text = text[pos:pos + delete_count]
                    text = text[:pos] + text[pos + delete_count:]
                    extracted_data['info'].append({
                        'id': event_num,
                        'name': 'text-delete',
                        'text': deleted_text,
                        'eventSource': event_source,
                        'event_time': event_time,
                        'count': delete_count,
                        'pos': pos,
                        'current_text': text,
                    })
            if event_name == 'suggestion-open':
                extracted_data['info'].append({
                    'id': event_num,
                    'name': event_name,
                    'eventSource': event_source,
                    'event_time': event_time,
                    'current_text': text,
                })
                extracted_data['snapshots'].append({
                    'text': text,
                    'eventName': event_name,
                    'eventSource': event_source,
                    'event_time': event_time,
                    'eventNum': event_num
                })
            if ops:
                extracted_data['snapshots'].append({
                    'text': text,
                    'eventName': event_name,
                    'eventSource': source,
                    'event_time': event_time,
                    'eventNum': event_num
                })
            previous_event_name = event_name
        if entry['eventNum'] == None:
            for entry in extracted_data['info']:
                if 'id' in entry:
                    del entry['id']
        # print(text)
        extracted_data['text'].append(text)
        extracted_data['end_time'] = last_event_time
        extracted_data = convert_and_calculate(extracted_data)
        extracted_data.pop('json', None)
        extracted_data.pop('snapshots', None)
        if is_json:
            write_json(extracted_data, json_path, session)
        # else:
        #     write_json(data, json_path, session)

if __name__ == "__main__":
    dataset_name = "legislation_formal_study"
    static_dir = "D:\Study\Lab\Vitualization\Ink-Pulse\static"
    json_path = os.path.join(static_dir, "import_dataset", f"{dataset_name}")
    session_id_collection = []
    for filename in os.listdir(json_path):
        filename = filename.removesuffix(".jsonl")
        session_id_collection.append(filename)
    get_data(dataset_name, session_id_collection, static_dir, is_json=True)







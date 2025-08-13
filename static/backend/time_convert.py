import os
import json
from datetime import datetime

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        data = json.loads(content)
    if not isinstance(data, list) or len(data) == 0 or not all(isinstance(item, dict) for item in data):
        print(f"Invalid structure in file {file_path}")
        return

    base_time_str = data[0]['start_time']
    base_time = datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")
    
    for event in data:
        if 'start_time' in event:
            start_time = datetime.strptime(event['start_time'], "%Y-%m-%d %H:%M:%S")
            event['start_time'] = (start_time - base_time).total_seconds()
        if 'end_time' in event:
            end_time = datetime.strptime(event['end_time'], "%Y-%m-%d %H:%M:%S")
            event['end_time'] = (end_time - base_time).total_seconds()
        if 'last_event_time' in event:
            last_event_time = datetime.strptime(event['last_event_time'], "%Y-%m-%d %H:%M:%S")
            event['last_event_time'] = (last_event_time - base_time).total_seconds()

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False,  indent=4)

def process_files(base_path):
    for filename in os.listdir(base_path):
        if filename.endswith('.jsonl'):
            file_path = os.path.join(base_path, filename)
            read_file(file_path)
            print(f"Updated times in file: {filename}")

script_dir = os.path.dirname(os.path.abspath(__file__)) 
static_dir = os.path.dirname(script_dir)
# json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence-new")
process_files(json_path)
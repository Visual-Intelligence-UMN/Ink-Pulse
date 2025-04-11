import os
import json
from datetime import datetime

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file {file_path}: {e}")
        return
    
    if not isinstance(data, list) or len(data) == 0 or not all(isinstance(item, list) for item in data):
        print(f"Invalid structure in file {file_path}")
        return

    base_time_str = data[0][0]['start_time']
    base_time = datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")
    
    for item in data:
        for event in item:
            start_time_str = event['start_time']
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            relative_start_time = (start_time - base_time).total_seconds()
            event['start_time'] = relative_start_time

            end_time_str = event['end_time']
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            relative_end_time = (end_time - base_time).total_seconds()
            event['end_time'] = relative_end_time

            if 'last_event_time' in event:
                last_event_time_str = event['last_event_time']
                last_event_time = datetime.strptime(last_event_time_str, "%Y-%m-%d %H:%M:%S")
                relative_last_event_time = (last_event_time - base_time).total_seconds()
                event['last_event_time'] = relative_last_event_time

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
json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
process_files(json_path)
import json
import datetime
import os

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

def write_json(data, file_path, session):
    actual_session = session+'.jsonl'
    new_file_path = os.path.join(file_path, actual_session)
    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data written to {new_file_path}")

def get_data(dataset_name, session_id, static_dir, is_json):
    if is_json:
        json_path = os.path.join(static_dir, f"dataset/{dataset_name}/coauthor-json")
    else:
        json_path = os.path.join(static_dir, f"dataset/{dataset_name}/coauthor-sentence")
    for session in session_id:
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
                        init_time = datetime.datetime.fromtimestamp(init_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    event_num = json_data.get('eventNum')
                    event_name = json_data.get('eventName')
                    event_source = json_data.get('eventSource')
                    event_timestamp = json_data.get('eventTimestamp')
                    event_time = datetime.datetime.fromtimestamp(event_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
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
                    })
            if event_name == 'suggestion-open':
                extracted_data['info'].append({
                    'id': event_num,
                    'name': event_name,
                    'eventSource': event_source,
                    'event_time': event_time,
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
        data = collect_data(extracted_data['snapshots'])
        data = calculate_progress(data)
        extracted_data['text'].append(text)
        extracted_data['end_time'] = last_event_time
        extracted_data.pop('json', None)
        extracted_data.pop('snapshots', None)
        if is_json:
            write_json(extracted_data, json_path, session)
        else:
            write_json(data, json_path, session)

def check(data, correct):
    text = data['init_text'][0] if data['init_text'] else ""
    for entry in sorted(data["info"], key=lambda x: x['id']):
        op_type = entry['name']
        content = entry.get('text', '')
        pos = entry.get('pos', 0)

        if op_type == 'text-insert':
            text = text[:pos] + content + text[pos:]
        elif op_type == 'text-delete':
            text = text[:pos] + text[pos + len(content):]
    # print(correct)
    # print(text)
    # if text == correct:
    #     print("yes")
    # else:
    #     print("no")

def calculate_progress(data):
    total_length = len(data[-1]['text'])
    current_progress = 0
    for entry in data:
        entry['start_progress'] = current_progress
        entry['end_progress'] = len(entry['text']) / total_length
        current_progress = entry['end_progress']
    return data

def collect_data(snapshots):
    segments = []
    current_text = ""
    current_source = None
    current_start_time = None
    current_end_time = None
    last_event_time = None

    for snap in snapshots:
        text = snap['text']
        source = snap['eventSource']
        event_time = snap['event_time']
        event_name = snap['eventName']

        if current_source is None:
            current_source = source
            current_start_time = event_time
        if source != current_source or event_name == "suggestion-open":
            if current_text:
                segments.append({
                    "text": current_text,
                    "source": current_source,
                    "start_time": current_start_time,
                    "end_time": current_end_time,
                    "last_event_time": last_event_time
                })
            current_text = text
            if event_name != "suggestion-open":
                current_source = source
            current_start_time = event_time
        else:
            current_text = text

        current_end_time = event_time
        last_event_time = event_time

    if current_text:
        segments.append({
            "text": current_text,
            "source": current_source,
            "start_time": current_start_time,
            "end_time": current_end_time,
            "last_event_time": last_event_time
        })

    return segments

def main(dataset_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(os.path.dirname(script_dir))
    json_path = os.path.join(static_dir, "import_dataset", f"{dataset_name}")
    session_id = []
    for filename in os.listdir(json_path): 
        filename = filename.removesuffix(".jsonl")
        session_id.append(filename)

    new_path = os.path.join(static_dir, "dataset", f"{dataset_name}")
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        print(f"Create foler {dataset_name} in {new_path}")
    else:
        print(f"Folder {dataset_name} already exist in {new_path}.")

    new_json_path = os.path.join(static_dir, f"dataset/{dataset_name}/coauthor-json")
    if not os.path.exists(new_json_path):
        os.makedirs(new_json_path)
        print(f"Create foler coauthor-json in {new_json_path}")
    else:
        print(f"Folder coauthor-json already exist in {new_json_path}.")
    
    new_sentence_path = os.path.join(static_dir, f"dataset/{dataset_name}/coauthor-sentence")
    if not os.path.exists(new_sentence_path):
        os.makedirs(new_sentence_path)
        print(f"Create foler coauthor-sentence in {new_sentence_path}")
    else:
        print(f"Folder coauthor-sentence already exist in {new_sentence_path}.")

    get_data(dataset_name, session_id, static_dir, is_json=True)
    get_data(dataset_name, session_id, static_dir, is_json=False)
import json
import datetime
import os
import re

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

def write_json(data, file_path, session):
    actual_session = session['session_id']+'.jsonl'
    new_file_path = os.path.join(file_path, actual_session)
    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data written to {new_file_path}")

def split_text(whole_text, sentence_source):
    sentence_pattern = re.compile(r'([^.!?]*[.!?])\s*')  
    split_result = sentence_pattern.split(whole_text)
    split_result = [s for s in split_result if s]
    insert_data = []
    start_index = 0
    for sentence in split_result:
        if start_index < len(sentence_source):
            first_char_source = sentence_source[start_index]
            insert_data.append({
                "text": sentence,
                "source": first_char_source,
            })
        start_index += len(sentence)
    # print(insert_data)

    return insert_data

def get_sentence(session_id, static_dir):
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
    for session in session_id:
        extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': []}
        sentence_source = []
        file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-v1.0")
        actual_session = session['session_id']+'.jsonl'
        new_file_path = os.path.join(file_path, actual_session)
        with open(new_file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                cleaned_line = line.replace('\0', '')
                if cleaned_line.strip():
                    json_data = json.loads(cleaned_line)
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
                    text_delta = json_data.get('textDelta', {})
                    current_suggestions = json_data.get('currentSuggestions', {})
                    entry = {'eventNum': event_num, 'eventName': event_name, 'eventSource': event_source, 'event_time': event_time, 'textDelta': text_delta, 'currentSuggestions': current_suggestions}
                    extracted_data['json'].append(entry)

        extracted_data['init_time'].append(init_time)
        extracted_data['init_text'].append(init_text)
        text = ''.join(extracted_data['init_text'])
        sentence_source = ["api"] * len(text)
        for entry in extracted_data['json']:
            text_delta = entry['textDelta']
            event_source = entry.get('eventSource', 'unknown')
            event_time = entry.get('event_time', None)
            event_num = entry.get('eventNum', None)
            event_name = entry.get('eventName', None)
            if not isinstance(text_delta, dict): 
                if isinstance(text_delta, str) and text_delta.strip():
                    try:
                        text_delta = json.loads(text_delta)
                    except json.JSONDecodeError:
                        text_delta = {}
                else:
                    text_delta = {}
            ops = text_delta.get('ops', [])
            first_op = next((op for op in ops if 'retain' not in op), None)
            if event_name == "text-insert" and isinstance(first_op, dict) and 'delete' in first_op:
                event_name = "text-delete"
            if event_name == "text-insert":
                retain_pos = 0
                for op in text_delta['ops']:
                    if 'retain' in op:
                        retain_pos = op['retain']
                    if 'insert' in op:
                        inserts = op['insert']
                        insert_pos = min(retain_pos, len(text))
                        if len(inserts) > 1:
                            for i, char in enumerate(inserts):
                                current_insert_pos = insert_pos + i
                                text = text[:current_insert_pos] + char + text[current_insert_pos:]
                                sentence_source.insert(current_insert_pos, event_source)
                        else:
                            text = text[:insert_pos] + inserts + text[insert_pos:]
                            sentence_source[insert_pos:insert_pos] = [event_source] * len(inserts) 
                        break
            elif event_name == "text-delete":
                retain_pos = 0
                for op in text_delta['ops']:
                    if 'retain' in op:
                        retain_pos = op['retain']
                    if 'delete' in op:
                        delete_count = op['delete']
                        delete_pos = min(retain_pos, len(text) - 1)
                        text = text[:delete_pos] + text[delete_pos + delete_count:]
                        del sentence_source[delete_pos:delete_pos + delete_count]
                        break
        sentence_data = split_text(text, sentence_source)
        write_json(sentence_data, json_path, session)

def get_data(session_id, static_dir):
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-json")
    for session in session_id:
        extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': []}
        file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-v1.0")
        actual_session = session['session_id']+'.jsonl'
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
        for entry in extracted_data['json']:
            text_delta = entry['textDelta']
            event_source = entry.get('eventSource', 'unknown')
            event_time = entry.get('event_time', None)
            event_num = entry.get('eventNum', None)
            event_name = entry.get('eventName', None)
            current_suggestions = entry['currentSuggestions']
            if not isinstance(text_delta, dict): 
                # whether text part is empty or not
                if isinstance(text_delta, str) and text_delta.strip():
                    try:
                        text_delta = json.loads(text_delta)
                    except json.JSONDecodeError:
                        text_delta = {}
                else:
                    text_delta = {}
            ops = text_delta.get('ops', [])
            first_op = next((op for op in ops if 'retain' not in op), None)
            if event_name == "text-insert" and isinstance(first_op, dict) and 'delete' in first_op:
                # if multiple operation, check
                event_name = "text-delete"
            if event_name == "text-insert":
                retain_pos = 0
                for op in text_delta['ops']:
                    if 'retain' in op:
                        retain_pos = op['retain']
                    if 'insert' in op:
                        inserts = op['insert']
                        insert_pos = min(retain_pos, len(text))
                        last_pos = max(last_pos, insert_pos + len(inserts))
                        if len(inserts) > 1:
                            for i, char in enumerate(inserts):
                                current_insert_pos = insert_pos + i
                                text = text[:current_insert_pos] + char + text[current_insert_pos:]
                                extracted_data['info'].append({
                                    'id': event_num,
                                    'name': event_name,
                                    'text': char,
                                    'eventSource': event_source,
                                    'event_time': event_time,
                                    'count': 1,
                                    'pos': current_insert_pos,
                                })
                        else:
                            text = text[:insert_pos] + inserts + text[insert_pos:]
                            extracted_data['info'].append({
                                'id': event_num,
                                'name': event_name,
                                'text': inserts,
                                'eventSource': event_source,
                                'event_time': event_time,
                                'count': len(inserts),
                                'pos': insert_pos,
                            })
                        break
            elif event_name == "text-delete":
                retain_pos = 0
                for op in text_delta['ops']:
                    if 'retain' in op:
                        retain_pos = op['retain']
                    if 'delete' in op:
                        delete_count = op['delete']
                        delete_pos = min(retain_pos, len(text) - 1)
                        last_pos = min(last_pos, delete_pos)
                        deleted_text = text[delete_pos:delete_pos + delete_count]
                        text = text[:delete_pos] + text[delete_pos + delete_count:]
                        extracted_data['info'].append({
                            'id': event_num,
                            'name': event_name,
                            'text': deleted_text,
                            'eventSource': event_source,
                            'event_time': event_time,
                            'count': delete_count,
                            'pos': delete_pos,
                        })
                        break
            elif event_name == 'suggestion-open':
                if "currentSuggestions" in entry:
                    suggestions = [suggestion["trimmed"] for suggestion in entry["currentSuggestions"]]
                    extracted_data['info'].append({
                            'id': event_num,
                            'name': event_name,
                            'text': suggestions,
                            'eventSource': event_source,
                            'event_time': event_time,
                            'count': '',
                            'pos': '',
                    })
        extracted_data['text'].append(text)
        extracted_data['end_time'] = last_event_time
        write_json(extracted_data, json_path, session)
    
if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(script_dir)
    json_path = os.path.join(static_dir, "fine.json")
    session_id = load_json(json_path)
    # get_data(session_id, static_dir)
    get_sentence(session_id, static_dir)
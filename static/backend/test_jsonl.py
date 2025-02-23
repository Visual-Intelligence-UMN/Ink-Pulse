import json
import datetime

def get_data():
    extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': []}
    with open('D:/Study/Lab/Vitualization/vis-coauthor/public/chi2022-coauthor-v1.0/coauthor-v1.0/092396c287e54c3d9454ba20bb1ccc83.jsonl', 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, start=1):
            cleaned_line = line.replace('\0', '')
            if cleaned_line.strip():
                json_data = json.loads(cleaned_line)
                if line_number == 1:
                    init_text = json_data.get('currentDoc', '')
                    init_timestamp = json_data.get('eventTimestamp')
                    init_time = datetime.datetime.fromtimestamp(init_timestamp / 1000)
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
    last_pos = len(text)
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
    print(text)

if __name__ == '__main__':
    get_data()

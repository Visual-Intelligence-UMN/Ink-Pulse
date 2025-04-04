import json
import datetime
import os
import time

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

def split_text(whole_text, sentence_source, extra_time, extra_process):
    insert_data = []
    sentence = ""
    start_index = 0
    inside_quotes = False  
    quote_chars = {'"'}
    start_time = 0
    end_time = 0
    start_progress = 0
    end_progress = 0
    total_length = len(whole_text)
    extra_time = [datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in extra_time]
    time_deltas = [0]
    for j in range(1, len(extra_time)):
        time_deltas.append((extra_time[j] - extra_time[j - 1]).total_seconds())
    base_time = extra_time[0]
    for i, char in enumerate(whole_text):
        sentence += char

        if char in quote_chars:
            inside_quotes = not inside_quotes

        elif char in ".!?" and not inside_quotes:
            if i + 1 < len(whole_text) and whole_text[i + 1] in quote_chars:
                sentence += whole_text[i + 1]
                i += 1
                inside_quotes = not inside_quotes

            if start_index < len(sentence_source):
                first_char_source = sentence_source[start_index]
                start_time = sum(time_deltas[:start_index])
                start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
                start_relative_time = (start_datetime_obj - base_time).total_seconds()
                start_progress = extra_process[start_index] / total_length

                end_time = sum(time_deltas[:i + 1])
                end_datetime_obj = base_time + datetime.timedelta(seconds=end_time)
                end_relative_time = (end_datetime_obj - base_time).total_seconds()

                end_progress = extra_process[i] / total_length

                insert_data.append({
                    "text": sentence.strip(),
                    "source": first_char_source,
                    "start_time": start_relative_time,
                    "end_time": end_relative_time,
                    "start_progress": start_progress,
                    "end_progress": end_progress
                })

            start_time = end_time
            start_index += len(sentence)
            sentence = ""

        elif char == "\n" and not inside_quotes:
            if sentence.strip():
                if start_index < len(sentence_source):
                    first_char_source = sentence_source[start_index]

                    start_time = sum(time_deltas[:start_index])
                    start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
                    start_relative_time = (start_datetime_obj - base_time).total_seconds()

                    start_progress = extra_process[start_index] / total_length

                    end_time = sum(time_deltas[:i + 1])
                    end_datetime_obj = base_time + datetime.timedelta(seconds=end_time)
                    end_relative_time = (end_datetime_obj - base_time).total_seconds()

                    end_progress = extra_process[i] / total_length

                    insert_data.append({
                        "text": sentence.strip(),
                        "source": first_char_source,
                        "start_time": start_relative_time,
                        "end_time": end_relative_time,
                        "start_progress": start_progress,
                        "end_progress": end_progress
                    })

                start_time = end_time
                start_index += len(sentence)
                sentence = ""

    if sentence.strip():
        if start_index < len(sentence_source):
            first_char_source = sentence_source[start_index]

            start_time = sum(time_deltas[:start_index])
            start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
            start_relative_time = (start_datetime_obj - base_time).total_seconds()
            start_progress = extra_process[start_index] / total_length

            end_time = sum(time_deltas[:i + 1])
            end_datetime_obj = base_time + datetime.timedelta(seconds=end_time)
            end_relative_time = (end_datetime_obj - base_time).total_seconds()
            end_progress = extra_process[i] / total_length

            insert_data.append({
                "text": sentence.strip(),
                "source": first_char_source,
                "start_time": start_relative_time,
                "end_time": end_relative_time,
                "start_progress": start_progress,
                "end_progress": end_progress
            })

    return insert_data

def combine_text(text, sentence_with_source):
    insert_data = []
    length = len(text)
    inside_quotes = False  
    quote_chars = {'"'}
    start_progress = 0
    end_progress = 0
    start_index = 0
    sentence = ""
    time = [datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in sentence_with_source["time"]]
    time_deltas = [0]
    for j in range(1, len(time)):
        time_deltas.append((time[j] - time[j - 1]).total_seconds())
    base_time = time[0]
    for i, item in enumerate(sentence_with_source["text"]):
        sentence += item
        if item in quote_chars:
            inside_quotes = not inside_quotes
        elif item in ".!?" and not inside_quotes:
            if i + 1 < length and text[i + 1] in quote_chars:
                sentence += text[i + 1]
                i += 1
                inside_quotes = not inside_quotes

            if start_index < length:
                first_char_source = sentence_with_source["source"][start_index]
                start_time = sum(time_deltas[:start_index])
                start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
                start_relative_time = (start_datetime_obj - base_time).total_seconds()
                start_progress = len(text[:start_index]) / length

                end_time = sum(time_deltas[:i + 1])
                end_datetime_obj = base_time + datetime.timedelta(seconds=end_time)
                end_relative_time = (end_datetime_obj - base_time).total_seconds()
                end_progress = len(text[:i]) / length

                insert_data.append({
                    "text": sentence.strip(),
                    "source": first_char_source,
                    "start_time": start_relative_time,
                    "end_time": end_relative_time,
                    "start_progress": start_progress,
                    "end_progress": end_progress
                })

            start_time = end_time
            start_index += len(sentence)
            sentence = ""

        elif item == "\n" and not inside_quotes:
            if sentence.strip():
                if start_index < length:
                    first_char_source = sentence_with_source["source"][start_index]

                    start_time = sum(time_deltas[:start_index])
                    start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
                    start_relative_time = (start_datetime_obj - base_time).total_seconds()
                    start_progress = len(text[:start_index]) / length

                    end_time = sum(time_deltas[:i + 1])
                    end_datetime_obj = base_time + datetime.timedelta(seconds=end_time)
                    end_relative_time = (end_datetime_obj - base_time).total_seconds()

                    end_progress = len(text[:i]) / length

                    insert_data.append({
                        "text": sentence.strip(),
                        "source": first_char_source,
                        "start_time": start_relative_time,
                        "end_time": end_relative_time,
                        "start_progress": start_progress,
                        "end_progress": end_progress
                    })

                start_time = end_time
                start_index += len(sentence)
                sentence = ""

    if sentence.strip():
        if start_index < length:
            first_char_source = sentence_with_source["source"][start_index]

            start_time = sum(time_deltas[:start_index])
            start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
            start_relative_time = (start_datetime_obj - base_time).total_seconds()
            start_progress = len(text[:start_index]) / length

            end_time = sum(time_deltas[:i + 1])
            end_datetime_obj = base_time + datetime.timedelta(seconds=end_time)
            end_relative_time = (end_datetime_obj - base_time).total_seconds()
            end_progress = len(text[:i]) / length

            insert_data.append({
                "text": sentence.strip(),
                "source": first_char_source,
                "start_time": start_relative_time,
                "end_time": end_relative_time,
                "start_progress": start_progress,
                "end_progress": end_progress
            })

    return insert_data

def get_sentence(session_id, static_dir):
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
    sentence_with_source = {"text": [], "source": [], "time": []}
    for session in session_id:
        extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': []}
        sentence_source = []
        extra_time = []
        extra_process = []
        file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-v1.0")
        actual_session = session['session_id'] + '.jsonl'
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
        extra_time = [init_time] * len(text)
        extra_process = [len(text)] * len(text)

        sentence_with_source["source"] = ["api"] * len(text)
        sentence_with_source["text"] = list(text)
        sentence_with_source["time"] = [init_time] * len(text)

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
                                extra_time.insert(current_insert_pos, event_time)
                                extra_process.insert(current_insert_pos, len(text))

                                sentence_with_source["text"].insert(current_insert_pos, list(char))
                                sentence_with_source["source"].insert(current_insert_pos, event_source)
                                sentence_with_source["time"].insert(current_insert_pos, event_time)
                        else:
                            text = text[:insert_pos] + inserts + text[insert_pos:]
                            sentence_source[insert_pos:insert_pos] = [event_source] * len(inserts) 
                            extra_time[insert_pos:insert_pos] = [event_time] * len(inserts) 
                            extra_process[insert_pos:insert_pos] = [len(text)] * len(inserts)

                            sentence_with_source["text"].insert(insert_pos, list(inserts))
                            sentence_with_source["source"].insert(insert_pos, [event_source] * len(inserts))
                            sentence_with_source["time"].insert(insert_pos, [event_time] * len(inserts))
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
                        del extra_time[delete_pos:delete_pos + delete_count]
                        del extra_process[delete_pos:delete_pos + delete_count]

                        sentence_with_source["text"] = sentence_with_source["text"][:delete_pos] + sentence_with_source["text"][delete_pos + delete_count:]
                        sentence_with_source["source"] = sentence_with_source["source"][:delete_pos] + sentence_with_source["source"][delete_pos + delete_count:]
                        sentence_with_source["time"] = sentence_with_source["time"][:delete_pos] + sentence_with_source["time"][delete_pos + delete_count:]
                        break
        sentence_with_source_text = []
        sentence_with_source_source = []
        sentence_with_source_time = []
        for item in sentence_with_source['text']:
            if len(item[0]):
                sentence_with_source_text.append(item[0])
            else:
                sentence_with_source_text.append(item)
        text_test = flatten(sentence_with_source['text'])
        sentence_with_source['text'] = flatten(sentence_with_source['text'])
        sentence_with_source['source'] = flatten(sentence_with_source['source'])
        sentence_with_source['time'] = flatten(sentence_with_source['time'])
        # sentence_data = split_text(text, sentence_source, extra_time, extra_process)
        sentence_data = combine_text(text, sentence_with_source)
        write_json(sentence_data, json_path, session)

def flatten(data):
    new_data = []
    for item in data:
        if isinstance(item, list):
            new_data.extend(flatten(item))
        else:
            new_data.append(item)

    return new_data

def flatten_text(text):
    new_text = []
    for item in text:
        if isinstance(item, list):
            new_text.extend(flatten_text(item))
        else:
            new_text.append(text)

    return new_text

def get_data(session_id, static_dir):
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-json")
    for session in session_id:
        extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': []}
        file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-v1.0")
        actual_session = session['session_id'] + '.jsonl'
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
import json
import datetime
import os
from itertools import groupby
import pandas as pd

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
    start_time = 0
    end_time = 0
    last_event_time = datetime.datetime.strptime(sentence_with_source["last_event_time"], "%Y-%m-%d %H:%M:%S")
    start_index = 0
    sentence = ""
    sentence_with_source["time"] = [datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in sentence_with_source["time"]]
    time = sentence_with_source["time"]
    time_deltas = [0]
    base_time = time[0]
    for j in range(1, len(time)):
        time_deltas.append((time[j] - base_time).total_seconds())
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
                start_time = time_deltas[start_index]
                start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
                start_relative_time = (start_datetime_obj - base_time).total_seconds()
                start_progress = len(text[:start_index]) / length

                if i + 1 < length:
                    end_time = time_deltas[i + 1]
                else:
                    end_time = time_deltas[length - 1]
                end_relative_time = end_time
                end_progress = len(text[:i]) / length

                insert_data.append({
                    "text": sentence.strip(),
                    "source": first_char_source,
                    "start_time": start_relative_time,
                    "end_time": end_relative_time,
                    "start_progress": start_progress,
                    "end_progress": end_progress,
                    "last_event_time": (last_event_time - base_time).total_seconds()
                })

            start_time = end_time
            start_index += len(sentence)
            sentence = ""

        elif item == "\n" and not inside_quotes:
            if sentence.strip():
                if start_index < length:
                    first_char_source = sentence_with_source["source"][start_index]

                    start_time = time_deltas[start_index]
                    start_datetime_obj = base_time + datetime.timedelta(seconds=start_time)
                    start_relative_time = (start_datetime_obj - base_time).total_seconds()
                    start_progress = len(text[:start_index]) / length

                    if i + 1 < length:
                        end_time = time_deltas[i + 1]
                    else:
                        end_time = time_deltas[length - 1]
                    end_relative_time = end_time

                    end_progress = len(text[:i]) / length

                    insert_data.append({
                        "text": sentence.strip(),
                        "source": first_char_source,
                        "start_time": start_relative_time,
                        "end_time": end_relative_time,
                        "start_progress": start_progress,
                        "end_progress": end_progress,
                        "last_event_time": (last_event_time - base_time).total_seconds()
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
                "end_progress": end_progress,
                "last_event_time": (last_event_time - base_time).total_seconds()
            })

    return insert_data

def get_sentence(session_id, static_dir):
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
    sentence_with_source = {"text": [], "source": [], "time": [], "last_event_time": []}
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
                    last_event_time = event_time
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
        sentence_with_source['text'] = flatten(sentence_with_source['text'])
        sentence_with_source['source'] = flatten(sentence_with_source['source'])
        sentence_with_source['time'] = flatten(sentence_with_source['time'])
        sentence_with_source['last_event_time'] = last_event_time
        # sentence_data = split_text(text, sentence_source, extra_time, extra_process)
        # sentence_data = combine_text(text, sentence_with_source)
        # write_json(sentence_data, json_path, session)


def flatten(data):
    new_data = []
    for item in data:
        if isinstance(item, list):
            new_data.extend(flatten(item))
        else:
            new_data.append(item)

    return new_data


def get_data(session_id, static_dir):
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
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
        data = collect_data(extracted_data['info'], init_text, init_time, text, last_event_time)
        extracted_data['text'].append(text)
        extracted_data['end_time'] = last_event_time
        # write_json(extracted_data, json_path, session)
        write_json(data, json_path, session)


def collect_data(extracted_data, init_text, init_time, whole_text, last_event_time):
    data = []
    whole_text = whole_text[:-1]
    current_text = init_text
    current_data = {
        "text": list(init_text),
        "source": "api",
        "time": [init_time] * len(init_text),
        "last_event_time": last_event_time,
    }
    data.append({
        "text": list(current_data["text"]),
        "source": current_data["source"],
        "time": list(current_data["time"]),
        "last_event_time": current_data["last_event_time"],
        "start_time": init_time,
        "end_time": init_time,
    })
    current_start_time = init_time
    current_end_time = init_time
    first_event = True
    current_source = "api"
    for entry in extracted_data:
        if first_event:
            current_start_time = entry["event_time"]
            first_event = False
        if entry["name"] == "text-insert":
            if entry["eventSource"] != current_source:
                data.append({
                    "text": list(current_data["text"]),
                    "source": current_source,
                    "time": list(current_data["time"]),
                    "last_event_time": last_event_time,
                    "start_time": current_start_time,
                    "end_time": current_end_time,
                })
                current_start_time = entry["event_time"]
            if entry["pos"] == len(current_text):
                current_text += entry["text"]
                for char in entry["text"]:
                    current_data["text"].append(char)
                    current_data["time"].append(entry["event_time"])
            else:
                current_text = current_text[0:entry["pos"]] + entry["text"] + current_text[entry["pos"]:]
                for i, char in enumerate(entry["text"]):
                    insert_pos = entry["pos"] + i
                    current_data["text"].insert(insert_pos, char)
                    current_data["time"].insert(insert_pos, entry["event_time"])
            current_source = entry["eventSource"]
            current_end_time = entry["event_time"]
        if entry["name"] == "text-delete":
            current_text = current_text[0:entry["pos"]] + current_text[entry["pos"] + entry["count"]:]
            remain_count = entry["count"]
            index = entry["pos"]
            while remain_count > 0 and index < len(current_data["text"]):
                current_char = current_data["text"][index]
                if len(current_char) <= remain_count:
                    remain_count -= len(current_char)
                    del current_data["text"][index]
                    del current_data["time"][index]
                else:
                    current_data["text"][index] = current_char[remain_count:]
                    remain_count = 0
            current_end_time = entry["event_time"]
        if entry["name"] == "suggestion-open":
            data.append({
                "text": list(current_data["text"]),
                "source": current_source,
                "time": list(current_data["time"]),
                "last_event_time": last_event_time,
                "start_time": current_start_time,
                "end_time": current_end_time,
            })
    data.append({
        "text": list(current_data["text"]),
        "source": current_source,
        "time": list(current_data["time"]),
        "last_event_time": last_event_time,
        "start_time": current_start_time,
        "end_time": last_event_time,
    })

    final_data = []
    seen_texts = set()
    current_progress = 0
    prev_clean_text = None
    for d in data:
        d["text"] = "".join(d["text"])[:-1]
        d["time"] = d["time"][:-1]
        clean_text = d["text"].rstrip()
        if clean_text == prev_clean_text:
            continue
        if d["text"] not in seen_texts:
            final_data.append({k: v for k, v in d.items() if k != "time"})
            seen_texts.add(d["text"])
            prev_clean_text = clean_text
    for d in final_data:
        d["start_progress"] = current_progress
        d["end_progress"] = len(d["text"]) / len(whole_text)
        current_progress = d["end_progress"]

    final_data = [{k: v for k, v in entry.items() if k != "time"} for entry in final_data]

    return final_data


def deal_sentence(data, suggestion_data, whole_text):
    last_event_time = data[0]["last_event_time"]
    text_length = len(whole_text)
    result = []
    for d in data:
        d["source"] = d["source"][:-1]
        d["time"] = d["time"][:-1]
        d["text"] = d["text"][:-1]

    for index, d in enumerate(data):
        if index == 0 or index == len(data) - 1 or d["source"][-1] != data[index + 1]["source"][-1]:
            result.append(d)

    final_result = []
    for d in result:
        grouped_data = []
        current_source = None
        current_text_chars = []
        current_times = []
        
        for char, source, time in zip(d["text"], d["source"], d["time"]):
            if source != current_source:
                if current_source is not None:
                    grouped_data.append({
                        "source": current_source,
                        "text": "".join(current_text_chars),
                        "time": current_times,
                        "last_event_time": last_event_time,
                    })
                current_source = source
                current_text_chars = []
                current_times = []
            current_text_chars.append(char)
            current_times.append(time)
        
        if current_text_chars:
            grouped_data.append({
                "source": current_source,
                "text": "".join(current_text_chars),
                "time": current_times,
                "last_event_time": last_event_time,
            })

        final_result.append(grouped_data)

    for suggestion in sorted(suggestion_data, key=lambda x: x["time"]):
        suggestion_time = suggestion["time"]
        for data_index in range(len(final_result)):
            new_segments = []
            for entry in final_result[data_index]:
                times = entry["time"]
                for i in range(len(times) - 1):
                    if times[i] < suggestion_time < times[i + 1]:
                        idx = i + 1
                        new_segments.append({
                            "source": entry["source"],
                            "text": entry["text"][:idx],  
                            "time": entry["time"][:idx],
                            "last_event_time": last_event_time,
                        })
                        new_segments.append({
                            "source": entry["source"],
                            "text": entry["text"][idx:],
                            "time": entry["time"][idx:],
                            "last_event_time": last_event_time,
                        })
                        break
                else:
                    new_segments.append(entry)
            final_result[data_index] = new_segments

    for data_index in range(len(final_result)):
        char_count = 0
        for entry in final_result[data_index]:
            entry_length = len(entry["text"])
            entry["start_progress"] = char_count / text_length
            entry["end_progress"] = (char_count + entry_length) / text_length
            entry["start_time"] = entry["time"][0] if entry["time"] else None
            entry["end_time"] = entry["time"][-1] if entry["time"] else None
            char_count += entry_length
            
    final_result = [
        [
            entry for entry in group if entry["text"] not in ["\n", "\n\n", " ", "  ", "!", ".", "?", ","]
        ]
        for group in final_result
    ]
            
    final_result = [
        [{k: v for k, v in entry.items() if k != "time"} for entry in group]
        for group in final_result
    ]
    print(final_result)

    return final_result

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(script_dir)
    json_path = os.path.join(static_dir, "fine.json")
    session_id = load_json(json_path)
    get_data(session_id, static_dir)
    # get_sentence(session_id, static_dir)
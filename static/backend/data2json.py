import json
import datetime
import os

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

def write_json(data, file_path, session):
    # actual_session = session['session_id']+'.jsonl'
    actual_session = session+'.jsonl'
    new_file_path = os.path.join(file_path, actual_session)
    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data written to {new_file_path}")

def update_info(new_info, file_path, session):
    actual_session = session + '.jsonl'
    new_file_path = os.path.join(file_path, actual_session)
    with open(new_file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            line_num = e.lineno
            col_num = e.colno
            print(f"{new_file_path} Error at line {line_num}, column {col_num}")
            f.seek(0)
            lines = f.readlines()
            start = max(0, line_num - 5)
            end = min(len(lines), line_num + 5)
            print("Context around the error:")
            for i in range(start, end):
                print(f"{i+1}: {lines[i].rstrip()}")
            return
    data['info'] = new_info
    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    # print(f"'info' updated and written to {new_file_path}")

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
    # json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence-new")
    sentence_with_source = {"text": [], "source": [], "time": [], "last_event_time": []}
    for session in session_id:
        extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': []}
        sentence_source = []
        extra_time = []
        extra_process = []
        # file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-v1.0")
        file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/legislation_formal_study")
        # actual_session = session['session_id'] + '.jsonl'
        actual_session = session + '.jsonl'
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
        sentence_data = split_text(text, sentence_source, extra_time, extra_process)
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

def get_data(session_id, static_dir):
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-sentence")
    for session in session_id:
        extracted_data = {'init_text': [], 'init_time': [], 'json': [], 'text': [], 'info': [], 'end_time': [], 'snapshots': []}
        file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-v1.0")
        # actual_session = session['session_id'] + '.jsonl'
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
            if event_name == 'suggestion-open' and entry.get('currentSuggestions'):
                # suggestions = [s.get("trimmed", "") for s in entry["currentSuggestions"]]
                extracted_data['info'].append({
                    'id': event_num,
                    'name': event_name,
                    # 'text': suggestions,
                    'eventSource': event_source,
                    'event_time': event_time,
                    # 'count': '',
                    # 'pos': '',
                })
            if ops:
                extracted_data['snapshots'].append({
                    'text': text,
                    'eventName': event_name,
                    'eventSource': event_source,
                    'event_time': event_time,
                    'eventNum': event_num
                })
        # print(text)
        data = collect_data(extracted_data['snapshots'], text)
        extracted_data['text'].append(text)
        extracted_data['end_time'] = last_event_time
        extracted_data.pop('json', None)
        # check(extracted_data, text)
        # extracted_data.pop('snapshots', None)
        # write_json(extracted_data, json_path, session)
        # update_info(extracted_data, json_path, session)
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

def collect_data(snapshots, text):
    segments = []
    current_text = ""
    current_source = None
    current_start_time = None
    current_end_time = None
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
                    "last_event_time": current_end_time,
                })
            current_text = text
            current_source = source
            current_start_time = event_time
        else:
            current_text = text
        current_end_time = event_time
    if current_text:
        segments.append({
            "text": current_text,
            "source": current_source,
            "start_time": current_start_time,
            "end_time": current_end_time,
            "last_event_time": current_end_time,
        })
    # current_progress = 0
    # total_length = len(text)
    # for d in segments:
    #     d["start_progress"] = current_progress
    #     d["end_progress"] = len(d["text"]) / total_length
    #     current_progress = d["end_progress"]
    return segments

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

def add_fine(session_id, static_dir):
    json_path = os.path.join(static_dir, "fine-new.json")
    fine = load_json(json_path)
    data = []
    for session in session_id:
        data.append({
            "session_id": session,
            "prompt_code": "cat",
        })
    fine.extend(data)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(fine, f, ensure_ascii=False, indent=4)
    print(f"Data written to {json_path}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(script_dir)
    # json_path = os.path.join(static_dir, "fine.json")
    json_path = os.path.join(static_dir, "chi2022-coauthor-v1.0", "coauthor-v1.0")
    # session_id = load_json(json_path)
    session_id = []
    for filename in os.listdir(json_path): 
        filename = filename.removesuffix(".jsonl")
        session_id.append(filename)
        # print(filename)

    # get_sentence(session_id, static_dir)
    get_data(session_id, static_dir)
    # add_fine(session_id, static_dir)
import json
import os
import csv

def create_json(json_files):
    issue_collector = []
    for json_file in json_files:
        json_file_path = os.path.join(file_path, json_file)
        with open(json_file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                    cleaned_line = line.replace('\0', '')
                    if cleaned_line.strip():
                        json_data = json.loads(cleaned_line)
                        text_delta = json_data.get('textDelta', {})
                        if isinstance(text_delta, dict):
                            list_text_delta = list(text_delta.values())
                            count = sum(len(point) for point in list_text_delta)
                            if count != 2:
                                # print("sesion id:", json_file)
                                # print("issue line:", line)
                                issue_collector.append({
                                     "session id": json_file,
                                     "issue line": line,
                                })
                                output_file_path = os.path.join(output_path, f"issue,json")
                                with open(output_file_path, 'w', encoding='utf-8') as output_file:
                                    json.dump(issue_collector, output_file, ensure_ascii=False, indent=4)
    print("Done.")

def check_unique(issue_file, json_files):
    issue_session = set()
    count = 0
    fine_session = set()
    for session in issue_file:
        session_id = session['session id']
        issue_session.add(session_id)
    num = len(issue_session)
    for _ in json_files:
        count += 1
    print(count, num)
    print(num / count)
    json_file_set = set(json_files)
    fine_session = json_file_set - issue_session
    fine_session = list(fine_session)
    
    return fine_session

def read_csv(csv_file_path):
    """Reads the CSV file and returns a list of dictionaries with the relevant data."""
    csv_data = []
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            csv_data.append({key: str(value) for key, value in row.items()})
    return csv_data

def merge_csv_with_json(csv_data, fine_session):
    """Merges the CSV data with the fine session data based on session_id match."""
    session_data = {}
    for entry in csv_data:
        session_data[entry['session_id']] = entry  
    
    updated_fine_session = []
    for session_filename in fine_session:
        session_id = session_filename.split('.')[0]  
        if session_id in session_data:
            session_info = session_data[session_id]
            session_info['session_id'] = session_id  
            updated_fine_session.append(session_info)

    return updated_fine_session

def update_fine_json(fine_session, output_file_path):
    """Writes the updated fine session data to the output JSON file."""
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(fine_session, output_file, ensure_ascii=False, indent=4)
    print(f"Updated fine.json at {output_file_path}.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(script_dir)
    output_path = static_dir
    file_path = os.path.join(static_dir, "chi2022-coauthor-v1.0/coauthor-v1.0")
    json_files = [f for f in os.listdir(file_path) if f.endswith('.jsonl')]
    # create_json(json_files)
    issue_file_path = os.path.join(output_path, "issue.json")
    with open(issue_file_path, 'r', encoding='utf-8') as f:
        issue_file = json.load(f)
    fine_session = check_unique(issue_file, json_files)
    fine_file_path = os.path.join(output_path, f"fine.json")
    csv_path = os.path.join(output_path, "session_metadata.csv")
    with open(fine_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(fine_session, output_file, ensure_ascii=False, indent=4)
        print("Done.")

    with open(fine_file_path, 'r', encoding='utf-8') as fine_file:
        fine_session = json.load(fine_file)

    csv_data = read_csv(csv_path)

    updated_fine_session = merge_csv_with_json(csv_data, fine_session)

    update_fine_json(updated_fine_session, fine_file_path)
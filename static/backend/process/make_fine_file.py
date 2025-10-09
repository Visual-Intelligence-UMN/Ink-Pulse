import json
import os
import csv

def read_csv(csv_file_path):
    csv_data = []
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            csv_data.append({key: str(value) for key, value in row.items()})
    return csv_data

def merge_csv_with_json(csv_data, fine_session):
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
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(fine_session, output_file, ensure_ascii=False, indent=4)
    print(f"Updated fine.json at {output_file_path}.")

def main(dataset_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(os.path.dirname(script_dir))
    new_path = os.path.join(static_dir, "dataset", f"{dataset_name}")
    fine_file_path = os.path.join(new_path, f"fine.json")

    json_path = os.path.join(static_dir, "import_dataset")
    csv_path = os.path.join(json_path, f"{dataset_name}.csv")
    csv_data = read_csv(csv_path)
    fine_session = [row['session_id'] for row in csv_data]
    
    updated_fine_session = merge_csv_with_json(csv_data, fine_session)
    update_fine_json(updated_fine_session, fine_file_path)
import os
import json
# import openai
# openai.api_key = "KEY"

def read_sentence(session_path):
    with open(session_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        for setence in data:
            print(setence)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(script_dir)
    session_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0\coauthor-sentence")
    session_files = [f for f in os.listdir(session_dir) if f.endswith(".jsonl")]
    for session in session_files:
        session_path = os.path.join(session_dir, session)
        read_sentence(session_path)
        
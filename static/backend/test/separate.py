import os
import shutil
import pandas as pd
import json

def split_files_by_metadata(original_dir, argumentative_csv, creative_csv):
    argumentative_ids = set(pd.read_csv(argumentative_csv)["session_id"].astype(str))
    creative_ids = set(pd.read_csv(creative_csv)["session_id"].astype(str))
    argumentative_dir = original_dir + "-argumentative"
    creative_dir = original_dir + "-creative"

    os.makedirs(argumentative_dir, exist_ok=True)
    os.makedirs(creative_dir, exist_ok=True)
    for filename in os.listdir(original_dir):
        if not (filename.endswith(".jsonl") or filename.endswith(".json")):
            continue
        session_id = os.path.splitext(filename)[0]
        base_session_id = session_id.replace("_similarity", "")
        src_path = os.path.join(original_dir, filename)

        if base_session_id in argumentative_ids:
            dst_path = os.path.join(argumentative_dir, filename)
        elif base_session_id in creative_ids:
            dst_path = os.path.join(creative_dir, filename)
        else:
            print(f"Fail: {session_id}")
            continue

        # if session_id in argumentative_ids:
        #     dst_path = os.path.join(argumentative_dir, filename)
        # elif session_id in creative_ids:
        #     dst_path = os.path.join(creative_dir, filename)
        # else:
        #     print(f"Fail: {session_id}")
        #     continue

        shutil.copy2(src_path, dst_path)

    print("Done.")

def generate_session_json(original_dir, argumentative_csv, creative_csv):
    argumentative_ids = pd.read_csv(argumentative_csv)["session_id"].astype(str).tolist()
    creative_ids = pd.read_csv(creative_csv)["session_id"].astype(str).tolist()
    argumentative_files = [sid + "_similarity.json" for sid in argumentative_ids]
    creative_files = [sid + "_similarity.json" for sid in creative_ids]
    os.makedirs(original_dir, exist_ok=True)
    with open(os.path.join(original_dir, "argumentative.json"), "w", encoding="utf-8") as f:
        json.dump(argumentative_files, f, indent=2)
    with open(os.path.join(original_dir, "creative.json"), "w", encoding="utf-8") as f:
        json.dump(creative_files, f, indent=2)

    print(f"Generated argumentative.json ({len(argumentative_files)} files) and creative.json ({len(creative_files)} files)")

script_dir = os.path.dirname(os.path.abspath(__file__)) 
static_dir = os.path.dirname(script_dir)
split_files_by_metadata(
    original_dir=os.path.join(static_dir, "chi2022-coauthor-v1.0/w-content/similarity_results_w-content"),
    argumentative_csv=os.path.join(static_dir, "Metadata (argumentative).csv"),
    creative_csv=os.path.join(static_dir, "Metadata (creative).csv"),
)
# generate_session_json(
#     original_dir=static_dir,
#     argumentative_csv=os.path.join(static_dir, "Metadata (argumentative).csv"),
#     creative_csv=os.path.join(static_dir, "Metadata (creative).csv")
# )
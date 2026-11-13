
import os
import json
import time
import numpy as np
import pandas as pd
import boto3
from openai import AzureOpenAI
from openpyxl import load_workbook

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint="https://webarena-agent.openai.azure.com",
    api_version="2024-02-01",
    timeout=300.0
)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

dataset_name = "argumentative"

script_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))

new_json_path = os.path.join(static_dir, "dataset", dataset_name, "json")
new_segment_path = os.path.join(static_dir, "dataset", dataset_name, "segment")

output_path = os.path.join(script_dir, "semantic_change_robustness.xlsx")

N_RUNS = 1


def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_sentences(file_path):
    data = load_json(file_path)
    return [
        {
            "text": entry["text"],
            "source": entry.get("source", "unknown"),
            "start_progress": entry["start_progress"],
            "end_progress": entry["end_progress"],
            "start_time": entry["start_time"],
            "end_time": entry["end_time"],
            "last_event_time": entry["last_event_time"]
        }
        for entry in data if "text" in entry
    ]


def get_openai_embedding(text, retries=3):
    for attempt in range(retries):
        try:
            response = bedrock.invoke_model(
                modelId="us.cohere.embed-v4:0",
                body=json.dumps({
                    "texts": [text],
                    "input_type": "search_document",
                    "embedding_types": ["float"]
                }),
                accept="application/json",
                contentType="application/json"
            )

            result = json.loads(response["body"].read())
            return np.array(result["embeddings"]["float"][0])

        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  Embedding failed (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def compute_vector_norm(residual_vector):
    return float(np.linalg.norm(residual_vector))


def analyze_residuals(sentences, check):
    delta = 5
    first_is_empty = (
        not check["init_text"]
        or check["init_text"][0].strip() == ""
    )

    for i, sentence in enumerate(sentences):
        text = sentence.get("text", "").strip()

        if first_is_empty:
            if i == 0:
                sentence["residual_vector"] = 0.0
                continue
            elif i == 1:
                sentence["embedding"] = get_openai_embedding(text)
                sentence["residual_vector"] = 1.0
                continue

        if i == 0:
            sentence["embedding"] = get_openai_embedding(text)
            sentence["residual_vector"] = 0.0
        else:
            prev_text = sentences[i - 1]["text"]
            delta_chars = (
                sum(1 for a, b in zip(prev_text, text) if a != b)
                + abs(len(prev_text) - len(text))
            )
            sentence["embedding"] = get_openai_embedding(text)

            if delta_chars <= delta:
                sentence["residual_vector"] = 0.0
            else:
                prev_embedding = sentences[i - 1]["embedding"]
                residual_vector = sentence["embedding"] - prev_embedding
                sentence["residual_vector"] = compute_vector_norm(residual_vector)

    norms = [s["residual_vector"] for s in sentences]
    min_norm = min(norms)
    max_norm = max(norms)
    norm_range = max_norm - min_norm if max_norm != min_norm else 1.0

    for sentence in sentences:
        sentence["residual_vector_norm"] = (
            sentence["residual_vector"] - min_norm
        ) / norm_range

    return sentences


def get_col_order(row):
    fixed = ["session_id", "run"]
    seg_cols = sorted(
        [k for k in row.keys() if k.startswith("seg_")],
        key=lambda x: int(x.split("_")[1])
    )
    return fixed + seg_cols


def init_excel(output_path, norm_row, raw_row):
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame([norm_row])[get_col_order(norm_row)].to_excel(
            writer, sheet_name="Raw Normalized", index=False
        )
        pd.DataFrame([raw_row])[get_col_order(raw_row)].to_excel(
            writer, sheet_name="Raw Distance", index=False
        )
        pd.DataFrame().to_excel(
            writer, sheet_name="Summary Normalized", index=False
        )
        pd.DataFrame().to_excel(
            writer, sheet_name="Summary Distance", index=False
        )


def append_to_excel(output_path, norm_row, raw_row):
    wb = load_workbook(output_path)

    for sheet_name, row in [
        ("Raw Normalized", norm_row),
        ("Raw Distance", raw_row)
    ]:
        ws = wb[sheet_name]
        col_order = get_col_order(row)
        ws.append([row[col] for col in col_order])

    wb.save(output_path)


def write_summary_sheets(output_path, normalized_df, raw_distance_df):
    wb = load_workbook(output_path)

    for sheet_name, summary in [
        ("Summary Normalized", create_summary(normalized_df)),
        ("Summary Distance", create_summary(raw_distance_df))
    ]:
        ws = wb[sheet_name]
        ws.delete_rows(1, ws.max_row)
        ws.append(list(summary.columns))

        for _, row in summary.iterrows():
            ws.append(list(row))

    wb.save(output_path)


def create_summary(df):
    seg_cols = [c for c in df.columns if c.startswith("seg_")]
    summary_rows = []

    for session_id, group in df.groupby("session_id"):
        row = {"session_id": session_id}

        for col in seg_cols:
            row[f"{col}_mean"] = group[col].mean()
            row[f"{col}_std"] = group[col].std()
            row[f"{col}_min"] = group[col].min()
            row[f"{col}_max"] = group[col].max()

        summary_rows.append(row)

    return pd.DataFrame(summary_rows)


def load_done_from_excel(output_path):
    done = set()
    normalized_rows = []
    raw_distance_rows = []

    if not os.path.exists(output_path):
        return done, normalized_rows, raw_distance_rows

    try:
        norm_df = pd.read_excel(
            output_path, sheet_name="Raw Normalized"
        )
        raw_df = pd.read_excel(
            output_path, sheet_name="Raw Distance"
        )

        normalized_rows = norm_df.to_dict("records")
        raw_distance_rows = raw_df.to_dict("records")

        for row in normalized_rows:
            done.add((str(row["session_id"]), int(row["run"])))

        print(f"Resuming: {len(done)} runs already in Excel.")

    except Exception as e:
        print(f"Could not read existing Excel ({e}), starting fresh.")

    return done, normalized_rows, raw_distance_rows


done, normalized_rows, raw_distance_rows = load_done_from_excel(
    output_path
)

for file_name in sorted(os.listdir(new_segment_path)):
    if not file_name.endswith(".json"):
        continue

    session_id = os.path.splitext(file_name)[0]
    file_path = os.path.join(new_segment_path, file_name)
    check_file = os.path.join(new_json_path, session_id + ".json")

    if not os.path.exists(check_file):
        print(f"Skipping {session_id} - no check file found")
        continue

    check = load_json(check_file)
    print(f"Processing {session_id}...")

    for run in range(N_RUNS):
        key = (session_id, run + 1)

        if key in done:
            print(f"  Run {run + 1} already in Excel, skipping")
            continue

        fresh_sentences = read_sentences(file_path)
        results = analyze_residuals(fresh_sentences, check)

        normalized_row = {
            "session_id": session_id,
            "run": run + 1
        }
        raw_row = {
            "session_id": session_id,
            "run": run + 1
        }

        for seg_idx, s in enumerate(results):
            normalized_row[f"seg_{seg_idx}"] = float(
                s["residual_vector_norm"]
            )
            raw_row[f"seg_{seg_idx}"] = float(
                s["residual_vector"]
            )

        normalized_rows.append(normalized_row)
        raw_distance_rows.append(raw_row)
        done.add(key)

        if not os.path.exists(output_path):
            init_excel(output_path, normalized_row, raw_row)
        else:
            append_to_excel(output_path, normalized_row, raw_row)

        print(f"  Run {run + 1} saved to Excel ✓")


normalized_df = pd.DataFrame(normalized_rows)
raw_distance_df = pd.DataFrame(raw_distance_rows)

write_summary_sheets(
    output_path,
    normalized_df,
    raw_distance_df
)

print("\nDone!")
print(f"Saved to: {output_path}")
print(f"Total sessions: {normalized_df['session_id'].nunique()}")
print(f"Total rows: {len(normalized_df)}")

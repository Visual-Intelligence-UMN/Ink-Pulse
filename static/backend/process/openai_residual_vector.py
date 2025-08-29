import os
import json
import numpy as np
import openai

if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("Please set OPENAI_API_KEY")

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

def read_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        sentences = [
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
    return sentences

def get_openai_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(input=[text], model=model)
    return np.array(response.data[0].embedding)

def compute_vector_norm(residual_vector):
    return float(np.linalg.norm(residual_vector))

def analyze_residuals(sentences, check):
    results = []
    delta = 5
    first_is_empty = not check["init_text"] or check["init_text"][0].strip() == ""

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
            delta_chars = sum(1 for a, b in zip(prev_text, text) if a != b) + abs(len(prev_text) - len(text))
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
        raw_norm = sentence["residual_vector"]
        normalized = (raw_norm - min_norm) / norm_range
        sentence["residual_vector_norm"] = normalized
    for sentence in sentences:
        result_entry = {
            "sentence": sentence["text"],
            "source": sentence["source"],
            "start_progress": sentence["start_progress"],
            "end_progress": sentence["end_progress"],
            "start_time": sentence["start_time"],
            "end_time": sentence["end_time"],
            "last_event_time": sentence["last_event_time"],
            "residual_vector": sentence["residual_vector"],
            "residual_vector_norm": sentence["residual_vector_norm"],
        }
        results.append(result_entry)
    return results

def convert_types(obj):
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def save_results_to_json(results, session_id, output_dir):
    output_file = os.path.join(output_dir, f"{session_id}_similarity.json")
    results_converted = [
        {k: convert_types(v) for k, v in entry.items()}
        for entry in results
    ]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results_converted, f, indent=4, ensure_ascii=False)
    print(f"Similarity results saved to {output_file}")

def main(dataset_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(os.path.dirname(script_dir))
    session_dir = os.path.join(static_dir, f"dataset/{dataset_name}/coauthor-sentence")
    check_dir = os.path.join(static_dir, f"dataset/{dataset_name}/coauthor-json")

    output_dir = os.path.join(static_dir, "dataset", f"{dataset_name}", "similarity_results")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Create foler similarity_results in {output_dir}")
    else:
        print(f"Folder similarity_results already exist in {output_dir}.")
    for file_name in os.listdir(session_dir):
        if file_name.endswith(".jsonl"):
            file_path = os.path.join(session_dir, file_name)
            session_id = os.path.splitext(file_name)[0]
            sentences = read_sentences(file_path)
            check_file = os.path.join(check_dir, session_id + ".jsonl")
            check = load_json(check_file)
            results = analyze_residuals(sentences, check)
            save_results_to_json(results, session_id, output_dir)

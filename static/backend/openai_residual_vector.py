import os
import json
import numpy as np
import openai

if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("Please set OPENAI_API_KEY")

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


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


def compute_char_norm(text_current, text_prev, vector_norm):
    char_diff = max(1, len(text_current) - len(text_prev))
    return vector_norm / char_diff


def analyze_residuals(sentences):
    results = []
    for i, sentence in enumerate(sentences):
        sentence["embedding"] = get_openai_embedding(sentence["text"])
        if i == 0:
            sentence["residual_vector_norm"] = 1.0
            sentence["residual_vector_char_norm"] = 1.0
        else:
            prev_embedding = sentences[i - 1]["embedding"]
            curr_embedding = sentence["embedding"]
            residual_vector = curr_embedding - prev_embedding
            residual_vector_norm = compute_vector_norm(residual_vector)

            prev_text = sentences[i - 1]["text"]
            curr_text = sentence["text"]
            residual_vector_char_norm = compute_char_norm(curr_text, prev_text, residual_vector_norm)

            sentence["residual_vector_norm"] = residual_vector_norm
            sentence["residual_vector_char_norm"] = residual_vector_char_norm

        result_entry = {
            "sentence": sentence["text"],
            "source": sentence["source"],
            "start_progress": sentence["start_progress"],
            "end_progress": sentence["end_progress"],
            "start_time": sentence["start_time"],
            "end_time": sentence["end_time"],
            "last_event_time": sentence["last_event_time"],
            "residual_vector_norm": sentence.get("residual_vector_norm"),
            "residual_vector_char_norm": sentence.get("residual_vector_char_norm")
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

    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)

    session_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "coauthor-sentence")
    output_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "similarity_results")
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(session_dir):
        if file_name.endswith(".jsonl"):
            file_path = os.path.join(session_dir, file_name)
            session_id = os.path.splitext(file_name)[0]

            sentences = read_sentences(file_path)
            results = analyze_residuals(sentences)

            save_results_to_json(results, session_id, output_dir)

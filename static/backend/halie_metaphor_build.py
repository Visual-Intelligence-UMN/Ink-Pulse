"""
Phase 1: Build segment_results + json + session.csv for halie_metaphor dataset.

Each segment = one metaphor sentence.
Uses event_blocks.csv for structured data + coauthor-json for raw events.
Calls OpenAI text-embedding-3-small for semantic change computation.

Usage:
    # Process all sessions in event_blocks.csv:
    OPENAI_API_KEY=sk-... python halie_metaphor_build.py

    # Process only the first N sessions (batch mode):
    OPENAI_API_KEY=sk-... python halie_metaphor_build.py --batch 10

    # Process N sessions starting from offset K (for resuming):
    OPENAI_API_KEY=sk-... python halie_metaphor_build.py --batch 10 --offset 10
"""

import argparse
import csv
import json
import os
import numpy as np
import openai

DATASET = "halie_metaphor"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.dirname(SCRIPT_DIR)
EVENT_BLOCKS_CSV = os.path.join(STATIC_DIR, "import_dataset", "halie_metaphor_event_blocks.csv")
COAUTHOR_JSON_DIR = os.path.join(STATIC_DIR, "dataset", DATASET, "coauthor-json")
SEGMENT_OUT_DIR = os.path.join(STATIC_DIR, "dataset", DATASET, "segment_results")
JSON_OUT_DIR = os.path.join(STATIC_DIR, "dataset", DATASET, "json")
SESSION_CSV_PATH = os.path.join(STATIC_DIR, "dataset", DATASET, "session.csv")

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def get_embedding(text):
    resp = client.embeddings.create(input=[text], model="text-embedding-3-small")
    return np.array(resp.data[0].embedding)


def load_event_blocks(target_sessions=None):
    """Load event_blocks.csv, grouped by session_id.
    
    If target_sessions is provided (list of session IDs), only those are loaded.
    Otherwise all sessions are loaded.
    """
    sessions = {}
    with open(EVENT_BLOCKS_CSV) as f:
        for row in csv.DictReader(f):
            sid = row["session_id"]
            if target_sessions is not None and sid not in target_sessions:
                continue
            sessions.setdefault(sid, []).append(row)
    for sid in sessions:
        sessions[sid].sort(key=lambda r: int(r["order_id"]))
    return sessions


def get_all_session_ids():
    """Return all unique session IDs from event_blocks.csv in order of first appearance."""
    seen = []
    with open(EVENT_BLOCKS_CSV) as f:
        for row in csv.DictReader(f):
            sid = row["session_id"]
            if sid not in seen:
                seen.append(sid)
    return seen


def load_existing_session_csv():
    """Load already-processed sessions from session.csv."""
    if not os.path.exists(SESSION_CSV_PATH):
        return {}
    existing = {}
    with open(SESSION_CSV_PATH) as f:
        for row in csv.DictReader(f):
            existing[row["session_id"]] = row
    return existing


def safe_float(val, default=0.0):
    try:
        return float(val) if val.strip() else default
    except (ValueError, AttributeError):
        return default


def build_segment_results(metaphors):
    """Convert a list of metaphor rows into segment_results format."""
    n = len(metaphors)
    if n == 0:
        return []

    embeddings = []
    for m in metaphors:
        text = m["final_sentence"].strip()
        if text:
            embeddings.append(get_embedding(text))
        else:
            embeddings.append(None)

    raw_norms = []
    for i, emb in enumerate(embeddings):
        if i == 0 or emb is None:
            raw_norms.append(0.0)
        elif embeddings[i - 1] is None:
            raw_norms.append(1.0)
        else:
            residual = emb - embeddings[i - 1]
            raw_norms.append(float(np.linalg.norm(residual)))
    mn, mx = min(raw_norms), max(raw_norms)
    rng = mx - mn if mx != mn else 1.0
    norm_values = [(v - mn) / rng for v in raw_norms]

    cumulative_time = 0.0
    segments = []
    for i, m in enumerate(metaphors):
        elapsed_sec = safe_float(m["elapsed_time"]) * 60
        start_t = cumulative_time
        end_t = cumulative_time + elapsed_sec
        cumulative_time = end_t

        acceptance = safe_float(m["acceptance"], default=-1)
        if acceptance < 0:
            source = "user"
        elif acceptance >= 80:
            source = "api"
        else:
            source = "user"

        segments.append({
            "sentence": len(m["final_sentence"]) / 3000,
            "source": source,
            "start_progress": i / n,
            "end_progress": (i + 1) / n,
            "start_time": round(start_t, 1),
            "end_time": round(end_t, 1),
            "last_event_time": round(end_t, 1),
            "residual_vector_norm": round(norm_values[i], 6),
            "score": None,
            "acceptance": safe_float(m["acceptance"], default=-1),
            "num_queries": int(m["num_queries"]),
            "apt": safe_float(m["apt"], default=-1),
            "specific": safe_float(m["specific"], default=-1),
            "imageable": safe_float(m["imageable"], default=-1),
            "final_sentence": m["final_sentence"],
            "model_completion": m["model_completion"],
            "model": m["model"],
        })

    return segments


def build_json_file(sid):
    """Read coauthor-json and reformat into the standard json/ format."""
    src = os.path.join(COAUTHOR_JSON_DIR, sid + ".jsonl")
    with open(src) as f:
        data = json.load(f)

    init_text = data.get("init_text", [""])[0] if isinstance(data.get("init_text"), list) else ""
    init_time = data.get("init_time", [""])[0] if isinstance(data.get("init_time"), list) else ""
    end_time = data.get("end_time", "")
    text_val = data.get("text", [""])[0] if isinstance(data.get("text"), list) else ""
    text_len = len(text_val) if isinstance(text_val, str) else text_val

    actions = []
    for entry in data.get("info", []):
        action = {
            "name": entry.get("name", ""),
            "text": entry.get("text", ""),
            "eventSource": entry.get("eventSource", "user"),
            "event_time": entry.get("event_time", ""),
            "pos": entry.get("pos", 0),
        }
        if "count" in entry:
            action["count"] = entry["count"]
        actions.append(action)

    char_count = len(init_text)
    max_char_count = char_count
    for a in actions:
        if a["name"] == "text-insert":
            char_count += len(a.get("text", ""))
        elif a["name"] == "text-delete":
            char_count -= a.get("count", len(a.get("text", "")))
            char_count = max(char_count, 0)
        max_char_count = max(max_char_count, char_count)

    total_len = max(max_char_count, 1)
    char_count = len(init_text)
    for a in actions:
        if a["name"] == "text-insert":
            char_count += len(a.get("text", ""))
        elif a["name"] == "text-delete":
            char_count -= a.get("count", len(a.get("text", "")))
            char_count = max(char_count, 0)
        a["progress"] = round(char_count / total_len, 4)

    return {
        "init_text": init_text,
        "init_time": init_time,
        "text": total_len,
        "actions": actions,
        "end_time": end_time,
    }


def build_session_csv(session_data, segments_map):
    """Generate session.csv with per-session summary stats."""
    rows = []
    for sid, metaphors in session_data.items():
        segs = segments_map.get(sid, [])
        total_api = sum(1 for s in segs if s["source"] == "api")
        ai_ratio = total_api / len(segs) if segs else 0
        sem_sum = sum(s["residual_vector_norm"] for s in segs)

        # avg_overall: mean of non-empty 'overall' values across sentences
        # Note: CSV column is "overall " (trailing space); strip keys when loading if needed
        overall_vals = [safe_float(m.get("overall", m.get("overall ", ""))) for m in metaphors if m.get("overall", m.get("overall ", "")).strip()]
        avg_overall = round(sum(overall_vals) / len(overall_vals), 4) if overall_vals else ""

        rows.append({
            "session_id": sid,
            "judge_score": round(float(avg_overall) * 10, 4) if avg_overall != "" else "",
            "length": len(metaphors),
            "AI_ratio": round(ai_ratio, 4),
            "sum_semantic_score": round(sem_sum, 4),
            "prompt_code": metaphors[0].get("prompt", "metaphor"),
            "avg_overall": avg_overall,
        })

    with open(SESSION_CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["session_id", "judge_score", "length", "AI_ratio", "sum_semantic_score", "prompt_code", "avg_overall"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  session.csv → {len(rows)} sessions")


def main():
    parser = argparse.ArgumentParser(description="Build halie_metaphor dataset files.")
    parser.add_argument("--batch", type=int, default=None,
                        help="Number of sessions to process in this run (default: all)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip the first N sessions (default: 0)")
    parser.add_argument("--skip-done", action="store_true",
                        help="Skip sessions that already have segment_results files")
    args = parser.parse_args()

    os.makedirs(SEGMENT_OUT_DIR, exist_ok=True)
    os.makedirs(JSON_OUT_DIR, exist_ok=True)

    all_ids = get_all_session_ids()
    print(f"Total sessions in event_blocks.csv: {len(all_ids)}")

    # Apply offset
    all_ids = all_ids[args.offset:]

    # Skip already-done sessions if requested
    if args.skip_done:
        before = len(all_ids)
        all_ids = [sid for sid in all_ids
                   if not os.path.exists(os.path.join(SEGMENT_OUT_DIR, sid + ".json"))]
        print(f"  Skipping {before - len(all_ids)} already-processed sessions")

    # Apply batch limit
    if args.batch is not None:
        all_ids = all_ids[:args.batch]

    if not all_ids:
        print("No sessions to process.")
        return

    print(f"Processing {len(all_ids)} sessions (offset={args.offset}, batch={args.batch})")

    session_data = load_event_blocks(target_sessions=set(all_ids))
    # Preserve the order from all_ids
    ordered_session_data = {sid: session_data[sid] for sid in all_ids if sid in session_data}
    print(f"  Loaded {len(ordered_session_data)} sessions from event_blocks.csv")

    segments_map = {}
    for i, (sid, metaphors) in enumerate(ordered_session_data.items(), 1):
        print(f"\n[{i}/{len(ordered_session_data)}] Processing {sid[:8]}... ({len(metaphors)} metaphors)")

        print("  Computing embeddings...")
        segs = build_segment_results(metaphors)
        segments_map[sid] = segs

        out_path = os.path.join(SEGMENT_OUT_DIR, sid + ".json")
        with open(out_path, "w") as f:
            json.dump(segs, f, indent=2, ensure_ascii=False)
        print(f"  segment_results → {len(segs)} segments")

        print("  Building json/...")
        json_data = build_json_file(sid)
        json_path = os.path.join(JSON_OUT_DIR, sid + ".json")
        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"  json → {len(json_data['actions'])} actions")

    # Merge with existing session.csv entries from previous batches
    print("\nUpdating session.csv...")
    existing = load_existing_session_csv()
    existing.update({sid: None for sid in segments_map})  # placeholder, will rebuild below

    # Rebuild session.csv: existing rows + new rows
    all_segment_files = [f for f in os.listdir(SEGMENT_OUT_DIR) if f.endswith(".json")]
    full_session_data = load_event_blocks()  # load all for CSV rebuild
    full_segments_map = {}
    for fname in all_segment_files:
        sid = fname.replace(".json", "")
        if sid in segments_map:
            full_segments_map[sid] = segments_map[sid]
        else:
            with open(os.path.join(SEGMENT_OUT_DIR, fname)) as f:
                full_segments_map[sid] = json.load(f)

    build_session_csv(
        {sid: full_session_data.get(sid, []) for sid in full_segments_map},
        full_segments_map
    )

    done_count = len(all_segment_files)
    remaining = len(get_all_session_ids()) - done_count
    print(f"\nDone! Total processed so far: {done_count}/80  (remaining: {remaining})")
    if remaining > 0 and args.batch:
        next_offset = args.offset + len(ordered_session_data)
        print(f"  Next run: python halie_metaphor_build.py --batch {args.batch} --offset {next_offset}")
        print(f"  Or resume skipping done: python halie_metaphor_build.py --batch {args.batch} --skip-done")


if __name__ == "__main__":
    main()

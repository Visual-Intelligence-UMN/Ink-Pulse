#!/usr/bin/env python3
"""
halie_summarization_build.py

Builds InkPulse-compatible json/ and segment_results/ files
from HALIE Text Summarization data.

Usage:
  python halie_summarization_build.py                  # process all
  python halie_summarization_build.py --batch 3        # first 3
  python halie_summarization_build.py --batch 10 --offset 3
  python halie_summarization_build.py --skip-done      # resume
"""

import os
import json
import csv
import zipfile
import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher

# ─── Paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(SCRIPT_DIR, "..", "dataset", "halie_summarization")

LOGS_ZIP       = os.path.expanduser("~/Downloads/summarization_logs.zip")
EVENT_BLOCKS   = os.path.expanduser("~/Downloads/summarization_event_blocks.csv")

JSON_OUT_DIR    = os.path.join(DATASET_DIR, "json")
SEGMENT_OUT_DIR = os.path.join(DATASET_DIR, "segment_results")
SESSION_CSV     = os.path.join(DATASET_DIR, "session.csv")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def ms_to_iso(ts_ms: int) -> str:
    """Convert Unix millisecond timestamp to ISO-like string (UTC)."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def quill_insert_text(ops: list) -> str:
    """Extract concatenated inserted text from Quill delta ops."""
    return "".join(op.get("insert", "") for op in ops if "insert" in op and isinstance(op.get("insert"), str))


def quill_delete_count(ops: list) -> int:
    """Sum all delete values from Quill delta ops."""
    return sum(op.get("delete", 0) for op in ops if "delete" in op)


def normalized_edit_distance(a: str, b: str) -> float:
    """Return normalized edit distance [0, 1] between two strings."""
    if not a and not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    return round(1.0 - ratio, 4)


# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_event_blocks() -> dict:
    """Load summarization_event_blocks.csv grouped by session_id, sorted by order_id."""
    data: dict[str, list] = {}
    with open(EVENT_BLOCKS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = row["session_id"]
            data.setdefault(sid, []).append(row)
    for sid in data:
        data[sid].sort(key=lambda r: int(r["order_id"]))
    return data


def parse_events(session_id: str) -> list | None:
    """Load and parse JSONL events for a session from the zip."""
    with zipfile.ZipFile(LOGS_ZIP) as z:
        try:
            with z.open(f"logs/{session_id}.jsonl") as f:
                lines = f.read().decode("utf-8").strip().split("\n")
        except KeyError:
            return None
    return [json.loads(line) for line in lines if line.strip()]


# ─── Per-Document Segment Extraction ──────────────────────────────────────────

def extract_doc_segments(events: list) -> list:
    """
    Split event list into per-document editing segments.

    Each document follows this pattern in the event log:
        api text-insert  ← loads AI summary into editor (user is on reading screen)
        button-next      ← user moves to editing screen
        [user edits...]  ← user inserts/deletes characters in the summary
        button-next      ← user submits edited summary
        summary-add      ← system shows original document for review
        button-next      ← user moves to next document

    Returns a list of dicts:
        init_text     : str   – AI-generated summary
        init_ts       : int   – Unix ms of the api INSERT event
        edit_start_ts : int   – Unix ms of first button-next (reading→editing)
        edit_end_ts   : int   – Unix ms of second button-next (submit)
        actions       : list  – raw user edit dicts {name, text/count, ts}
        document_text : str   – original news article (from summary-add event)
    """
    segments = []
    i = 0
    n = len(events)

    while i < n:
        ev = events[i]

        # Look for an api text-insert that loads a non-trivial summary
        if ev.get("eventName") == "text-insert" and ev.get("eventSource") == "api":
            ops = ev.get("textDelta", {})
            if isinstance(ops, dict):
                ops = ops.get("ops", [])
            else:
                ops = []
            api_text = quill_insert_text(ops)

            if len(api_text) < 5:
                i += 1
                continue

            init_ts = int(ev["eventTimestamp"])

            # Advance to the first button-next (end of reading phase)
            j = i + 1
            while j < n and events[j].get("eventName") != "button-next":
                j += 1
            if j >= n:
                break
            edit_start_ts = int(events[j]["eventTimestamp"])
            j += 1  # skip this button-next

            # Collect user edit events until the next button-next (submit)
            user_actions = []
            while j < n and events[j].get("eventName") != "button-next":
                ev2 = events[j]
                if ev2.get("eventSource") == "user" and ev2.get("eventName") in ("text-insert", "text-delete"):
                    ops2 = ev2.get("textDelta", {})
                    if isinstance(ops2, dict):
                        ops2 = ops2.get("ops", [])
                    else:
                        ops2 = []

                    if ev2["eventName"] == "text-insert":
                        text = quill_insert_text(ops2)
                        if text:
                            user_actions.append({
                                "name": "text-insert",
                                "text": text,
                                "ts": int(ev2["eventTimestamp"]),
                            })
                    else:
                        count = quill_delete_count(ops2)
                        if count > 0:
                            user_actions.append({
                                "name": "text-delete",
                                "count": count,
                                "ts": int(ev2["eventTimestamp"]),
                            })
                j += 1

            edit_end_ts = int(events[j]["eventTimestamp"]) if j < n else (edit_start_ts + 1000)

            # Look for a summary-add event after the submit button-next to get the original document text.
            # The summary-add textDelta is a plain string starting with "Document: <article text>".
            document_text = ""
            k = j + 1
            while k < n and events[k].get("eventName") != "text-insert":
                if events[k].get("eventName") == "summary-add":
                    raw = events[k].get("textDelta", "")
                    if isinstance(raw, str):
                        # Strip the "Document: " prefix that HALIE prepends
                        prefix = "Document: "
                        document_text = raw[len(prefix):] if raw.startswith(prefix) else raw
                    break
                k += 1

            segments.append({
                "init_text": api_text,
                "init_ts": init_ts,
                "edit_start_ts": edit_start_ts,
                "edit_end_ts": edit_end_ts,
                "actions": user_actions,
                "document_text": document_text,
            })

            i = j  # continue from after the submit button-next
        else:
            i += 1

    return segments


# ─── Output Builders ──────────────────────────────────────────────────────────

def build_json_file(session_id: str, doc_segments: list) -> dict:
    """
    Build the json/*.json timeline file consumed by the Line Chart.

    All document editing events are merged into one flat action list,
    with api DELETE+INSERT actions separating each document switch.
    Each action includes event_time (ISO string) and progress.
    """
    if not doc_segments:
        return {"init_text": "", "init_time": "1970-01-01 00:00:00",
                "text": 1, "actions": [], "end_time": "1970-01-01 00:00:00"}

    session_start_ms = doc_segments[0]["init_ts"]

    # First pass: compute max char count across entire session
    char_count = 0
    max_char_count = 0
    for seg in doc_segments:
        char_count = len(seg["init_text"])         # api loads new summary (replaces old)
        max_char_count = max(max_char_count, char_count)
        for a in seg["actions"]:
            if a["name"] == "text-insert":
                char_count += len(a["text"])
            elif a["name"] == "text-delete":
                char_count = max(char_count - a["count"], 0)
            max_char_count = max(max_char_count, char_count)

    total_len = max(max_char_count, 1)

    # Second pass: build action list
    all_actions = []
    char_count = 0

    for seg in doc_segments:
        init_iso = ms_to_iso(seg["init_ts"])

        # If there was a previous document, emit a clear (api DELETE)
        if char_count > 0:
            all_actions.append({
                "name": "text-delete",
                "text": "x" * char_count,   # placeholder – length is what matters
                "count": char_count,
                "eventSource": "api",
                "event_time": init_iso,
                "pos": 0,
                "progress": 0.0,
            })
            char_count = 0

        # Emit the api INSERT (AI summary load)
        char_count = len(seg["init_text"])
        all_actions.append({
            "name": "text-insert",
            "text": seg["init_text"],
            "eventSource": "api",
            "event_time": init_iso,
            "pos": 0,
            "progress": round(char_count / total_len, 4),
        })

        # User edit events
        for a in seg["actions"]:
            event_iso = ms_to_iso(a["ts"])
            if a["name"] == "text-insert":
                char_count += len(a["text"])
                all_actions.append({
                    "name": "text-insert",
                    "text": a["text"],
                    "eventSource": "user",
                    "event_time": event_iso,
                    "pos": 0,
                    "progress": round(char_count / total_len, 4),
                })
            elif a["name"] == "text-delete":
                char_count = max(char_count - a["count"], 0)
                all_actions.append({
                    "name": "text-delete",
                    "text": "x" * a["count"],   # placeholder
                    "count": a["count"],
                    "eventSource": "user",
                    "event_time": event_iso,
                    "pos": 0,
                    "progress": round(char_count / total_len, 4),
                })

    last_seg = doc_segments[-1]
    return {
        "init_text": "",
        "init_time": ms_to_iso(session_start_ms),
        "text": total_len,
        "actions": all_actions,
        "end_time": ms_to_iso(last_seg["edit_end_ts"]),
    }


def build_segment_results(doc_segments: list, blocks: list) -> list:
    """
    Build segment_results entries (one per document).

    Includes standard InkPulse fields plus custom HALIE-summarization fields.
    residual_vector_norm = normalized edit distance between consecutive edited summaries.
    """
    if not doc_segments or not blocks:
        return []

    session_start_ms = doc_segments[0]["init_ts"]
    results = []
    prev_edited = None

    for i, (seg, block) in enumerate(zip(doc_segments, blocks)):
        start_time_min = (seg["edit_start_ts"] - session_start_ms) / 1000 / 60
        end_time_min   = (seg["edit_end_ts"]   - session_start_ms) / 1000 / 60

        original_summary = block.get("original_summary", "")
        edited_summary   = block.get("edited_summary", "")
        edit_distance    = int(block.get("distance", 0))

        sem_change = normalized_edit_distance(prev_edited, edited_summary) if prev_edited is not None else 0.0

        results.append({
            # ── Standard InkPulse fields ──────────────────────────
            "sentence": edited_summary,
            "source": "user",
            "start_time":     round(start_time_min, 4),
            "end_time":       round(end_time_min, 4),
            "start_progress": round(i / len(blocks), 4),
            "end_progress":   round((i + 1) / len(blocks), 4),
            "residual_vector_norm": sem_change,
            # ── Custom HALIE-summarization fields ─────────────────
            "document_text":    seg.get("document_text", ""),
            "original_summary": original_summary,
            "edited_summary":   edited_summary,
            "edit_distance":    edit_distance,
            "original_consistency": block.get("original_consistency", ""),
            "original_coherency":   block.get("original_coherency", ""),
            "original_relevance":   block.get("original_relevance", ""),
            "edited_consistency": block.get("edited_consistency", ""),
            "edited_coherency":   block.get("edited_coherency", ""),
            "edited_relevance":   block.get("edited_relevance", ""),
            "model": block.get("model", ""),
            "doc_idx": i,
        })

        prev_edited = edited_summary

    return results


def build_session_csv(session_ids: list, segments_map: dict):
    """Merge new session rows into session.csv (preserves existing rows)."""
    new_rows: dict[str, dict] = {}
    for sid in session_ids:
        segs = segments_map.get(sid, [])
        if not segs:
            continue
        total_dist = sum(s.get("edit_distance", 0) for s in segs)
        n = len(segs)
        avg_dist = round(total_dist / n, 2) if n else 0

        def bool_val(s: str) -> int:
            return 1 if str(s).strip().lower() in ("true", "1", "yes") else 0

        quality_improvements = sum(
            1 for s in segs
            if (bool_val(s.get("edited_consistency", "")) > bool_val(s.get("original_consistency", "")))
            or (bool_val(s.get("edited_coherency", "")) > bool_val(s.get("original_coherency", "")))
            or (bool_val(s.get("edited_relevance", "")) > bool_val(s.get("original_relevance", "")))
        )

        new_rows[sid] = {
            "session_id": sid,
            "num_docs": n,
            "avg_edit_distance": avg_dist,
            "total_edit_distance": total_dist,
            "quality_improvements": quality_improvements,
            "judge_score": avg_dist,   # import-groups.ts reads col[1] as judge_score
        }

    # Merge with existing
    existing: dict[str, dict] = {}
    if os.path.exists(SESSION_CSV):
        with open(SESSION_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing[row["session_id"]] = row
    existing.update(new_rows)

    fieldnames = ["session_id", "num_docs", "avg_edit_distance",
                  "total_edit_distance", "quality_improvements", "judge_score"]
    with open(SESSION_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing.values():
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"  session.csv → {len(existing)} rows")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build halie_summarization dataset files.")
    parser.add_argument("--batch",     type=int, default=None, help="Number of sessions per run")
    parser.add_argument("--offset",    type=int, default=0,    help="Skip first N sessions")
    parser.add_argument("--skip-done", action="store_true",    help="Skip already-processed sessions")
    args = parser.parse_args()

    os.makedirs(JSON_OUT_DIR,    exist_ok=True)
    os.makedirs(SEGMENT_OUT_DIR, exist_ok=True)

    event_blocks = load_event_blocks()
    all_ids = sorted(event_blocks.keys())
    print(f"Total sessions with event_blocks: {len(all_ids)}")

    all_ids = all_ids[args.offset:]

    if args.skip_done:
        before = len(all_ids)
        all_ids = [sid for sid in all_ids
                   if not os.path.exists(os.path.join(SEGMENT_OUT_DIR, sid + ".json"))]
        print(f"  Skipping {before - len(all_ids)} already-processed sessions")

    if args.batch is not None:
        all_ids = all_ids[:args.batch]

    if not all_ids:
        print("No sessions to process.")
        return

    print(f"Processing {len(all_ids)} sessions  (offset={args.offset}, batch={args.batch})\n")

    segments_map: dict[str, list] = {}

    for idx, sid in enumerate(all_ids, 1):
        print(f"[{idx}/{len(all_ids)}] {sid[:8]}...")

        events = parse_events(sid)
        if events is None:
            print("  No JSONL found, skipping")
            continue

        blocks = event_blocks.get(sid, [])
        doc_segments = extract_doc_segments(events)

        if len(doc_segments) != len(blocks):
            print(f"  WARNING: parsed {len(doc_segments)} segments vs {len(blocks)} blocks – using min")

        min_len = min(len(doc_segments), len(blocks))
        doc_segments = doc_segments[:min_len]
        blocks_trimmed = blocks[:min_len]

        segs = build_segment_results(doc_segments, blocks_trimmed)
        segments_map[sid] = segs

        seg_path = os.path.join(SEGMENT_OUT_DIR, sid + ".json")
        with open(seg_path, "w", encoding="utf-8") as f:
            json.dump(segs, f, indent=2, ensure_ascii=False)
        print(f"  segment_results: {len(segs)} docs")

        json_data = build_json_file(sid, doc_segments)
        json_path = os.path.join(JSON_OUT_DIR, sid + ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"  json:            {len(json_data['actions'])} actions")

    print("\nUpdating session.csv ...")
    build_session_csv(list(segments_map.keys()), segments_map)

    done = len([f for f in os.listdir(SEGMENT_OUT_DIR) if f.endswith(".json")])
    total = len(event_blocks)
    remaining = total - done
    print(f"\nDone! Processed so far: {done}/{total}  (remaining: {remaining})")
    if remaining > 0 and args.batch:
        next_offset = args.offset + len(segments_map)
        print(f"  Next run: python halie_summarization_build.py --batch {args.batch} --offset {next_offset}")
        print(f"  Or resume: python halie_summarization_build.py --batch {args.batch} --skip-done")


if __name__ == "__main__":
    main()

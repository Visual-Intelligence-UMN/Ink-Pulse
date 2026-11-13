import os
import json
import random
import pandas as pd
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic
from openpyxl import load_workbook

random.seed(23)

dataset_name = "creative"

# ---- Two clients ----
gpt_client = OpenAI(
    base_url="https://bedrock-mantle.us-east-2.api.aws/openai/v1",
    api_key=os.getenv("AWS_BEARER_TOKEN_BEDROCK")
)

claude_client = Anthropic(
    base_url="https://bedrock-mantle.us-east-2.api.aws/anthropic",
    api_key=os.getenv("AWS_BEARER_TOKEN_BEDROCK")
)

GPT_MODEL = "openai.gpt-5.6-terra"
CLAUDE_MODEL = "anthropic.claude-haiku-4-5"

script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, f"writing_quality_comparison_{dataset_name}.xlsx")


# ---- Text reconstruction from raw .jsonl (ported from notebook's get_data) ----
# The processed json files only store len(text), not the text itself.
# So we reconstruct intro + full article directly from the raw import_dataset .jsonl.

def reconstruct_text_from_jsonl(jsonl_path):
    """
    Replays all insert/delete ops from the raw .jsonl to reconstruct the final
    article text and the initial intro text, exactly as the notebook's get_data() does.
    Returns (init_text, full_article_text).
    """
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = [line.replace("\0", "") for line in f if line.strip()]

    init_text = ""
    text = ""
    previous_event_name = None

    for line_number, line in enumerate(lines, start=1):
        json_data = json.loads(line)

        if line_number == 1:
            init_text = json_data.get("currentDoc", "")
            init_timestamp = json_data.get("eventTimestamp")
            text = init_text  # start with whatever was pre-filled

        event_name = json_data.get("eventName")
        event_source = json_data.get("eventSource", "unknown")
        text_delta = json_data.get("textDelta", {})

        if not isinstance(text_delta, dict):
            if isinstance(text_delta, str) and text_delta.strip():
                try:
                    text_delta = json.loads(text_delta)
                except json.JSONDecodeError:
                    text_delta = {}
            else:
                text_delta = {}

        ops = text_delta.get("ops", [])
        pos = 0

        for op in ops:
            if "retain" in op:
                pos += op["retain"]
            elif "insert" in op:
                inserts = op["insert"]
                if not isinstance(inserts, str):
                    continue
                # Mirror the notebook's api-source logic for suggestion-close
                source = event_source
                if previous_event_name == "suggestion-close" and len(inserts) > 5:
                    source = "api"
                text = text[:pos] + inserts + text[pos:]
                pos += len(inserts)
            elif "delete" in op:
                delete_count = op["delete"]
                text = text[:pos] + text[pos + delete_count:]

        previous_event_name = event_name

    return init_text, text


def longest_common(s1, s2):
    min_len = min(len(s1), len(s2))
    i = 0
    while i < min_len and s1[i] == s2[i]:
        i += 1
    return s1[:i]


def read_sentences(jsonl_path):
    """
    Returns (intro, article) by reconstructing text from the raw .jsonl.
    Strips the intro prefix from the article, matching notebook behaviour.
    """
    init_text, full_text = reconstruct_text_from_jsonl(jsonl_path)

    if init_text and init_text.strip():
        intro = init_text.strip()
        article = full_text.lstrip()
        prefix = longest_common(intro, article)
        if prefix:
            article = article[len(prefix):].lstrip()
            print("  Match: intro prefix stripped")
        else:
            print("  No common prefix found")
    else:
        print("  Has no intro")
        intro = ""
        article = full_text.lstrip()

    return intro, article


# ---- Model callers ----

def refresh_clients():
    """Re-read the bearer token from env and rebuild both clients.
    Call this after refreshing AWS_BEARER_TOKEN_BEDROCK in your shell,
    or hook it up to your team's token-refresh command here.
    """
    global gpt_client, claude_client
    token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    gpt_client = OpenAI(
        base_url="https://bedrock-mantle.us-east-2.api.aws/openai/v1",
        api_key=token
    )
    claude_client = Anthropic(
        base_url="https://bedrock-mantle.us-east-2.api.aws/anthropic",
        api_key=token
    )
    print("  Clients refreshed with new token.")

def is_auth_error(e):
    msg = str(e)
    return "401" in msg or "invalid_api_key" in msg or "expired" in msg or "authentication_error" in msg

def call_gpt(input_prompt, retries=3):
    for attempt in range(retries):
        try:
            response = gpt_client.responses.create(
                model=GPT_MODEL,
                input=input_prompt,
                max_output_tokens=512
            )
            return response.output_text
        except Exception as e:
            if is_auth_error(e) and attempt < retries - 1:
                print(f"  Auth error (attempt {attempt+1}). Refresh AWS_BEARER_TOKEN_BEDROCK then press Enter...")
                input()
                refresh_clients()
            else:
                raise

def call_claude(input_prompt, retries=3):
    for attempt in range(retries):
        try:
            response = claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": input_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            if is_auth_error(e) and attempt < retries - 1:
                print(f"  Auth error (attempt {attempt+1}). Refresh AWS_BEARER_TOKEN_BEDROCK then press Enter...")
                input()
                refresh_clients()
            else:
                raise

def build_prompt(session_id, topic, intro, article):
    return f"""
        Topic: {topic}
        Introduction: {intro}
        Article: {article}
        —– 
        You are evaluating an article co-written by a human and an AI. You must objectively score the topic-article pair based on the two criteria below:
        New Idea (0-5):  
        Evaluate how much *new, original thinking* the article contributes *beyond the Introduction*.  
        - 0: No ideas; incoherent or irrelevant.  
        - 1: Purely obvious or generic.  
        - 2: Fragmented or shallow ideas.  
        - 3: Standard ideas with some development.  
        - 4: Clear new insights or novel angles.  
        - 5: Multiple strong original ideas; deep or creative expansion beyond the intro.

        Coherence (0-5):  
        Evaluate how well the article maintains *logical structure*, *natural transitions*, and *stylistic consistency* throughout.
        - 0: Disjointed or jarring; abrupt shifts in tone or topic. 
        - 1: Minimal cohesion; sections feel stitched together.
        - 2: Mostly smooth but has several awkward transitions.
        - 3: Generally coherent; occasional unevenness.
        - 4: Well-structured with clear, natural progression.
        - 5: Seamless flow and unity; stylistically and structurally refined.

        Note: The Introduction is provided for context only and should NOT be considered part of the article content for scoring purposes.
        Your response should be in JSON format as follows:  
        ["session_id": {session_id}, "idea_score": "idea_score","coherence_score": "coherence_score", "reason": "Explain briefly why you gave these scores, citing specific examples or patterns from the article."]
        —–
        score:
    """

def process_evaluate(answer):
    answer = answer.strip().removeprefix("```json").removesuffix("```").strip()
    if answer.startswith("[") and answer.endswith("]"):
        answer = "{" + answer[1:-1] + "}"
    try:
        data = json.loads(answer)
        idea_score = int(data["idea_score"])
        coherence_score = int(data["coherence_score"])
        score = idea_score + coherence_score
    except Exception as e:
        print("Fail:", answer)
        print(e)
        idea_score = 0
        coherence_score = 0
        score = 0
        with open("failed.txt", "a") as f:
            f.write(answer + "\n")
    return score, idea_score, coherence_score

def evaluate_prompt(caller_fn, model_name, session_id, topic, intro, article):
    prompt = build_prompt(session_id, topic, intro, article)
    answer = caller_fn(prompt)
    score, idea_score, coherence_score = process_evaluate(answer)
    return {
        "session_id": session_id,
        "model": model_name,
        "idea_score": idea_score,
        "coherence_score": coherence_score,
        "total_score": score,
        "reason": answer
    }


# ---- Excel helpers (same save/resume pattern as semantic_change) ----

COLUMNS = ["session_id", "model", "idea_score", "coherence_score", "total_score", "reason"]

def init_excel(output_path, row):
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame([row])[COLUMNS].to_excel(writer, sheet_name="All Results", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="Comparison", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="Correlation", index=False)

def append_to_excel(output_path, row):
    wb = load_workbook(output_path)
    ws = wb["All Results"]
    ws.append([row[col] for col in COLUMNS])
    wb.save(output_path)

def compute_rank_agreement(gpt_scores, claude_scores, common):
    """
    Kendall's tau-b: fraction of session *pairs* where GPT and Claude
    agree on which session scored higher (concordant pairs) minus
    discordant pairs, normalized. Ranges -1 to 1.
    Also returns raw concordant/discordant counts for interpretability.
    """
    from scipy.stats import kendalltau
    import itertools

    g = gpt_scores[common].values
    c = claude_scores[common].values

    concordant = discordant = tied = 0
    for (g1, c1), (g2, c2) in itertools.combinations(zip(g, c), 2):
        g_dir = int(g1 > g2) - int(g1 < g2)  # +1, 0, -1
        c_dir = int(c1 > c2) - int(c1 < c2)
        if g_dir == 0 or c_dir == 0:
            tied += 1
        elif g_dir == c_dir:
            concordant += 1
        else:
            discordant += 1

    total_pairs = concordant + discordant + tied
    tau, pval = kendalltau(g, c)
    return {
        "kendall_tau": round(tau, 4),
        "kendall_p": round(pval, 4),
        "concordant_pairs": concordant,
        "discordant_pairs": discordant,
        "tied_pairs": tied,
        "total_pairs": total_pairs,
        "pct_concordant": round(concordant / (concordant + discordant) * 100, 2) if (concordant + discordant) > 0 else None
    }


def write_summary_sheets(output_path, results_df):
    from scipy.stats import spearmanr

    # Exclude failed parses (score=0) from rank analysis
    valid_df = results_df[results_df["total_score"] > 0]

    pivot_df = results_df.pivot(
        index="session_id",
        columns="model",
        values=["idea_score", "coherence_score", "total_score"]
    ).reset_index()
    pivot_df.columns = ["_".join(col).strip("_") for col in pivot_df.columns]

    gpt_scores = valid_df[valid_df["model"] == GPT_MODEL].set_index("session_id")["total_score"]
    claude_scores = valid_df[valid_df["model"] == CLAUDE_MODEL].set_index("session_id")["total_score"]
    common = gpt_scores.index.intersection(claude_scores.index)

    corr, pval = None, None
    rank_stats = {}
    if len(common) > 1:
        corr, pval = spearmanr(gpt_scores[common], claude_scores[common])
        print(f"\nSpearman r={corr:.3f}, p={pval:.4f}")
        rank_stats = compute_rank_agreement(gpt_scores, claude_scores, common)
        print(f"Kendall tau={rank_stats['kendall_tau']}, concordant={rank_stats['pct_concordant']}%")

    # Add ranks to pivot for inspection
    pivot_df = pivot_df.copy()
    gpt_all   = results_df[results_df["model"] == GPT_MODEL].set_index("session_id")["total_score"]
    claude_all = results_df[results_df["model"] == CLAUDE_MODEL].set_index("session_id")["total_score"]
    pivot_df["rank_gpt"]    = pivot_df["session_id"].map(gpt_all.rank(ascending=False, method="min"))
    pivot_df["rank_claude"] = pivot_df["session_id"].map(claude_all.rank(ascending=False, method="min"))
    pivot_df["rank_diff"]   = (pivot_df["rank_gpt"] - pivot_df["rank_claude"]).abs()
    pivot_df = pivot_df.sort_values("rank_diff", ascending=False)  # biggest disagreements first

    wb = load_workbook(output_path)

    ws_cmp = wb["Comparison"]
    ws_cmp.delete_rows(1, ws_cmp.max_row)
    ws_cmp.append(list(pivot_df.columns))
    for _, row in pivot_df.iterrows():
        ws_cmp.append(list(row))

    ws_cor = wb["Correlation"]
    ws_cor.delete_rows(1, ws_cor.max_row)
    if corr is not None:
        # Spearman
        ws_cor.append(["metric", "value"])
        ws_cor.append(["spearman_r", round(corr, 4)])
        ws_cor.append(["spearman_p", round(pval, 4)])
        ws_cor.append([])
        # Kendall / rank agreement
        for k, v in rank_stats.items():
            ws_cor.append([k, v])

    wb.save(output_path)


# ---- Resume: load already-done (session_id, model) pairs ----

def load_done_from_excel(output_path):
    done = set()
    all_rows = []
    if not os.path.exists(output_path):
        return done, all_rows
    try:
        df = pd.read_excel(output_path, sheet_name="All Results")
        all_rows = df.to_dict("records")
        for row in all_rows:
            done.add((str(row["session_id"]), str(row["model"])))
        print(f"Resuming: {len(done)} evaluations already in Excel.")
    except Exception as e:
        print(f"Could not read existing Excel ({e}), starting fresh.")
    return done, all_rows


# ---- Main ----

def main(dataset_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(os.path.dirname(script_dir))

    # Raw .jsonl files live in import_dataset/<dataset_name>/
    jsonl_dir = os.path.join(static_dir, "import_dataset", dataset_name)
    topic_dir = os.path.join(static_dir, "import_dataset", f"{dataset_name}.csv")

    topic_df = pd.read_csv(topic_dir)
    done, all_rows = load_done_from_excel(output_path)

    for file_name in sorted(os.listdir(jsonl_dir)):
        if not file_name.endswith(".jsonl"):
            continue

        jsonl_path = os.path.join(jsonl_dir, file_name)
        session_id = os.path.splitext(file_name)[0]
        session = topic_df[topic_df["session_id"] == session_id]

        if session.empty:
            continue

        print(f"Processing {session_id}...")
        topic = session["prompt_code"].values[0]
        intro, article = read_sentences(jsonl_path)

        for caller_fn, model_name in [(call_gpt, GPT_MODEL), (call_claude, CLAUDE_MODEL)]:
            key = (session_id, model_name)
            if key in done:
                print(f"  {model_name} already done, skipping")
                continue

            try:
                result = evaluate_prompt(caller_fn, model_name, session_id, topic, intro, article)
            except Exception as e:
                print(f"  {model_name} failed for {session_id}: {e}")
                continue

            all_rows.append(result)
            done.add(key)

            if not os.path.exists(output_path):
                init_excel(output_path, result)
            else:
                append_to_excel(output_path, result)

            print(f"  {model_name} saved to Excel ✓")

    results_df = pd.DataFrame(all_rows)
    if not results_df.empty:
        write_summary_sheets(output_path, results_df)

    print(f"\nDone. Saved to: {output_path}")
    print(f"Total sessions: {results_df['session_id'].nunique()}")
    print(f"Total evaluations: {len(results_df)}")


if __name__ == "__main__":
    main(dataset_name)
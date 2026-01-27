import os
import pandas as pd
from openai import OpenAI
import random
random.seed(23)
import json

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

def write_json(data, result, output_file):
    for item in data:
        item["score"] = result[0]["Score"]
    with open(output_file, "w", encoding="utf-8") as writer:
        json.dump(data, writer, ensure_ascii=False, indent=4)
    print("Done writing to: ", output_file)

def chatgpt_prompter(input_prompt):
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model = "gpt-4o",
        messages=[
            {"role": "user", "content": input_prompt}
        ],
        temperature = 0,
    )
    return completion.choices[0].message.content

def evaluate_prompt(session_id, topic, intro, article):
    result = []
    EVALUATION_PROMPT_TEMPLATE = f"""
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
    answer = chatgpt_prompter(EVALUATION_PROMPT_TEMPLATE)
    # print("system_prompt: ", EVALUATION_PROMPT_TEMPLATE)
    # print(answer)
    score = process_evaluate(answer)
    # print(score)
    result.append({
        'Prompt': EVALUATION_PROMPT_TEMPLATE,
        'Evaluation': answer,
        'Score': score
    })
    return result

def process_evaluate(answer):
    answer = answer.strip().removeprefix("```json").removesuffix("```").strip()
    if answer.startswith("[") and answer.endswith("]"):
        answer = "{" + answer[1:-1] + "}"
    try:
        data = json.loads(answer)
        idea_score = data["idea_score"]
        coherence_score = data["coherence_score"]
        score = int (idea_score) + int(coherence_score)
    except Exception as e:
        print("Fail:", answer)
        print(e)
        score = 0
        with open("failed.txt", "a") as f:
            f.write(answer + "\n")
    return score

def longest_common(s1, s2):
    min_len = min(len(s1), len(s2))
    i = 0
    while i < min_len and s1[i] == s2[i]:
        i += 1
    return s1[:i]

def read_sentences(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        intro = data["init_text"][0].strip()
        article = data["text"][0].lstrip()
        prefix = longest_common(intro, article)
        if prefix:
            article = article[len(prefix):].lstrip()
            # print("Match")
        else:
            print("No common prefix found")
    return intro, article

def write_file(note_dir, session_id, results):
    note_path = os.path.join(note_dir, session_id + ".json")
    os.makedirs(note_dir, exist_ok=True)
    with open(note_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Done eval results: {note_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    session_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "coauthor-json")
    topic_dir = os.path.join(static_dir, "Metadata (creative).csv")
    output_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "similarity_results")
    note_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "eval_results")
    # os.makedirs(output_dir, exist_ok=True)
    topic_df = pd.read_csv(topic_dir)
    for file_name in os.listdir(session_dir):
        if file_name.endswith(".jsonl"):
            file_path = os.path.join(session_dir, file_name)
            session_id = os.path.splitext(file_name)[0]
            # print(session_id)
            session = topic_df[topic_df["session_id"] == session_id]
            if not session.empty:
                print(session_id)
                topic = session["prompt_code"].values[0]
                intro, article = read_sentences(file_path)
                # print(intro)
                # print(article)
                result = evaluate_prompt(session_id, topic, intro, article)
                output_path = os.path.join(output_dir, (session_id + "_similarity" + ".json"))
                write_json(load_json(output_path), result, output_path)

                write_file(note_dir, session_id, result)


if __name__ == "__main__":    
    main()
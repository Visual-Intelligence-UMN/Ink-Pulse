import os
import pandas as pd
from openai import OpenAI
import random
random.seed(23)
import json

api_key = ""
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
        You are evaluating an article co-written by a human and an AI. You must score the topic-article pair on a scale from 0 to 5 based on this rubric:
        Score 0: The content is unrelated to the topic, incoherent, or completely fails to form a meaningful piece of writing.
        Score 1: The content is extremely superficial, lacks logical development, or reads like a mix of raw AI output and minimal human edits. The writing is highly fragmented and lacks coherence. Human-AI integration is poor or almost nonexistent.
        Score 2: The article addresses the topic but is fragmented, overly simplistic, or disjointed. The ideas do not build well on each other. Human and AI contributions feel disconnected, with sudden transitions or unclear flow.
        Score 3: The article stays on topic and has a logical structure, but much of the content is generic, repetitive, or shallow. AI-generated sections are noticeable due to stylistic mismatches, filler phrases, or lack of nuance. Transitions or tone shifts may be abrupt.
        Score 4: The article flows well and develops its ideas with some depth. There may be slight inconsistencies in tone or moments of cliché, but the structure is solid and the content is relevant and coherent. Human-AI integration is smooth, though not fully seamless.
        Score 5: The article is insightful, original, and demonstrates deep idea development. The writing is natural, coherent, and fully cohesive throughout. The human-AI collaboration is seamless — it feels like a single, unified authorial voice. There are no signs of template-based or generic AI writing.
        Note: The Introduction is provided for context only and should NOT be considered part of the article content for scoring purposes.
        Your response should be in JSON format as follows:  
        ["session_id": {session_id}, "score": "score", "reason": "your reason why you give that score"].
        —–
        score:
    """      
    answer = chatgpt_prompter(EVALUATION_PROMPT_TEMPLATE)
    print("system_prompt: ", EVALUATION_PROMPT_TEMPLATE)
    print(answer)
    score = process_evaluate(answer)
    print(score)
    result.append({
        'Prompt': EVALUATION_PROMPT_TEMPLATE,
        'Evaluation': answer,
        'Score': score
    })
    return result

def process_evaluate(answer):
    answer = answer.strip().removeprefix("```json").removesuffix("```").strip()
    data = json.loads(answer)
    score = data["score"]
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

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.dirname(script_dir)
    session_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "coauthor-json")
    topic_dir = os.path.join(static_dir, "session_metadata.csv")
    output_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "similarity_results")
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
                print(intro)
                print(article)
                # result = evaluate_prompt(session_id, topic, intro, article)
                # output_path = os.path.join(output_dir, (session_id + "_similarity" + ".json"))
                # write_json(load_json(output_path), result, output_path)
            break
        break

if __name__ == "__main__":    
    main()
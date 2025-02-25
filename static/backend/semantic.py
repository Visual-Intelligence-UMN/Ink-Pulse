import os
import json
import numpy as np
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
# import openai
# openai.api_key = "KEY"

def read_sentence(session_path):
    with open(session_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        for setence in data:
            print(setence)

def get_sentence_vector(sentence, model):
        vectors = [model.wv[word] for word in sentence if word in model.wv]

        return np.mean(vectors, axis=0) if vectors else np.zeros(model.vector_size)

def sentence_similarity(sent1, sent2, model):
    vec1 = get_sentence_vector(sent1, model)
    vec2 = get_sentence_vector(sent2, model)

    return cosine_similarity([vec1], [vec2])[0][0]

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(script_dir)
    session_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0\coauthor-sentence")
    session_files = [f for f in os.listdir(session_dir) if f.endswith(".jsonl")]
    for session in session_files:
        session_path = os.path.join(session_dir, session)
        read_sentence(session_path)
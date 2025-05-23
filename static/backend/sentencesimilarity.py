import os
import json
import numpy as np
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)

# def read_sentences(file_path):
#     with open(file_path, 'r', encoding='utf-8') as file:
#         data = json.load(file)
#         sentences = [(entry["text"], entry.get("source", "unknown"), entry["start_progress"], entry["end_progress"], entry["start_time"], entry["end_time"], entry["last_event_time"]) for entry in data if "text" in entry]
#     return sentences

def read_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
        if not isinstance(data, list):
            raise ValueError("Expected a list of lists in JSON file")

        sentences = [
            [
                (entry["text"], entry.get("source", "unknown"), entry["start_progress"], 
                 entry["end_progress"], entry["start_time"], entry["end_time"], entry["last_event_time"]) 
                for entry in sublist if "text" in entry
            ]
            for sublist in data
        ]
    return sentences

def preprocess_sentence(sentence):
    return word_tokenize(sentence.lower())

def train_word2vec_model(sentences):
    # tokenized_sentences = [preprocess_sentence(sent[0]) for sent in sentences]
    tokenized_sentences = [
        preprocess_sentence(sent[0]) for sent in sentences[-1]
    ]
    
    model = Word2Vec(sentences=tokenized_sentences, vector_size=100, window=5, min_count=1, workers=4)
    return model

def get_sentence_vector(sentence, model):
    if isinstance(sentence, tuple):
        sentence = sentence[0]

    words = preprocess_sentence(sentence)
    vectors = [model.wv[word] for word in words if word in model.wv]
    
    return np.mean(vectors, axis=0) if vectors else np.zeros(model.vector_size)

def sentence_similarity(sent1, sent2, model):
    if isinstance(sent1, tuple):
        sent1 = sent1[0]
    if isinstance(sent2, tuple):
        sent2 = sent2[0]

    vec1 = get_sentence_vector(sent1, model)
    vec2 = get_sentence_vector(sent2, model)
    
    vec1 = vec1.reshape(1, -1)
    vec2 = vec2.reshape(1, -1)
    
    return cosine_similarity(vec1, vec2)[0][0]

def analyze_sentence_similarity(sentences, model):
    results = []
    
    if sentences:
        results.append({
            "sentence": sentences[0][0],
            "source": sentences[0][1],
            "max_similarity": 0.0,
            "dissimilarity": 1.0,
            "most_similar_previous": None,
            "start_progress": sentences[0][2],
            "end_progress": sentences[0][3],
            "start_time": sentences[0][4],
            "end_time": sentences[0][5],
            "last_event_time": sentences[0][6],
        })
    for i in range(1, len(sentences)):
        similarities = []
        for j in range(0, i):
            sim = sentence_similarity(sentences[i][0], sentences[j][0], model)
            similarities.append((j, sim))
        if similarities:
            most_similar_idx, max_similarity = max(similarities, key=lambda x: x[1])
            dissimilarity = 1.0 - max_similarity
            
            results.append({
                "sentence": sentences[i][0],
                "source": sentences[i][1],
                "max_similarity": max_similarity,
                "dissimilarity": dissimilarity,
                "most_similar_previous": most_similar_idx,
                "start_progress": sentences[i][2],
                "end_progress": sentences[i][3],
                "start_time": sentences[i][4],
                "end_time": sentences[i][5],
                "last_event_time": sentences[0][6],
            })
    
    return results

def analyze_sentence_similarity(nested_sentences, model):
    results = []

    for sublist in nested_sentences:
        sub_results = []
        if sublist:
            sub_results.append({
                "sentence": sublist[0][0],
                "source": sublist[0][1],
                "max_similarity": 0.0,
                "dissimilarity": 1.0,
                "most_similar_previous": None,
                "start_progress": sublist[0][2],
                "end_progress": sublist[0][3],
                "start_time": sublist[0][4],
                "end_time": sublist[0][5],
                "last_event_time": sublist[0][6],
            })

        for i in range(1, len(sublist)):
            similarities = []
            for j in range(0, i):
                sim = sentence_similarity(sublist[i][0], sublist[j][0], model)
                similarities.append((j, sim))

            if similarities:
                most_similar_idx, max_similarity = max(similarities, key=lambda x: x[1])
                dissimilarity = 1.0 - max_similarity

                sub_results.append({
                    "sentence": sublist[i][0],
                    "source": sublist[i][1],
                    "max_similarity": max_similarity,
                    "dissimilarity": dissimilarity,
                    "most_similar_previous": most_similar_idx,
                    "start_progress": sublist[i][2],
                    "end_progress": sublist[i][3],
                    "start_time": sublist[i][4],
                    "end_time": sublist[i][5],
                    "last_event_time": sublist[i][6],
                })

        results.append(sub_results)

    return results

def convert_types(obj):
        if isinstance(obj, np.float32) or isinstance(obj, np.float64):
            return float(obj)
        elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
            return int(obj)
        return obj

def save_results_to_json(results, session_id, output_dir):
    output_file = os.path.join(output_dir, f"{session_id}_similarity.json")

    results_converted = [
        [{k: convert_types(v) for k, v in entry.items()} for entry in sublist] 
        for sublist in results
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
            model = train_word2vec_model(sentences)
            results = analyze_sentence_similarity(sentences, model)
            
            save_results_to_json(results, session_id, output_dir)

import os
import json
import numpy as np
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)

def read_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            sentences = [entry["text"] for entry in data if "text" in entry]
    return sentences

def preprocess_sentence(sentence):
    return word_tokenize(sentence.lower())

def train_word2vec_model(sentences):
    tokenized_sentences = [preprocess_sentence(sent) for sent in sentences]
    
    model = Word2Vec(sentences=tokenized_sentences, vector_size=100, window=5, min_count=1, workers=4)
    return model

def get_sentence_vector(sentence, model):
    words = preprocess_sentence(sentence)
    
    vectors = [model.wv[word] for word in words if word in model.wv]
    
    # If no words returning the mean vector or zeroes\
    return np.mean(vectors, axis=0) if vectors else np.zeros(model.vector_size)

def sentence_similarity(sent1, sent2, model):
    vec1 = get_sentence_vector(sent1, model)
    vec2 = get_sentence_vector(sent2, model)
    
    vec1 = vec1.reshape(1, -1)
    vec2 = vec2.reshape(1, -1)
    
    return cosine_similarity(vec1, vec2)[0][0]

'''
def analyze_sentence_similarity(sentences, model):
    results = []
    
    # 1st sentence so no prev sentence to compare so just append
    if sentences:
        results.append({
            "sentence": sentences[0],
            "max_similarity": 0.0,
            "dissimilarity": 1.0,
            "most_similar_previous": None
        })
    
    # second setence so compare with first
    if len(sentences) > 1:
        similarity = sentence_similarity(sentences[1], sentences[0], model)
        results.append({
            "sentence": sentences[1],
            "max_similarity": similarity,
            "dissimilarity": 1.0 - similarity,
            "most_similar_previous": 0
        })
    
    # for 3rd sentence compare with previous sentence
    for i in range(2, len(sentences)):
        similarities = []
        for j in range(max(0, i-2), i):
            sim = sentence_similarity(sentences[i], sentences[j], model)
            similarities.append((j, sim))
        
        # Find the most similar previous sentence
        if similarities:
            most_similar_idx, max_similarity = max(similarities, key=lambda x: x[1])
            dissimilarity = 1.0 - max_similarity
            
            results.append({
                "sentence": sentences[i],
                "max_similarity": max_similarity,
                "dissimilarity": dissimilarity,
                "most_similar_previous": most_similar_idx
            })
    
    return results
'''

def analyze_sentence_similarity(sentences, model):
    results = []
    
    # 1st sentence so no prev sentence to compare so just append
    if sentences:
        results.append({
            "sentence": sentences[0],
            "max_similarity": 0.0,
            "dissimilarity": 1.0,
            "most_similar_previous": None
        })
    
    # For rest compare with all previous sentences and then append
    for i in range(1, len(sentences)):
        similarities = []
        for j in range(0, i):
            sim = sentence_similarity(sentences[i], sentences[j], model)
            similarities.append((j, sim))
        
        if similarities:
            most_similar_idx, max_similarity = max(similarities, key=lambda x: x[1])
            dissimilarity = 1.0 - max_similarity
            
            results.append({
                "sentence": sentences[i],
                "max_similarity": max_similarity,
                "dissimilarity": dissimilarity,
                "most_similar_previous": most_similar_idx
            })
    
    return results

def save_results_to_json(results, session_id, output_dir):
    output_file = os.path.join(output_dir, f"{session_id}_similarity.json")
    
    def convert_types(obj):
        if isinstance(obj, np.float32) or isinstance(obj, np.float64):
            return float(obj)
        elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
            return int(obj)
        return obj

    results_converted = [{k: convert_types(v) for k, v in entry.items()} for entry in results]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results_converted, f, indent=4, ensure_ascii=False)

    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    static_dir = os.path.dirname(script_dir)
    
    session_dir = os.path.join(static_dir, "chi2022-coauthor-v1.0", "coauthor-sentence")
    output_dir = os.path.join(static_dir, "similarity_results")
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(session_dir):
        if file_name.endswith(".jsonl"):
            file_path = os.path.join(session_dir, file_name)
            session_id = os.path.splitext(file_name)[0]

            
            sentences = read_sentences(file_path)
            model = train_word2vec_model(sentences)
            results = analyze_sentence_similarity(sentences, model)
            
            save_results_to_json(results, session_id, output_dir)

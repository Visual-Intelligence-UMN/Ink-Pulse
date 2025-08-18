import process.data2json
import process.time_convert
import process.make_fine_file
import process.openai_residual_vector
import process.evaluator
import process.clean
import process.content_length
import process.ai_ratio
import process.overall_sem_score
import process.score_summary
import process.session_name

"""
Put your dataset folder and .csv under /static/import_data/ and they should be the same name, like data/ and data.csv
The .csv file should contain at least session_id(file name) and prompt_code(topic of the article)
"""
# Change the name to your dataset's name
dataset_name = "legislation_formal_study"

process.data2json.main(dataset_name)
process.time_convert.main(dataset_name)
process.make_fine_file.main(dataset_name)
process.openai_residual_vector.main(dataset_name) # Code for calculating semantic score
process.evaluator.main(dataset_name) # Code LLM judge score, including evaluation template
process.clean.main(dataset_name)

# Code for calculating general features for all sessions in your dataset
process.content_length.main(dataset_name)
process.ai_ratio.main(dataset_name)
process.overall_sem_score.main(dataset_name)
process.score_summary.main(dataset_name)
process.session_name.main(dataset_name)

import os
import json

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    return data

script_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.dirname(script_dir)
json_path = os.path.join(static_dir, "dataset_name.json")
data = load_json(json_path)
data.append(dataset_name)
with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)







# How to use
Run **`npm run dev`**

Click the point in the chart to check the current text

#### `dataset checking`
**`static/issue.json`**: File that contains issue **session id** and **line**

**`static/fine.json`**: File that contains **session id** and other related data (link to **session_metadata.csv**)

**`static/chi2022-coauthor-v1.0/coauthor-json/`**: Files that contains extracted data from fine sessions

**`static/chi2022-coauthor-v1.0/coauthor-sentence/`**: Files that contains extracted sentences and sources for each session

#### `python code`
**`static/backend/check_multiple.py`**: Code for creating the fine.json and issue.json

**`static/backend/data2json.py`**: Code for creating files in **/coauthor-json**

**`static/backend/extract_jsonl.py`**: Code for extracting data

**`static/backend/test_jsonl.py`**: Test code of **extract_jsonl.py**
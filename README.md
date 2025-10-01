# InkPulse: Understanding Interactions in Human-AI Co-writing through Fuzzy Visual Patterns

## Gettign started
First, install all dependencies by using: 

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:5173](http://localhost:5173) with your browser to see the result.

## How to import your own dataset

Put your dataset in folder **`static/import_dataset`**

Your dataset should contains:

1. data/session.jsonl

2. data.csv

session.jsonl format should be the same as CoAuthor's, or at least keystroke-level logs. Sample can be checked in **`static/import_dataset/creative`**

dataset.csv should contain at least **session_id** and **prompt_code**. Sample can be checked in **`static/import_dataset/creative.csv`**

If you want to change the method for calculating **semantic score** or **writing quality score**, related code can be found in **`static/backend/process`**

## Dataset
**`static/dataset`**: Files that contains dataset used in the tool

## Code
**`static/backend`**: Code for data processing
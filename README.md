# InkPulse: Understanding Interactions in Human-AI Co-writing through Fuzzy Visual Patterns

## Introduction

The repository is for InkPulse, a visual analytics system that supports the identification, search, and
analysis of key interactions in human-AI co-writing.

The introduction video can be found [here](https://drive.google.com/file/d/10hUfbSWKgs8HGooqmY0QcR2q3_x5e5AH/view?usp=sharing).

https://github.com/user-attachments/assets/52fd3243-0cf5-4943-a456-d8fd09c1538b

## Getting started

If running for the first time, ensure you have Node.js **v18 or newer** installed. You can check your version by running:

```bash
node -v
```

Install all dependencies by using: 

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

## Project structure

This project is organized with the following structure(only list main folders):


### Structure

- **`/src/routes/`**  
  Contains the main application routes.

- **`/src/components/`**  
  Contains the key components used throughout the project, such as charts.

- **`/static/backend/`**  
  Contains code related to data processing. The main file for data processing is `index.py`, and additional processing logic is contained in `/static/backend/process`.

- **`/static/dataset/`**  
  Contains the processed datasets that are used by the application.

- **`/static/import_dataset/`**  
  Contains the raw data files.

- **`/static/pattern/`**  
  Contains saved patterns.

## How to import your own dataset

Before loading your dataset, please check the data structure used in the project [here](https://docs.google.com/document/d/13v_90J6CMw9Cgdh7tF_-nVc_o5XaYOiswhhOw3KJseE/edit?usp=sharing).

Put your dataset in folder **`static/import_dataset`**

Your dataset should contains:

1. data/session.jsonl

2. data.csv

session.jsonl format should be similar as [CoAuthor](https://coauthor.stanford.edu/)'s, or at least keystroke-level logs. Sample can be checked in **`static/import_dataset/creative`**

dataset.csv should contain at least **session_id** and **prompt_code**. Sample can be checked in **`static/import_dataset/creative.csv`**

If you want to change the method for calculating **semantic score** or **writing quality score**, related code can be found in **`static/backend/process`**, in `openai_residual_vector.py` and `evaluator.py`.

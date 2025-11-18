# InkPulse

The repository is for InkPulse, a visual analytics system that supports the identification, search, and analysis of key interactions in human-AI co-writing.

The introduction video can be found [here](https://github.com/user-attachments/assets/52fd3243-0cf5-4943-a456-d8fd09c1538b)

https://github.com/user-attachments/assets/52fd3243-0cf5-4943-a456-d8fd09c1538b
## Table of Contents

- [InkPulse](#inkpulse)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [Project Structure](#project-structure)
  - [Data Structure](#data-structure)
    - [Detailed Data Specifications](#detailed-data-specifications)
      - [Events (Individual User Actions)](#events-individual-user-actions)
      - [Event Blocks (Grouped Actions)](#event-blocks-grouped-actions)
      - [Session Info (Session-Level Metadata)](#session-info-session-level-metadata)
  - [How to import your own dataset](#how-to-import-your-own-dataset)

## Getting Started

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
```

Open [http://localhost:5173](http://localhost:5173) with your browser to see the result.

## Project Structure

```text
.
├── .github/
│   └── workflows/        # github action files for app building and delopyment
│ 
├── src/
│   ├── components/       # Svelte UI components (charts, dialogs, panels)
│   ├── lib/              # Shared utilities/helpers
│   ├── routes/           # SvelteKit routes (pages + endpoints)
│   ├── workers/          # Web workers for background tasks
│   ├── app.d.ts          # App-level TypeScript declarations
│   └── app.html          # HTML template
│ 
├── static/
│   ├── backend/          # Python backend for data processing
│   ├── dataset/          # Processed datasets used by the app
│   └── patterns/         # User-saved patterns from visual exploration
│ 
├── package.json
└── README.md
```

## Data Structure

InkPulse organizes writing session data across three hierarchical levels of abstraction: 
**Events** → **Event Blocks** → **Session Info**.
<!-- ![description](ssa.png) -->

- **Events (Individual User Actions)**: the finest level of granularity captures each individual user action (e.g., insertion, deletion, accept AI suggestion) during a writing session. Each session is stored as a separate JSONL file named `[session_id].jsonl`, located at `static/dataset/[dataset_name]/json` folder.
- **Event Blocks (Grouped Actions):** To facilitate analysis, individual events are grouped into event blocks. By default, an event block contains all consecutive actions a user performs while actively writing, ending when the user either requests AI suggestions or accepts an AI insertion. Each session is stored as `[session_id].jsonl` within  `static/dataset/[dataset_name]/segment_results` folder.
- **Session Info (Session-Level Metadata):** this file (`static/dataset/[dataset_name]/session.json`) contains high-level metadata (e.g., topic, writing ID, AI model) for writing sessions. This JSON files contains all the writing sessions from a specific dataset, with each JSON object corresponds to one writing session.

### Detailed Data Specifications

Below is the structure and examples for the three levels.

#### Events (Individual User Actions)

  **Location:** `static/dataset/[dataset_name]/json/[session_id].jsonl`
  Each file is a writing session with the following structure: 
  ```json
  {
    "init_text": [ "..." ],
    "init_time": [ "..." ],
    "events": [
      {
        "id": num,
        "name": "suggestion-open | text-insert | text-delete",
        "text": "...",
        "eventSource": "user | api",
        "event_time": "YYYY-MM-DD hh:mm:ss",
        "progress": num,
        "count": num,
        "pos": num
      }
    ]
  }
  ```

  - **init_text**: Initial text representing the topic
  - **init_time**: Timestamp indicating when the initial text was presented
  - **text**: Full text content
  - **events**: Present each action
    - **id**: Unique identifier of the operation
    - **name**: Name of the action
    - **text**: The text content involved in the action
    - **eventSource**: Source of the action
    - **event_time**: Timestamp of the action
    - **event_progress**: Progress of the action
    - **count**: Number of characters
    - **pos**: Position of characters
  
  **Example:**
  ```json
  {
    "init_text": [
      "Humans once wielded formidable magical power..."
    ],
    "init_time": [
      "2021-08-17 07:22:04"
    ],
    "events": [
      {
        "id": 2,
        "name": "suggestion-open",
        "eventSource": "api",
        "event_time": "2021-08-17 07:22:12"
      },
      {
        "id": 9,
        "name": "text-insert",
        "text": "\nThe world is a dangerous place, but it is also filled with wonder.\n",
        "eventSource": "api",
        "event_time": "2021-08-17 07:22:17",
        "count": 68,
        "pos": 272,
        "progress": 0.11647824597464886
      }
    ]
  }

  ```
  
#### Event Blocks (Grouped Actions)

  **Location:** `static/dataset/[dataset_name]/segment_results/[session_id].json`
  **Schema:**
  ```
    List[
      {
        "start_progress": float,       # Document progress at segment start
        "end_progress": float,         # Document progress at segment end
        "start_time": float,           # Start time (seconds)
        "end_time": float,             # End time (seconds)
        "actions": List[num],          # list of action IDs
        "residual_vector_norm": float, # Semantic expansion score
      }
    ]
  ```
  Additional, user-defined attributes (e.g., scores, text length) can be added as needed.


#### Session Info (Session-Level Metadata)

  **Location:** `static/dataset/[dataset_name]/session.json`

  High-level metadata for all writing sessions. Each JSON object represents one complete session. Only `session_id` is required; all other fields are user-defined based on analysis needs.

  **Schema:**
  ```JSON
  {
    "session_id": str,        # Unique session identifier
    "writer_id": str,         # Unique writer identifier
    "topic": str,             # Writing prompt/topic
    ...
  }
  ```
  



## How to import your own dataset

You can use **`static/backend/index.ipynb`** to preprocess the data, a Google olab version is available [here]().

This script takes in two files (i) `data/session.jsonl`, which saves the complete writing action logs as the format specified in the [CoAuther Dataset Schema](https://coauthor.stanford.edu), and (ii) `data.csv`, which specific the session level data at least **session_id** and **prompt_code**. Sample can be checked in **`static/import_dataset/creative.csv`**. The outputed folder `[dataset_name]` will contain all the files as described in [Data Structure](#data-structure). Put the folder within `static/dataset`, you can then start the visual exploration.
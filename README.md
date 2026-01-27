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

- **Events (Individual User Actions)**: the finest level of granularity captures each individual user action (e.g., insertion, deletion, accept AI suggestion) during a writing session. Each session is stored as a separate JSON file named `[session_id].json`, located at `static/dataset/[dataset_name]/json` folder.
- **Event Blocks (Grouped Actions):** To facilitate analysis, individual events are grouped into event blocks. By default, an event block contains all consecutive actions a user performs while actively writing, ending when the user either requests AI suggestions or accepts an AI insertion. Each session is stored as `[session_id].json` within  `static/dataset/[dataset_name]/segment_results` folder.
- **Session Info (Session-Level Metadata):** this file (`static/dataset/[dataset_name]/session.json`) contains high-level metadata (e.g., topic, writing ID, AI model) for writing sessions. This JSON files contains all the writing sessions from a specific dataset, with each JSON object corresponds to one writing session.

### Detailed Data Specifications

Below is the structure and examples for the three levels.

#### Events (Individual User Actions)

  **Location:** `static/dataset/[dataset_name]/json/[session_id].json`
  Each file is a writing session with the following structure
  
  **Schema:**
  ```typescript

  type Event {
    // Type of action
    name: "suggestion-open" | "text-insert" | "text-delete" | string;       
    text?: string;         // Text content involved in the action (if applicable)
    eventSource: "user" | "api"; // Source of the action
    event_time: string;    // Timestamp, e.g., "YYYY-MM-DD hh:mm:ss"
    progress: number;      // Document-level progress (0–1)
    pos: number;           // Character position in the document
  }

  type SessionEvents {
    init_text: string[];   // Initial text representing the topic
    init_time: string[];   // Timestamp(s) when the initial text was presented
    text: string[];        // Full text content (after applying actions)
    events: Event[];       // List of all actions in the session
  }
  ```
   **Example**: [/static/dataset/creative/json/016...84f.json](https://github.com/Visual-Intelligence-UMN/Ink-Pulse/blob/main/static/dataset/creative/json/01650a401e614c38a04a904165a5784f.json)
  
#### Event Blocks (Grouped Actions)

  **Location:** `static/dataset/[dataset_name]/segment_results/[session_id].json`
  
  **Schema:**
  ```typescript
    type EventBlock = {
      start_progress: number; // Document progress at segment start (0–1)
      end_progress: number;   // Document progress at segment end (0–1)
      start_time: number;     // Start time in seconds since session start
      end_time: number;       // End time in seconds since session start
      actions: number[];      // List of action IDs in this block

      // Other user-defined attributes (e.g., scores, text length)
      [key: string]: number | string | boolean | number[] | string[] | null;
    };

    type EventBlocksFile = EventBlock[];

  ```
  Additional, user-defined attributes (e.g., scores, text length) can be added as needed.

  **Example**: [/static/dataset/creative/segment_results/016...84f.json](https://github.com/Visual-Intelligence-UMN/Ink-Pulse/blob/main/static/dataset/creative/segment_results/01650a401e614c38a04a904165a5784f.json)


#### Session Info (Session-Level Metadata)

  **Location:** `static/dataset/[dataset_name]/session.json`

  High-level metadata for all writing sessions. Each JSON object represents one complete session. Only `session_id` is required; all other fields are user-defined based on analysis needs.

  **Schema:**
  ```typescript
  type SessionInfo = {
    session_id: string; // Required: unique session identifier

    // Optional / user-defined fields:
    writer_id?: string; // Unique writer identifier
    topic?: string;     // Writing prompt/topic

    // Other user-defined attributes
    [key: string]: string | number | boolean | null | undefined;
  };

  type SessionInfoFile = SessionInfo[];
  ```

  **Example**: [/static/dataset/creative/session.json](https://github.com/Visual-Intelligence-UMN/Ink-Pulse/blob/main/static/dataset/creative/session.json)

## How to import your own dataset

**Data Preprocessing:** You can use **`static/backend/index.ipynb`** to preprocess the data, a Google olab version is available [here](https://drive.google.com/file/d/1ODkYqNn1siQ_x27KbnhK5h59wIOrjW79/view?usp=sharing). You need to use `[dataset_name].zip` instead of folder `[dataset_name]`.

This script takes in two files (i) `data/session.jsonl`, which saves the complete writing action logs as the format specified in the [CoAuther Dataset Schema](https://coauthor.stanford.edu), and (ii) `data.csv`, which specific the session level data at least **session_id** and **prompt_code**. Sample can be checked in **`static/import_dataset/creative.csv`**. The outputed folder `[dataset_name]` will contain all the files as described in [Data Structure](#data-structure). 

**Loading Data into InkPulse:** 
- Method One: Running InkPulse Locally. Fork this repo and run InkPulse locally following the [Getting Started](#getting-started) instructions. Place the folder generated from last step within `static/dataset` and register your dataset (`[dataset_name]`) at `static/dataset/dataset_name.json`. You can then start your visual exploration.
- Method Two: Upload Directly to the Website. Direct upload support is currently under development. Stay tuned for updates!

Use the following code to convert your dataset into local database. NOTE: only folder that in **`static/dataset`** will be detected.


```bash
npx tsx scripts/import-groups.ts
```

Or, you can upload a `.zip` file on the website.

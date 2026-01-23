#!/usr/bin/env python3
"""
Create a test dataset with additional fields for testing auto-adaptation.
This script copies a few sessions from an existing dataset and adds new fields to segment_results.
"""

import json
import os
import shutil
import random

# Configuration
SOURCE_DATASET = 'static/dataset/creative'
OUTPUT_DATASET = 'test_new_fields'
NUM_SESSIONS = 3  # Only take 3 sessions for quick testing

# New fields to add (field_name: calculation_function)
NEW_FIELDS = {
    'semantic_change_v2': lambda item: round(item['residual_vector_norm'] * random.uniform(0.7, 1.3), 4),
    'ai_contribution_rate': lambda item: 1.0 if item['source'] == 'api' else round(random.uniform(0, 0.3), 2),
    'editing_intensity': lambda item: round(random.uniform(0.1, 1.0), 3),
    'coherence_score': lambda item: round(random.uniform(0.5, 1.0), 3),
}


def create_test_dataset():
    print("🚀 Creating test dataset...")

    # 1. Create directories
    os.makedirs(f'{OUTPUT_DATASET}/json', exist_ok=True)
    os.makedirs(f'{OUTPUT_DATASET}/segment_results', exist_ok=True)
    print(f"📁 Created directories: {OUTPUT_DATASET}/")

    # 2. Copy session.csv (only first N sessions)
    print(f"📋 Processing session.csv...")
    with open(f'{SOURCE_DATASET}/session.csv', 'r') as f:
        lines = f.readlines()

    if len(lines) <= NUM_SESSIONS:
        print(
            f"⚠️  Warning: Source has only {len(lines)-1} sessions, using all")
        NUM_SESSIONS_ACTUAL = len(lines) - 1
    else:
        NUM_SESSIONS_ACTUAL = NUM_SESSIONS

    with open(f'{OUTPUT_DATASET}/session.csv', 'w') as f:
        f.write(lines[0])  # header
        f.writelines(lines[1:NUM_SESSIONS_ACTUAL+1])

    print(f"✅ Created session.csv with {NUM_SESSIONS_ACTUAL} sessions")

    # 3. Get session IDs
    sessions = []
    for line in lines[1:NUM_SESSIONS_ACTUAL+1]:
        parts = line.strip().split(',')
        if len(parts) > 0 and parts[0]:
            sessions.append(parts[0])

    print(f"📝 Session IDs: {sessions}")

    # 4. Copy json files (no modification)
    print(f"📄 Copying json files...")
    for sid in sessions:
        src = f'{SOURCE_DATASET}/json/{sid}.json'
        dst = f'{OUTPUT_DATASET}/json/{sid}.json'
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"  ✓ {sid}.json")
        else:
            print(f"  ⚠️ {sid}.json not found")

    # 5. Process segment_results files (add new fields)
    print(f"🔨 Processing segment_results files and adding new fields...")
    total_segments = 0

    for sid in sessions:
        src = f'{SOURCE_DATASET}/segment_results/{sid}.json'
        dst = f'{OUTPUT_DATASET}/segment_results/{sid}.json'

        if not os.path.exists(src):
            print(f"  ⚠️ {sid}.json not found in segment_results")
            continue

        with open(src, 'r') as f:
            data = json.load(f)

        # Add new fields to each segment
        for item in data:
            for field_name, calc_func in NEW_FIELDS.items():
                try:
                    item[field_name] = calc_func(item)
                except Exception as e:
                    print(f"    ⚠️ Error calculating {field_name}: {e}")
                    item[field_name] = 0.0

        with open(dst, 'w') as f:
            json.dump(data, f, indent=2)

        total_segments += len(data)
        print(f"  ✓ {sid}.json ({len(data)} segments)")

    print(f"\n✅ Dataset created successfully!")
    print(f"📊 Statistics:")
    print(f"   - Sessions: {len(sessions)}")
    print(f"   - Total segments: {total_segments}")
    print(f"   - New fields added: {list(NEW_FIELDS.keys())}")
    print(f"\n📦 Next steps:")
    print(f"   1. cd to project root")
    print(f"   2. Run: zip -r {OUTPUT_DATASET}.zip {OUTPUT_DATASET}/")
    print(f"   3. Upload {OUTPUT_DATASET}.zip via the web interface")
    print(f"   4. Select '{OUTPUT_DATASET}' from Dataset dropdown")
    print(f"   5. Check console for field detection logs")


if __name__ == '__main__':
    create_test_dataset()

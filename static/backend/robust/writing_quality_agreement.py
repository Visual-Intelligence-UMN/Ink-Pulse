import pandas as pd
import numpy as np
from scipy.stats import spearmanr, kendalltau
import itertools
import os

datasets = ["argumentative", "creative"]
N_RUNS = 3

MODELS = {
    "GPT-5.6 Terra": "openai.gpt-5.6-terra",
    "Claude Haiku 4.5": "anthropic.claude-haiku-4-5"
}

for dataset in datasets:
    print(f"\n=== {dataset} ===")
    run_dfs = []
    for i in range(1, N_RUNS + 1):
        fname = os.path.join("writing_quality", f"writing_quality_comparison_{dataset}_{i}.xlsx")
        try:
            df = pd.read_excel(fname, sheet_name="All Results")
            run_dfs.append(df)
            print(f"  Loaded run {i}: {len(df)} rows, {df['session_id'].nunique()} sessions")
        except Exception as e:
            print(f"  Error run {i}: {e}")

    if not run_dfs:
        continue

    print()
    for model_name, model_id in MODELS.items():
        sp_vals, kt_vals, pct_vals = [], [], []
        for (i, df1), (j, df2) in itertools.combinations(enumerate(run_dfs), 2):
            m1 = df1[df1["model"] == model_id].set_index("session_id")["total_score"]
            m2 = df2[df2["model"] == model_id].set_index("session_id")["total_score"]
            common = m1.index.intersection(m2.index)
            if len(common) < 2:
                continue
            a, b = m1[common].values, m2[common].values
            sp, _ = spearmanr(a, b)
            kt, _ = kendalltau(a, b)
            concordant = discordant = 0
            for idx1, idx2 in itertools.combinations(range(len(a)), 2):
                a_dir = int(a[idx1] > a[idx2]) - int(a[idx1] < a[idx2])
                b_dir = int(b[idx1] > b[idx2]) - int(b[idx1] < b[idx2])
                if a_dir != 0 and b_dir != 0:
                    if a_dir == b_dir:
                        concordant += 1
                    else:
                        discordant += 1
            pct = concordant / (concordant + discordant) * 100 if (concordant + discordant) > 0 else None
            sp_vals.append(sp)
            kt_vals.append(kt)
            if pct:
                pct_vals.append(pct)

        print(f"  [{model_name}] within-model cross-run:")
        print(f"    Spearman:   {np.mean(sp_vals):.4f} (range {min(sp_vals):.4f}-{max(sp_vals):.4f})")
        print(f"    Kendall:    {np.mean(kt_vals):.4f} (range {min(kt_vals):.4f}-{max(kt_vals):.4f})")
        print(f"    Concordant: {np.mean(pct_vals):.2f}%")
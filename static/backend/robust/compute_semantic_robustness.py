import pandas as pd
import numpy as np
from scipy.stats import spearmanr, kendalltau
import itertools
import os

datasets = ["argumentative", "creative"]
N_RUNS = 5

for dataset in datasets:
    print(f"\n=== {dataset} ===")
    all_dfs = []
    for i in range(1, N_RUNS + 1):
        fname = os.path.join(dataset, f"semantic_change_robustness_{i}.xlsx")
        try:
            df = pd.read_excel(fname, sheet_name="Raw Distance")
            seg_cols = [c for c in df.columns if c.startswith("seg_")]
            df_clean = df[["session_id"] + seg_cols].copy()
            df_clean["run"] = i
            all_dfs.append(df_clean)
            print(f"  Loaded run {i}: {len(df)} sessions")
        except Exception as e:
            print(f"  Error run {i}: {e}")

    if len(all_dfs) < 2:
        continue

    seg_cols = [c for c in all_dfs[0].columns if c.startswith("seg_")]

    # Pairwise Spearman and Kendall across all run pairs
    spearman_vals, kendall_vals, concordant_pcts = [], [], []

    for (i, df1), (j, df2) in itertools.combinations(enumerate(all_dfs), 2):
        merged = pd.merge(
            df1[["session_id"] + seg_cols].rename(columns={c: f"{c}_a" for c in seg_cols}),
            df2[["session_id"] + seg_cols].rename(columns={c: f"{c}_b" for c in seg_cols}),
            on="session_id"
        )
        a_cols = [f"{c}_a" for c in seg_cols]
        b_cols = [f"{c}_b" for c in seg_cols]
        a_vals = merged[a_cols].values.flatten()
        b_vals = merged[b_cols].values.flatten()
        mask = ~np.isnan(a_vals) & ~np.isnan(b_vals) & (a_vals > 0) & (b_vals > 0)
        a_v, b_v = a_vals[mask], b_vals[mask]

        sp, _ = spearmanr(a_v, b_v)
        kt, _ = kendalltau(a_v, b_v)

        # Pairwise concordant %
        concordant = discordant = 0
        for idx1, idx2 in itertools.combinations(range(len(a_v)), 2):
            a_dir = int(a_v[idx1] > a_v[idx2]) - int(a_v[idx1] < a_v[idx2])
            b_dir = int(b_v[idx1] > b_v[idx2]) - int(b_v[idx1] < b_v[idx2])
            if a_dir != 0 and b_dir != 0:
                if a_dir == b_dir:
                    concordant += 1
                else:
                    discordant += 1
        pct = concordant / (concordant + discordant) * 100 if (concordant + discordant) > 0 else None

        spearman_vals.append(sp)
        kendall_vals.append(kt)
        if pct:
            concordant_pcts.append(pct)
        print(f"  Run {i+1} vs Run {j+1}: Spearman={sp:.4f}, Kendall={kt:.4f}, Concordant={pct:.2f}%")

    print(f"\n  Mean Spearman:   {np.mean(spearman_vals):.4f} (range {min(spearman_vals):.4f}-{max(spearman_vals):.4f})")
    print(f"  Mean Kendall:    {np.mean(kendall_vals):.4f} (range {min(kendall_vals):.4f}-{max(kendall_vals):.4f})")
    print(f"  Mean Concordant: {np.mean(concordant_pcts):.2f}%")
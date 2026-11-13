"""
compare_models.py
=================
Compares writing-quality scores across three models for one or more datasets:
  1. openai.gpt-5.6-terra        — Excel comparison file (idea_score, coherence_score, total_score)
  2. anthropic.claude-haiku-4-5  — same Excel file
  3. gpt-4o                      — per-session JSON files in dataset/{dataset}/segment_results/
                                   (score field per segment; aggregated to session level)

Correlation metrics match those produced by the original Excel pipeline:
  spearman_r, spearman_p, kendall_tau, kendall_p,
  concordant_pairs, discordant_pairs, tied_pairs, total_pairs, pct_concordant

Usage:
    python compare_models.py
"""

import json
import numpy as np
import pandas as pd
from itertools import combinations
from pathlib import Path
from scipy import stats
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

# ═══════════════════════════════ CONFIG ═══════════════════════════════════════

DATASETS = [
    ("argumentative", "writing_quality_comparison_argumentative.xlsx"),
    ("creative",      "writing_quality_comparison_creative.xlsx"),
]

# How to collapse per-segment gpt-4o scores → one session score
# Options: "mean" | "sum" | "max" | "min" | "median"
GPT4O_AGGREGATION = "mean"

OUTPUT_PATH = "model_comparison_results.xlsx"

# Resolves to the same root the original pipeline uses
_script_dir = Path(__file__).resolve().parent
_static_dir  = (_script_dir / ".." / "..").resolve()

# ══════════════════════════════════════════════════════════════════════════════


# ── Styling ───────────────────────────────────────────────────────────────────

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(color="FFFFFF", bold=True, name="Arial", size=11)
ALT_FILL    = PatternFill("solid", fgColor="EBF3FB")
BODY_FONT   = Font(name="Arial", size=10)
BOLD_FONT   = Font(name="Arial", size=10, bold=True)
ITALIC_FONT = Font(name="Arial", size=9, italic=True)
THIN_SIDE   = Side(style="thin", color="B0B0B0")
THIN_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE,
                     top=THIN_SIDE,  bottom=THIN_SIDE)
GREEN_FILL  = PatternFill("solid", fgColor="C6EFCE")
RED_FILL    = PatternFill("solid", fgColor="FFC7CE")
ORANGE_FILL = PatternFill("solid", fgColor="FFEB9C")
GREY_FILL   = PatternFill("solid", fgColor="D9D9D9")

DATASET_TAB_COLORS = ["1F78B4", "E31A1C", "33A02C", "FF7F00", "6A3D9A"]
COMBINED_TAB_COLOR = "5A5A5A"

MODEL_COLORS = {
    "gpt-4o":                     "ED7D31",
    "openai.gpt-5.6-terra":       "4472C4",
    "anthropic.claude-haiku-4-5": "70AD47",
}

FRIENDLY = {
    "session_id":      "Session ID",
    "dataset":         "Dataset",
    "terra_idea":      "Terra – Idea",
    "terra_coherence": "Terra – Coherence",
    "terra_total":     "Terra – Total",
    "haiku_idea":      "Haiku – Idea",
    "haiku_coherence": "Haiku – Coherence",
    "haiku_total":     "Haiku – Total",
    "gpt4o_score":     "GPT-4o Score",
    "mean_score":      "Mean Score",
    "std_score":       "Std Dev",
    "score_range":     "Range (max−min)",
    "agree":           "Agree (≤0.5)",
}

SCORE_COLS = ["terra_idea", "terra_coherence", "terra_total",
              "haiku_idea", "haiku_coherence", "haiku_total", "gpt4o_score"]


# ── Cell helpers ──────────────────────────────────────────────────────────────

def _sc(cell, font=None, fill=None, align="center", border=True, fmt=None):
    if font:    cell.font   = font
    if fill:    cell.fill   = fill
    if border:  cell.border = THIN_BORDER
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    if fmt:     cell.number_format = fmt

def _hdr(ws, row, col, value, align="center"):
    cell = ws.cell(row=row, column=col, value=value)
    _sc(cell, font=HEADER_FONT, fill=HEADER_FILL, align=align)
    return cell

def _body(ws, row, col, value, alt=False, fmt=None, font=None, fill=None):
    cell = ws.cell(row=row, column=col, value=value)
    _sc(cell, font=font or BODY_FONT,
        fill=fill if fill is not None else (ALT_FILL if alt else None),
        fmt=fmt)
    return cell

def _autofit(ws, min_w=10, max_w=44):
    for col in ws.columns:
        w = max((len(str(c.value or "")) for c in col), default=0)
        ws.column_dimensions[get_column_letter(col[0].column)].width = \
            max(min_w, min(max_w, w + 2))


# ── Data loading ──────────────────────────────────────────────────────────────

def load_excel_scores(path: str) -> pd.DataFrame:
    wb   = load_workbook(path, data_only=True)
    ws   = wb.active
    rows = list(ws.iter_rows(values_only=True))
    df   = pd.DataFrame(rows[1:], columns=rows[0]).dropna(subset=["session_id","model"])
    for c in ["idea_score", "coherence_score", "total_score"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["session_id"] = df["session_id"].astype(str)
    return df


def load_gpt4o_scores(dataset_name: str, aggregation: str = "mean") -> pd.DataFrame:
    seg_dir = _static_dir / "dataset" / dataset_name / "segment_results"
    if not seg_dir.exists():
        print(f"  [WARN] Not found: {seg_dir} — gpt-4o will be empty for '{dataset_name}'")
        return pd.DataFrame(columns=["session_id", "gpt4o_score"])

    agg_fn = {"mean": np.mean, "sum": np.sum, "max": np.max,
               "min": np.min, "median": np.median}.get(aggregation, np.mean)
    records = []
    for fpath in sorted(seg_dir.glob("*.json")):
        try:
            data   = json.loads(fpath.read_text(encoding="utf-8"))
            scores = [e["score"] for e in data if "score" in e]
            if scores:
                records.append({"session_id": fpath.stem,
                                 "gpt4o_score": round(float(agg_fn(scores)), 4)})
        except Exception as e:
            print(f"  [WARN] {fpath.name}: {e}")

    df = pd.DataFrame(records) if records else \
         pd.DataFrame(columns=["session_id", "gpt4o_score"])
    df["session_id"] = df["session_id"].astype(str)
    print(f"  [INFO] gpt-4o: {len(df)} sessions loaded from '{dataset_name}'")
    return df


def build_wide(excel_df: pd.DataFrame, gpt4o_df: pd.DataFrame) -> pd.DataFrame:
    terra = (excel_df[excel_df["model"] == "openai.gpt-5.6-terra"]
             .rename(columns={"idea_score": "terra_idea",
                               "coherence_score": "terra_coherence",
                               "total_score": "terra_total"})
             [["session_id", "terra_idea", "terra_coherence", "terra_total"]])
    haiku = (excel_df[excel_df["model"] == "anthropic.claude-haiku-4-5"]
             .rename(columns={"idea_score": "haiku_idea",
                               "coherence_score": "haiku_coherence",
                               "total_score": "haiku_total"})
             [["session_id", "haiku_idea", "haiku_coherence", "haiku_total"]])
    wide = terra.merge(haiku, on="session_id", how="outer")
    if not gpt4o_df.empty:
        wide = wide.merge(gpt4o_df, on="session_id", how="outer")
    else:
        wide["gpt4o_score"] = np.nan
    return wide.sort_values("session_id").reset_index(drop=True)


# ── Metric computation ────────────────────────────────────────────────────────

def _concordant_discordant_tied(x: np.ndarray, y: np.ndarray):
    """
    Brute-force O(n²) count of concordant, discordant, and tied pairs.
    Matches the exact values produced by the original Excel pipeline.
    """
    C = D = T = 0
    for i, j in combinations(range(len(x)), 2):
        dx = x[i] - x[j]
        dy = y[i] - y[j]
        prod = dx * dy
        if   prod > 0: C += 1
        elif prod < 0: D += 1
        else:          T += 1
    return C, D, T


def compute_correlation_metrics(a: pd.Series, b: pd.Series) -> dict:
    """
    Compute the exact same metrics as the original Excel Correlation sheet:
      spearman_r, spearman_p,
      kendall_tau, kendall_p,
      concordant_pairs, discordant_pairs, tied_pairs, total_pairs, pct_concordant
    """
    mask = a.notna() & b.notna()
    av, bv = a[mask].values, b[mask].values
    n = len(av)

    if n < 3:
        return {k: "n/a" for k in ["spearman_r", "spearman_p",
                                    "kendall_tau", "kendall_p",
                                    "concordant_pairs", "discordant_pairs",
                                    "tied_pairs", "total_pairs", "pct_concordant"]}

    sr, sp = stats.spearmanr(av, bv)
    kt, kp = stats.kendalltau(av, bv)

    C, D, T = _concordant_discordant_tied(av, bv)
    total   = C + D + T
    pct     = round(C / (C + D) * 100, 4) if (C + D) > 0 else 0.0

    return {
        "spearman_r":       round(float(sr), 4),
        "spearman_p":       round(float(sp), 4),
        "kendall_tau":      round(float(kt), 4),
        "kendall_p":        round(float(kp), 4),
        "concordant_pairs": C,
        "discordant_pairs": D,
        "tied_pairs":       T,
        "total_pairs":      total,
        "pct_concordant":   pct,
    }


def compute_all_correlations(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Run the correlation metrics for every model pair on total scores.
    Pairs: Terra vs Haiku, Terra vs GPT-4o, Haiku vs GPT-4o.
    """
    pairs = [
        ("terra_total", "haiku_total",  "Terra vs Haiku"),
        ("terra_total", "gpt4o_score",  "Terra vs GPT-4o"),
        ("haiku_total", "gpt4o_score",  "Haiku vs GPT-4o"),
    ]
    rows = []
    for col_a, col_b, label in pairs:
        if col_a not in wide.columns or col_b not in wide.columns:
            continue
        metrics = compute_correlation_metrics(wide[col_a], wide[col_b])
        n       = wide[[col_a, col_b]].dropna().shape[0]
        rows.append({"pair": label, "n": n, **metrics})
    return pd.DataFrame(rows)


def compute_summary(wide: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in SCORE_COLS if c in wide.columns]
    rows = []
    for name, fn in [("Mean","mean"),("Std Dev","std"),
                     ("Median","median"),("Min","min"),("Max","max")]:
        row = {"Statistic": name}
        for c in cols:
            row[c] = round(float(getattr(wide[c].dropna(), fn)()), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def compute_agreement(wide: pd.DataFrame) -> pd.DataFrame:
    avail = [c for c in ["terra_total","haiku_total","gpt4o_score"]
             if c in wide.columns]
    sub   = wide[["session_id"] + avail].dropna(subset=avail).copy()
    sub["score_range"] = sub[avail].max(axis=1) - sub[avail].min(axis=1)
    sub["agree"]       = sub["score_range"] <= 0.5
    sub["mean_score"]  = sub[avail].mean(axis=1).round(3)
    sub["std_score"]   = sub[avail].std(axis=1).round(3)
    return sub[["session_id"] + avail +
               ["mean_score","std_score","score_range","agree"]]


def compute_distribution(wide: pd.DataFrame) -> dict:
    mapping = {"GPT-4o":"gpt4o_score","Terra":"terra_total","Haiku":"haiku_total"}
    result  = {}
    for lbl, col in mapping.items():
        if col not in wide.columns: continue
        s  = wide[col].dropna().round().astype(int)
        ct = s.value_counts().sort_index().reset_index()
        ct.columns = ["Score","Count"]
        result[lbl] = ct
    return result


# ── Sheet writers ─────────────────────────────────────────────────────────────

def write_raw(ws, wide: pd.DataFrame, has_dataset_col=False):
    cols = (["session_id","dataset"] if has_dataset_col else ["session_id"]) + \
           [c for c in SCORE_COLS if c in wide.columns]
    for ci, c in enumerate(cols, 1):
        _hdr(ws, 1, ci, FRIENDLY.get(c, c))
    for ri, (_, row) in enumerate(wide[cols].iterrows(), 2):
        alt = ri % 2 == 0
        for ci, c in enumerate(cols, 1):
            val = row[c]
            fmt = "@" if c in ("session_id","dataset") else "0.00"
            _body(ws, ri, ci, None if pd.isna(val) else val, alt=alt, fmt=fmt)
    ws.freeze_panes = "B2"
    _autofit(ws)


def write_summary(ws, summary_df: pd.DataFrame):
    cols = list(summary_df.columns)
    for ci, c in enumerate(cols, 1):
        _hdr(ws, 1, ci, FRIENDLY.get(c, c))
    for ri, (_, row) in enumerate(summary_df.iterrows(), 2):
        for ci, c in enumerate(cols, 1):
            val = row[c]
            fmt = "0.0000" if c != "Statistic" else "@"
            _body(ws, ri, ci,
                  None if isinstance(val, float) and np.isnan(val) else val,
                  alt=ri%2==0, fmt=fmt)
    _autofit(ws)


def write_correlations(ws, corr_df: pd.DataFrame):
    """
    Writes a Correlation sheet with the exact same metrics as the original
    Excel pipeline, extended to all three model pairs.
    Layout: one block per model pair (metric | value), separated by blank rows.
    """
    METRIC_LABELS = {
        "spearman_r":       "spearman_r",
        "spearman_p":       "spearman_p",
        "kendall_tau":      "kendall_tau",
        "kendall_p":        "kendall_p",
        "concordant_pairs": "concordant_pairs",
        "discordant_pairs": "discordant_pairs",
        "tied_pairs":       "tied_pairs",
        "total_pairs":      "total_pairs",
        "pct_concordant":   "pct_concordant",
    }
    INT_METRICS = {"concordant_pairs","discordant_pairs","tied_pairs","total_pairs"}

    # Column headers
    _hdr(ws, 1, 1, "metric")
    for ci, row in enumerate(corr_df.itertuples(), 2):
        _hdr(ws, 1, ci, f"{row.pair}\n(n={row.n})")

    # One row per metric
    for ri, (key, label) in enumerate(METRIC_LABELS.items(), 2):
        # Metric name (left-aligned)
        cell = ws.cell(row=ri, column=1, value=label)
        _sc(cell, font=BODY_FONT, fill=ALT_FILL if ri%2==0 else None, align="left")

        for ci, (_, pair_row) in enumerate(corr_df.iterrows(), 2):
            val = pair_row.get(key, "n/a")
            if isinstance(val, float) and np.isnan(val):
                val = "n/a"
            fmt = "#,##0" if key in INT_METRICS else \
                  "0.0000" if val != "n/a" else "@"
            _body(ws, ri, ci, val, alt=ri%2==0, fmt=fmt)

    # Note about pct_concordant formula
    note_row = len(METRIC_LABELS) + 3
    note = ws.cell(row=note_row, column=1,
        value="pct_concordant = concordant / (concordant + discordant) × 100  "
              "(tied pairs excluded, matching original pipeline)")
    note.font      = ITALIC_FONT
    note.alignment = Alignment(horizontal="left")
    ws.merge_cells(start_row=note_row, start_column=1,
                   end_row=note_row,   end_column=len(corr_df)+1)

    _autofit(ws)
    ws.column_dimensions["A"].width = 22


def write_agreement(ws, agree_df: pd.DataFrame):
    score_cols = [c for c in ["terra_total","haiku_total","gpt4o_score"]
                  if c in agree_df.columns]
    cols = ["session_id"] + score_cols + \
           ["mean_score","std_score","score_range","agree"]
    for ci, c in enumerate(cols, 1):
        _hdr(ws, 1, ci, FRIENDLY.get(c, c))

    for ri, (_, row) in enumerate(agree_df[cols].iterrows(), 2):
        agreed = bool(row["agree"])
        alt    = ri % 2 == 0
        for ci, c in enumerate(cols, 1):
            val = row[c]
            if isinstance(val, (bool, np.bool_)): val = "Yes" if val else "No"
            elif pd.isna(val):                     val = None
            fill = (GREEN_FILL if agreed else RED_FILL) if c == "agree" else \
                   (ALT_FILL if alt else None)
            cell = ws.cell(row=ri, column=ci, value=val)
            _sc(cell, font=BODY_FONT, fill=fill,
                fmt="0.00" if c not in ("session_id","agree") else "@")

    n, total = int(agree_df["agree"].sum()), len(agree_df)
    note = ws.cell(row=total+3, column=1,
        value=f"Sessions where all models agree within ±0.5: "
              f"{n} / {total} ({100*n/total:.1f}%)")
    note.font = BOLD_FONT
    ws.freeze_panes = "B2"
    _autofit(ws)


def write_distribution(ws, dist_dict: dict):
    all_scores = sorted({s for df in dist_dict.values() for s in df["Score"]})
    models     = list(dist_dict.keys())
    n          = len(all_scores)

    _hdr(ws, 1, 1, "Score")
    for ci, m in enumerate(models, 2):
        _hdr(ws, 1, ci, m)
    for ri, score in enumerate(all_scores, 2):
        alt = ri % 2 == 0
        _body(ws, ri, 1, score, alt=alt)
        for ci, m in enumerate(models, 2):
            df  = dist_dict.get(m, pd.DataFrame())
            row = df[df["Score"] == score]
            val = int(row["Count"].values[0]) if not row.empty else 0
            _body(ws, ri, ci, val, alt=alt)

    chart = BarChart()
    chart.type, chart.grouping = "col", "clustered"
    chart.title         = "Score Distribution by Model"
    chart.y_axis.title  = "Number of Sessions"
    chart.x_axis.title  = "Score"
    chart.width, chart.height = 22, 14
    cats = Reference(ws, min_col=1, min_row=2, max_row=n+1)
    for ci, m in enumerate(models, 2):
        ref = Reference(ws, min_col=ci, min_row=1, max_row=n+1)
        chart.add_data(ref, titles_from_data=True)
        color_key = {"GPT-4o":"gpt-4o","Terra":"openai.gpt-5.6-terra",
                     "Haiku":"anthropic.claude-haiku-4-5"}.get(m, m)
        chart.series[-1].graphicalProperties.solidFill = \
            MODEL_COLORS.get(color_key, "808080")
    chart.set_categories(cats)
    ws.add_chart(chart, "F2")
    _autofit(ws)


def write_pairwise(ws, wide: pd.DataFrame):
    pairs = [("terra_total","haiku_total","Terra − Haiku"),
             ("terra_total","gpt4o_score","Terra − GPT-4o"),
             ("haiku_total","gpt4o_score","Haiku − GPT-4o")]
    avail = [(ca,cb,lbl) for ca,cb,lbl in pairs
             if ca in wide.columns and cb in wide.columns]

    _hdr(ws, 1, 1, "Session ID")
    for ci, (_,_,lbl) in enumerate(avail, 2):
        _hdr(ws, 1, ci, lbl)

    for ri, (_, row) in enumerate(wide.iterrows(), 2):
        alt = ri % 2 == 0
        _body(ws, ri, 1, row["session_id"], alt=alt, fmt="@")
        for ci, (ca, cb, _) in enumerate(avail, 2):
            a, b = row.get(ca), row.get(cb)
            diff = None if pd.isna(a) or pd.isna(b) else round(float(a)-float(b), 3)
            fill = ORANGE_FILL if diff is not None and abs(diff) >= 2 else \
                   (ALT_FILL if alt else None)
            cell = ws.cell(row=ri, column=ci, value=diff)
            _sc(cell, font=BODY_FONT, fill=fill, fmt="0.000")

    last = len(wide) + 3
    ws.cell(row=last, column=1, value="Mean |diff|").font = BOLD_FONT
    for ci, (ca, cb, _) in enumerate(avail, 2):
        sub = wide[[ca, cb]].dropna()
        val = round((sub[ca]-sub[cb]).abs().mean(), 4) if not sub.empty else None
        _body(ws, last, ci, val, font=BOLD_FONT, fmt="0.0000")

    ws.cell(row=last+1, column=1,
            value="Orange = difference ≥ 2 points.").font = ITALIC_FONT
    ws.freeze_panes = "B2"
    _autofit(ws)


def write_cross_dataset(ws, combined: pd.DataFrame):
    datasets     = combined["dataset"].unique()
    model_specs  = [("Terra","terra_total"),
                    ("Haiku","haiku_total"),
                    ("GPT-4o","gpt4o_score")]

    # ── Summary table ──────────────────────────────────────────────────────
    sum_cols = ["Dataset","N Sessions"] + \
               [f"{m} Mean" for m,_ in model_specs] + \
               [f"{m} Std"  for m,_ in model_specs]
    for ci, c in enumerate(sum_cols, 1):
        _hdr(ws, 1, ci, c)

    def ds_row(ds, sub):
        r = {"Dataset": ds,
             "N Sessions": int(sub["session_id"].nunique())}
        for m, col in model_specs:
            r[f"{m} Mean"] = round(sub[col].mean(), 4) if col in sub else None
            r[f"{m} Std"]  = round(sub[col].std(),  4) if col in sub else None
        return r

    row_data = [ds_row(ds, combined[combined["dataset"]==ds]) for ds in datasets]
    row_data.append(ds_row("COMBINED", combined))

    for ri, r in enumerate(row_data, 2):
        is_comb = r["Dataset"] == "COMBINED"
        alt     = ri % 2 == 0
        for ci, c in enumerate(sum_cols, 1):
            val  = r.get(c)
            fill = GREY_FILL if is_comb else (ALT_FILL if alt else None)
            font = BOLD_FONT if is_comb else BODY_FONT
            fmt  = ("#,##0" if c == "N Sessions" else
                    "0.0000" if c not in ("Dataset",) else "@")
            cell = ws.cell(row=ri,column=ci,
                           value=None if (isinstance(val,float) and np.isnan(val))
                                 else val)
            _sc(cell, font=font, fill=fill, fmt=fmt)

    # ── Chart ──────────────────────────────────────────────────────────────
    # Write a small helper table (datasets only) for chart data
    cs = len(sum_cols) + 2   # chart-table start column
    ws.cell(row=1, column=cs, value="Dataset")
    avail_models = [m for m,col in model_specs if col in combined.columns]
    for ci, m in enumerate(avail_models, cs+1):
        ws.cell(row=1, column=ci, value=m)
    for ri, ds in enumerate(datasets, 2):
        sub = combined[combined["dataset"]==ds]
        ws.cell(row=ri, column=cs, value=ds)
        for ci, m in enumerate(avail_models, cs+1):
            col = dict(model_specs)[m]
            ws.cell(row=ri, column=ci,
                    value=round(sub[col].mean(), 4) if col in sub.columns else None)

    nd = len(datasets)
    chart = BarChart()
    chart.type, chart.grouping = "col", "clustered"
    chart.title         = "Mean Total Score by Dataset and Model"
    chart.y_axis.title  = "Mean Score"
    chart.x_axis.title  = "Dataset"
    chart.width, chart.height = 22, 14
    cats = Reference(ws, min_col=cs, min_row=2, max_row=nd+1)
    for ci, m in enumerate(avail_models, cs+1):
        ref = Reference(ws, min_col=ci, min_row=1, max_row=nd+1)
        chart.add_data(ref, titles_from_data=True)
        color_key = {"Terra":"openai.gpt-5.6-terra",
                     "Haiku":"anthropic.claude-haiku-4-5",
                     "GPT-4o":"gpt-4o"}.get(m, m)
        chart.series[-1].graphicalProperties.solidFill = \
            MODEL_COLORS.get(color_key, "808080")
    chart.set_categories(cats)
    ws.add_chart(chart, f"B{nd+4}")

    _autofit(ws)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    wb = Workbook()
    wb.remove(wb.active)

    all_wides = []

    for idx, (ds_name, excel_path) in enumerate(DATASETS):
        print(f"\n{'═'*60}")
        print(f"  Dataset: {ds_name.upper()}")
        print(f"{'═'*60}")

        excel_df = load_excel_scores(excel_path)
        print(f"  Excel: {len(excel_df)} rows, "
              f"{excel_df['session_id'].nunique()} sessions")

        gpt4o_df = load_gpt4o_scores(ds_name, GPT4O_AGGREGATION)
        wide     = build_wide(excel_df, gpt4o_df)
        wide.insert(1, "dataset", ds_name)
        all_wides.append(wide)

        corr_df = compute_all_correlations(wide)
        summary = compute_summary(wide.drop(columns=["dataset"]))
        agree   = compute_agreement(wide)
        dist    = compute_distribution(wide)

        # Console output
        print(f"\n  Correlations:")
        print(corr_df.to_string(index=False))
        n_agree = int(agree["agree"].sum())
        print(f"\n  Agreement within ±0.5: {n_agree}/{len(agree)} "
              f"({100*n_agree/len(agree):.1f}%)")

        tab_color = DATASET_TAB_COLORS[idx % len(DATASET_TAB_COLORS)]
        prefix    = ds_name[:4].capitalize()

        def new_ws(title):
            ws = wb.create_sheet(title=f"{prefix} – {title}")
            ws.sheet_properties.tabColor = tab_color
            return ws

        write_raw(new_ws("Raw Data"),         wide.drop(columns=["dataset"]))
        write_summary(new_ws("Summary"),      summary)
        write_correlations(new_ws("Correlations"), corr_df)
        write_agreement(new_ws("Agreement"),  agree)
        write_distribution(new_ws("Distribution"), dist)
        write_pairwise(new_ws("Differences"), wide.drop(columns=["dataset"]))

    # ── Combined ──────────────────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print("  Building combined view …")
    combined = pd.concat(all_wides, ignore_index=True)

    def new_cws(title):
        ws = wb.create_sheet(title=f"Combined – {title}")
        ws.sheet_properties.tabColor = COMBINED_TAB_COLOR
        return ws

    write_raw(new_cws("Raw"),          combined, has_dataset_col=True)
    write_summary(new_cws("Summary"),  compute_summary(combined.drop(columns=["dataset"])))
    write_correlations(new_cws("Correlations"), compute_all_correlations(combined))
    write_agreement(new_cws("Agreement"),       compute_agreement(combined))

    ws_cross = wb.create_sheet("Cross-Dataset")
    ws_cross.sheet_properties.tabColor = COMBINED_TAB_COLOR
    write_cross_dataset(ws_cross, combined)

    wb.save(OUTPUT_PATH)
    print(f"\n[INFO] Saved → {OUTPUT_PATH}")
    print(f"       {len(wb.sheetnames)} sheets: {wb.sheetnames}")


if __name__ == "__main__":
    main()
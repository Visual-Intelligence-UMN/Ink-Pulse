// Feature catalog for InkPulse pattern interpretation and deterministic evaluation (App. B.1).
// Domain knowledge (units, meanings, allowed operations, roles) lives here rather than in the prompt.

export const BLOCK_DEFINITION =
  'A block is one contiguous writing segment by a single contributor ("user" = Human, "api" = AI) ' +
  "within a co-writing session. Reference blocks are ordered chronologically with 0-based indices " +
  "0..N-1. Each block records its contributor (source), writing progress delta (0-1 fraction of final " +
  "session text), semantic change (residual_vector_norm), and duration in seconds (0 is a valid " +
  "recorded duration for instant AI insertions, not missing data). When provided, " +
  "session_relative_position is the block start's normalized elapsed-time position in [0, 1] across " +
  "the whole session.";

export const FEATURE_CATALOG = [
  {
    id: "source",
    label: "Source",
    level: "block",
    value_type: "source",
    unit: "categorical",
    operations: {
      source: ["="],
      count: ["=", "<", "<=", ">", ">="],
    },
    normalization: "categorical",
    provenance: "block.source",
    role: "descriptor",
    meaning:
      'Contributor of the block: "user" (Human) or "api" (AI). Supports single-block equality, ' +
      "full-window sequence lock ({sequence: true} = {reference: true}) for turn-taking order, " +
      "and counting matching blocks.",
  },
  {
    id: "progress",
    label: "Writing Progress",
    level: "block",
    value_type: "number",
    unit: "ratio_0_1",
    operations: {
      scalar: ["=", "<", "<=", ">", ">="],
      pairwise: ["=", "<", "<=", ">", ">="],
      ratio: ["=", "<", "<=", ">", ">="],
      trend: ["<", ">"],
      count: ["=", "<", "<=", ">", ">="],
      aggregate: ["=", "<", "<=", ">", ">="],
      "session-position": ["=", "<", "<=", ">", ">="],
    },
    normalization: "robust_iqr",
    provenance: "end_progress - start_progress",
    role: "descriptor",
    meaning:
      "Fraction of total session text added during the block on a 0-1 scale (e.g., 0.05 = 5% of " +
      "final text, not percentage points). For session-position, normalized start progress in [0, 1] " +
      "across the whole session.",
  },
  {
    id: "semantic_change",
    label: "Semantic Change",
    level: "block",
    value_type: "number",
    unit: "residual_vector_norm",
    operations: {
      scalar: ["=", "<", "<=", ">", ">="],
      pairwise: ["=", "<", "<=", ">", ">="],
      ratio: ["=", "<", "<=", ">", ">="],
      trend: ["<", ">"],
      count: ["=", "<", "<=", ">", ">="],
      aggregate: ["=", "<", "<=", ">", ">="],
    },
    normalization: "robust_iqr",
    provenance: "residual_vector_norm",
    role: "descriptor",
    meaning:
      "Novelty or semantic shift introduced by the block, measured as residual_vector_norm " +
      "(nonnegative number, typically 0 to ~1).",
  },
  {
    id: "time",
    label: "Duration",
    level: "block",
    value_type: "number",
    unit: "seconds",
    operations: {
      scalar: ["=", "<", "<=", ">", ">="],
      pairwise: ["=", "<", "<=", ">", ">="],
      ratio: ["=", "<", "<=", ">", ">="],
      trend: ["<", ">"],
      count: ["=", "<", "<=", ">", ">="],
      aggregate: ["=", "<", "<=", ">", ">="],
      "session-position": ["=", "<", "<=", ">", ">="],
    },
    normalization: "none",
    provenance: "end_time - start_time",
    role: "constraint-only",
    meaning:
      "Block duration in seconds (end_time - start_time; 0 is a valid recorded duration for AI " +
      "insertions, not missing). Constraint-only: never use as a ranking attribute. For " +
      "session-position, normalized elapsed time in [0, 1] at block start across the whole session.",
  },
];

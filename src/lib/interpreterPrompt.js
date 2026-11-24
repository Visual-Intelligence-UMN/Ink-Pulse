import { BLOCK_DEFINITION, FEATURE_CATALOG } from "./featureCatalog.js";

// Fig. 10 system prompt with only the required adaptations for fixed-window execution,
// reference-bound anchors, ratio defaults, primary/secondary attributes, and explicit source sequence.
export const SPEC_SYSTEM_PROMPT = `SYSTEM ROLE
You translate an analyst's observation of a human-AI co-writing episode into a PatternSpecDraft.
You do not generate SQL, executable code, database column names, or features that are absent from the supplied feature catalog.
INPUTS
You will receive:
- a natural-language description of the intended pattern;
- an ordered reference episode with block-level feature values;
- a feature catalog defining the available features and operations;
- default minimum and maximum candidate-span lengths; and
- the JSON schema for PatternSpecDraft.
INTERPRETATION RULES
- Treat the selected episode as a reference example, not as a complete statement of the analyst's intent.
- Use only feature identifiers from the supplied feature catalog.
- Never use a feature whose analytical role is "outcome" as a search attribute or hard constraint.
- Create a hard constraint only when the relationship is explicitly stated by the analyst or marked as analyst-confirmed in the input.
- Represent salient properties visible in the reference but not stated by the analyst as soft ranking attributes.
- Use fixed-length matching (min_blocks=max_blocks=N); bind anchors by reference position. Put other-length or skipped-block requests in unresolved.
- Represent required events using anchors. Represent permitted intermediate events using gap rules. Do not constrain intermediate blocks unless the analyst's description requires it.
- Use {offset} for positional blocks; create anchors only for explicit predicates (never >= 0 dummies).
- Emit a source sequence constraint only for full turn-taking order, not single-contributor filters.
- Do not invent numeric thresholds. If the analyst uses an ambiguous term such as "substantial," "brief," "many," or "similar," encode only an explicitly supported direction and place the unresolved magnitude under unresolved. For ratio without a stated multiplier, suggest a reference-valid default and alternatives.
- Record the provenance of every constraint and attribute as one of user-description, reference-example, system-default, or analyst-confirmed.
- When the description cannot be represented with the available features, report the limitation under unresolved rather than substituting an unrelated feature.
SUPPORTED CONSTRAINT TYPES
A constraint must use one of the following types:
- source: required contributor or event type;
- scalar: comparison with an explicit scalar value;
- pairwise: comparison between two bound blocks or anchors;
- ratio: ratio between two bound values;
- trend: an increasing or decreasing within-source trend;
- count: number of blocks satisfying a typed predicate;
- aggregate: minimum, maximum, mean, or sum over a candidate span; or
- session-position: normalized temporal or writing-progress position.
Use only operations listed for the selected feature in the feature catalog.
OUTPUT RULES
Return raw JSON conforming exactly to PatternSpecDraft.
Do not wrap the response in Markdown.
Do not include SQL, code, or prose outside the JSON object.
Place human-readable explanations in the explanations field (one faithful entry per attribute and constraint).
Place assumptions that do not affect execution in the assumptions field.
Place ambiguities requiring analyst confirmation in the unresolved field.`;

export function hashPrompt(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) {
    h = ((h * 33) ^ text.charCodeAt(i)) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}

export const SPEC_PROMPT_HASH = hashPrompt(SPEC_SYSTEM_PROMPT);

export const PATTERN_SPEC_SCHEMA_GUIDE = {
  schema_version: "1.0",
  span: {
    min_blocks: "integer === N",
    max_blocks: "integer === N",
    anchors: [
      {
        id: "string (unique)",
        selector: "'first-matching' | 'last-matching' | 'first-matching-after'",
        after: "null (or earlier anchor id when selector is 'first-matching-after')",
        predicate: "{feature_id, operator, value}",
      },
    ],
    gaps: [
      {
        left: "earlier anchor id",
        right: "later anchor id",
        min_blocks: "integer >= 0",
        max_blocks: "integer >= min_blocks",
        constrain_intermediate: "boolean",
      },
    ],
  },
  attributes: [
    {
      id: "string (unique)",
      feature_id: "'source' | 'progress' | 'semantic_change' (never 'time')",
      scope: "BlockRef | {window: true} | {window: true, source: 'user' | 'api'}",
      expected: "{value: single number or 'user'|'api' (never an array)} | {operator, value} | {trend: 'increasing' | 'decreasing'}",
      priority: "'primary' | 'secondary'",
      provenance: "Provenance",
    },
  ],
  constraints: [
    {
      id: "string (unique)",
      type: "'source' | 'scalar' | 'pairwise' | 'ratio' | 'trend' | 'count' | 'aggregate' | 'session-position'",
      feature_id: "catalog feature_id",
      left: "typed left operand (see constraint_forms)",
      operator: "typed operator",
      right: "typed right operand (see constraint_forms)",
      provenance: "Provenance",
    },
  ],
  assumptions: ["nonblank string"],
  unresolved: [{ term: "nonblank string", message: "nonblank string" }],
  explanations: [{ target_id: "attribute or constraint id", text: "nonblank string" }],
};

export const CONSTRAINT_FORMS_GUIDE = {
  rules: [
    "Top-level JSON keys must be exactly: schema_version, span, attributes, constraints, assumptions, unresolved, explanations.",
    "All IDs across span.anchors, attributes, and constraints must be nonblank and globally unique.",
    "Every attribute and constraint id must have a matching faithful entry in explanations (accurately reflecting fixed offsets, unexecuted gaps, and time = block duration rather than inter-block pause).",
    "Source values must be 'user' (Human) or 'api' (AI).",
    "Numeric operators: '=', '<', '<=', '>', '>='. Source operator: '=' only.",
    "BlockRef is {offset: integer} (0-based in [0, N-1]) or {anchor_id: string}. Use {offset: i} directly for positional blocks (first=0, last=N-1). Only create span.anchors for blocks identified by an explicit stated predicate (e.g., first AI block); never invent dummy >= 0 predicates, and never create anchors for count, trend, or aggregate constraints (anchors pin fixed offsets).",
    "FeatureRef is BlockRef optionally with feature_id (defaults to constraint feature_id; cross-feature requires matching nonempty catalog unit).",
    "Predicate is {feature_id, operator, value}.",
    "Attribute expected.value must be a single number or 'user'/'api' (never an array). To represent a per-block reference profile, emit one attribute per block with scope {offset: i} (or {anchor_id}); use scope {window: true} only with {trend: ...} or a single scalar summary.",
    "Attribute priority: use 'primary' for descriptor features central to the analyst's description (including features that also have hard constraints, since constraints filter direction/bounds while attributes rank similarity to the reference); use 'secondary' for standout reference-only cues or ambiguous/uncertain terms in unresolved.",
    "Include at least one descriptor attribute whenever any descriptor feature ('source', 'progress', 'semantic_change') is relevant to the pattern; do not copy routine unmentioned blocks from the reference.",
    "trend (< or >) computes an overall within-source least-squares slope (occasional rebounds are allowed).",
    "Only add unresolved entries for genuine ambiguities, unstated thresholds/multipliers, out-of-catalog concepts, or explicit requests for another span length or skipped blocks. Do not mark already-encoded constraints (e.g., whole-span sums/distributions, directional trend slopes/magnitudes or rebounds), soft similarity tolerances, or unstated ranking/comparison criteria as unresolved.",
    "If an ambiguous term could map to multiple features or contradicts the reference, place it in unresolved rather than guessing a hard constraint.",
    "Provenance is one of: 'user-description', 'reference-example', 'system-default', 'analyst-confirmed'.",
    "Features with role 'constraint-only' (such as 'time') cannot appear in attributes.",
  ],
  forms: {
    source_block: {
      type: "source",
      feature_id: "source",
      left: "BlockRef",
      operator: "=",
      right: "{value: 'user' | 'api'}",
    },
    source_sequence: {
      type: "source",
      feature_id: "source",
      left: "{sequence: true}",
      operator: "=",
      right: "{reference: true}",
    },
    scalar: {
      type: "scalar",
      feature_id: "numeric feature_id",
      left: "BlockRef",
      operator: "NumericOp",
      right: "{value: number}",
    },
    pairwise: {
      type: "pairwise",
      feature_id: "numeric feature_id",
      left: "BlockRef",
      operator: "NumericOp",
      right: "FeatureRef",
    },
    ratio: {
      type: "ratio",
      feature_id: "numeric feature_id",
      left: "{numerator: BlockRef, denominator: FeatureRef}",
      operator: "NumericOp",
      right: "{value: number (must hold on reference; if multiplier unstated, suggest a reference-valid default > 1 or < 1 matching direction), alternatives?: number[] (include alternatives when multiplier unstated)}",
    },
    trend: {
      type: "trend",
      feature_id: "numeric feature_id",
      left: "{source: 'user' | 'api'}",
      operator: "'<' | '>'",
      right: "{value: 0}",
    },
    count: {
      type: "count",
      feature_id: "feature_id matching left.predicate.feature_id",
      left: "{predicate: Predicate}",
      operator: "NumericOp",
      right: "{value: integer >= 0}",
    },
    aggregate: {
      type: "aggregate",
      feature_id: "numeric feature_id",
      left: "{aggregate: 'min' | 'max' | 'mean' | 'sum', source?: 'user' | 'api'}",
      operator: "NumericOp",
      right: "{value: number} | {aggregate: 'min' | 'max' | 'mean' | 'sum', source?: 'user' | 'api', feature_id?: string}",
    },
    "session-position": {
      type: "session-position",
      feature_id: "'time' | 'progress'",
      left: "{offset: 0} | {anchor_id: string}",
      operator: "NumericOp",
      right: "{value: number in [0, 1]}",
    },
  },
};

function round2(num) {
  return Math.round(num * 100) / 100;
}

function readChartBlockFields(block) {
  const startProgress = block.startProgress ?? block.start_progress;
  const endProgress = block.endProgress ?? block.end_progress;
  const startTime = block.startTime ?? block.start_time;
  const endTime = block.endTime ?? block.end_time;
  return {
    source: block.source,
    startProgress,
    endProgress,
    startTime,
    endTime,
    residual_vector_norm: block.residual_vector_norm,
  };
}

// Old-path signal conversion: reads both barChartY (camelCase) and lineChart (snake_case)
// field names, keeping chart units (percent 0-100, minutes) rounded to 2 decimals.
export function convertPatternToSignal(pattern) {
  if (!pattern || pattern.length === 0) return null;
  const sourceTrend = pattern.map((block) => block.source);
  const progressDiff = [];
  const timeDiff = [];
  const semanticDiff = [];
  for (let i = 0; i < pattern.length; i++) {
    const fields = readChartBlockFields(pattern[i]);
    progressDiff.push(round2(fields.endProgress - fields.startProgress));
    timeDiff.push(round2(fields.endTime - fields.startTime));
    semanticDiff.push(round2(fields.residual_vector_norm));
  }

  return {
    sourceTrend,
    progress: progressDiff,
    time: timeDiff,
    semantic_change: semanticDiff,
  };
}

// Converts chart-unit blocks (progress 0-100, time in minutes) into canonical catalog-unit
// blocks (progress 0-1, time in seconds) for the new spec interpreter and evaluator.
export function convertChartBlocksToCatalogBlocks(blocks, wholeBlocks = null) {
  if (!Array.isArray(blocks) || blocks.length === 0) {
    return { blocks: [], sessionContext: {} };
  }
  const toCatalogBlock = (block) => {
    const fields = readChartBlockFields(block);
    return {
      source: fields.source,
      start_progress: fields.startProgress / 100,
      end_progress: fields.endProgress / 100,
      start_time: fields.startTime * 60,
      end_time: fields.endTime * 60,
      residual_vector_norm: fields.residual_vector_norm,
    };
  };

  const catalogBlocks = blocks.map(toCatalogBlock);
  const sessionContext = {};
  if (Array.isArray(wholeBlocks) && wholeBlocks.length > 0) {
    const wholeCatalog = wholeBlocks.map(toCatalogBlock);
    const startTimes = wholeCatalog.map((b) => b.start_time).filter(Number.isFinite);
    const endTimes = wholeCatalog.map((b) => b.end_time).filter(Number.isFinite);
    const startProgs = wholeCatalog.map((b) => b.start_progress).filter(Number.isFinite);
    const endProgs = wholeCatalog.map((b) => b.end_progress).filter(Number.isFinite);
    if (startTimes.length && endTimes.length) {
      sessionContext.time = { start: Math.min(...startTimes), end: Math.max(...endTimes) };
    }
    if (startProgs.length && endProgs.length) {
      sessionContext.progress = { start: Math.min(...startProgs), end: Math.max(...endProgs) };
    }
  }
  return { blocks: catalogBlocks, sessionContext };
}

function normalizeSource(value) {
  if (value === "Human" || value === "user") return "user";
  if (value === "AI" || value === "api") return "api";
  return value;
}

function serializeReferenceBlock(block, index, sessionContext) {
  const source = normalizeSource(block.source);
  const progress = Number.isFinite(block.progress)
    ? block.progress
    : Number.isFinite(block.end_progress) && Number.isFinite(block.start_progress)
      ? block.end_progress - block.start_progress
      : undefined;
  const semantic_change = Number.isFinite(block.semantic_change)
    ? block.semantic_change
    : block.residual_vector_norm;
  const time = Number.isFinite(block.duration_seconds)
    ? block.duration_seconds
    : Number.isFinite(block.time)
      ? block.time
      : Number.isFinite(block.end_time) && Number.isFinite(block.start_time)
        ? block.end_time - block.start_time
        : undefined;

  const out = { index, source, progress, semantic_change, time };

  if (Number.isFinite(block.session_relative_position)) {
    out.session_relative_position = block.session_relative_position;
  } else if (
    Number.isFinite(block.start_time) &&
    Number.isFinite(sessionContext?.time?.start) &&
    Number.isFinite(sessionContext?.time?.end) &&
    sessionContext.time.end > sessionContext.time.start
  ) {
    out.session_relative_position =
      (block.start_time - sessionContext.time.start) /
      (sessionContext.time.end - sessionContext.time.start);
  }

  return out;
}

// Builds the 4 App. B.1 inputs for the spec interpreter.
export function buildInterpreterInput(
  description,
  referenceBlocks,
  catalog = FEATURE_CATALOG,
  options = {},
) {
  const blocks = Array.isArray(referenceBlocks) ? referenceBlocks : [];
  const n = blocks.length;
  const sessionContext = options?.sessionContext ?? {};
  return {
    description,
    reference_episode: {
      length: n,
      blocks: blocks.map((block, index) => serializeReferenceBlock(block, index, sessionContext)),
    },
    feature_catalog: {
      block_definition: BLOCK_DEFINITION,
      features: catalog,
    },
    span_bounds: {
      min_blocks: n,
      max_blocks: n,
    },
    output_schema: PATTERN_SPEC_SCHEMA_GUIDE,
    constraint_forms: CONSTRAINT_FORMS_GUIDE,
  };
}

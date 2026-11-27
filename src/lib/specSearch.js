import { FEATURE_CATALOG } from "./featureCatalog.js";
import { evaluateSpec, validateSpec } from "./patternSpec.js";
import { weightsFromSpec } from "./ranking.js";

export const USE_SPEC_INTERPRETER = true;

// Check the multiplier itself, not whether unrelated clauses match the reference.
export function pendingRatioIds(spec, reference, sessionContext) {
  return spec.constraints.filter((clause) =>
    clause.type === "ratio" &&
    clause.provenance !== "analyst-confirmed" &&
    !evaluateSpec({ ...spec, constraints: [clause] }, reference, {
      ...sessionContext, catalog: FEATURE_CATALOG,
    }).pass,
  ).map(({ id }) => id);
}

export function describeRatio(clause, pending) {
  const { numerator, denominator } = clause.left;
  const value = (ref) => {
    const feature = ref.feature_id ?? clause.feature_id;
    const label = FEATURE_CATALOG.find(({ id }) => id === feature)?.label ?? feature;
    const block = ref.anchor_id ? `anchor ${ref.anchor_id}` : `block ${ref.offset + 1}`;
    return `${label} at ${block}`;
  };
  const left = value(numerator);
  const right = value(denominator);
  if (pending && clause.operator === "=") return `Exact ratio of ${left} to ${right} is not used until picked.`;
  if (pending) return `${left} ${clause.operator} ${right} (direction only).`;
  return `${left} divided by ${right} ${clause.operator} ${clause.right.value}×.`;
}

// Use only schema-defined clauses in the executable spec and in saved patterns.
export function executableSpec(draft, pendingIds) {
  const pending = draft.constraints.filter(({ id }) => pendingIds.includes(id));
  const textById = new Map(draft.constraints.filter((clause) => clause.type === "ratio")
    .map((clause) => [clause.id, describeRatio(clause, pendingIds.includes(clause.id))]));
  const deferred = new Set(pending.filter(({ operator }) => operator === "=").map(({ id }) => id));
  const seen = new Set();
  const explanations = draft.explanations.filter(({ target_id }) => !deferred.has(target_id))
    .map((entry) => {
      seen.add(entry.target_id);
      return textById.has(entry.target_id) ? { ...entry, text: textById.get(entry.target_id) } : entry;
    });
  for (const [target_id, text] of textById) {
    if (!seen.has(target_id) && !deferred.has(target_id)) explanations.push({ target_id, text });
  }
  const constraints = draft.constraints.filter(({ id }) => !deferred.has(id)).map((clause) =>
    pendingIds.includes(clause.id) ? {
      ...clause, type: "pairwise", left: clause.left.numerator, right: clause.left.denominator,
    } : clause,
  );
  return {
    ...draft, constraints, explanations,
    unresolved: [...draft.unresolved, ...pending.map((clause) => ({
      term: `Ratio ${clause.id}`,
      message: `${describeRatio(clause, true)} Pick a multiplier to apply a ratio filter.`,
    }))],
  };
}

export function confirmRatio(draft, id, value) {
  return {
    ...draft,
    constraints: draft.constraints.map((clause) => clause.id === id ? {
      ...clause, provenance: "analyst-confirmed",
      right: {
        value,
        alternatives: [...new Set([clause.right.value, ...(clause.right.alternatives ?? [])])]
          .filter((option) => option !== value),
      },
    } : clause),
  };
}

export function makeSpecSearchRecord(interpretation, count) {
  const { draft, pendingIds, userInput, llmRequest, llmResponse, systemPromptHash } = interpretation;
  const spec = executableSpec(draft, pendingIds);
  const validation = validateSpec(spec, { catalog: FEATURE_CATALOG, referenceLength: count });
  if (!validation.ok) throw new Error(`Invalid pattern spec: ${validation.errors.join("; ")}`);
  return { mode: "spec", spec, userInput, llmRequest, llmResponse, systemPromptHash };
}

// Block fields each catalog feature is computed from (see FEATURE_CATALOG provenance).
const FEATURE_FIELDS = {
  source: [["source"]],
  progress: [["start_progress", "startProgress"], ["end_progress", "endProgress"]],
  time: [["start_time", "startTime"], ["end_time", "endTime"]],
  semantic_change: [["residual_vector_norm"]],
};

function collectFeatureIds(node, out = new Set()) {
  if (Array.isArray(node)) node.forEach((item) => collectFeatureIds(item, out));
  else if (node && typeof node === "object") {
    for (const [key, value] of Object.entries(node)) {
      if (key === "feature_id" && typeof value === "string") out.add(value);
      else collectFeatureIds(value, out);
    }
  }
  return out;
}

// Event-block scheme the bundled datasets use (README: a block ends when the writer requests
// an AI suggestion or accepts an AI insertion). Segment files do not record it, so a dataset
// may declare it in static/dataset/<name>/meta.json; otherwise this default is assumed.
export const DEFAULT_SEGMENTATION = "human-ai-interaction";
export const NORMALIZATION_NOTE = "robust_iqr over the searched dataset (computed at search time)";

// meta.json (all keys optional):
// { "segmentation": "human-ai-interaction",
//   "features": { "semantic_change": { "version": "model-name" } } }
export function normalizeDatasetMeta(meta) {
  const declared = typeof meta?.segmentation === "string" && meta.segmentation.trim();
  const versions = {};
  for (const [id, entry] of Object.entries(meta?.features ?? {})) {
    if (entry?.version) versions[id] = String(entry.version);
  }
  return {
    segmentation: declared || DEFAULT_SEGMENTATION,
    segmentationAssumed: !declared,
    featureVersions: versions,
  };
}

// Recorded on every saved pattern (paper App. C.4); excluded ids make the saved result
// set reproducible on the same dataset.
export function buildReproducibility(meta, excludedSegmentIds) {
  const info = normalizeDatasetMeta(meta);
  return {
    segmentation: info.segmentation,
    segmentationAssumed: info.segmentationAssumed,
    featureVersions: info.featureVersions,
    normalization: NORMALIZATION_NOTE,
    overlapPolicy: "per-session windows overlapping by more than half are merged (lower distance kept)",
    excludedSegmentIds: [...excludedSegmentIds],
  };
}

const blockHas = (block, names) =>
  names.some((name) => (name === "source" ? block?.[name] != null : Number.isFinite(block?.[name])));

// Decide whether a saved spec can run on another dataset (paper App. C.5). `sampleBlocks` are
// blocks of the target dataset; `targetMeta` is its meta.json (or null). Nothing is dropped
// silently: `errors` block reuse, `warnings` must be confirmed by the user.
// Omit `sampleBlocks` for same-dataset reuse (only the spec itself is validated).
export function checkSpecCompatibility(saved, { sampleBlocks = null, targetMeta = null } = {}) {
  const errors = [];
  const warnings = [];
  const spec = saved?.searchSpec?.spec;
  const length = saved?.searchDetail?.data?.length;
  if (saved?.searchSpec?.mode !== "spec" || !spec) {
    return { ok: false, errors: ["This pattern was not saved with a typed specification, so it cannot be re-run."], warnings };
  }
  if (!length || !saved.searchDetail?.data) {
    return { ok: false, errors: ["The saved reference episode is missing."], warnings };
  }
  const validation = validateSpec(spec, { catalog: FEATURE_CATALOG, referenceLength: length });
  if (!validation.ok) errors.push(...validation.errors.map((e) => `Specification no longer valid: ${e}`));
  if (!sampleBlocks) return { ok: errors.length === 0, errors, warnings };

  const features = collectFeatureIds({ a: spec.attributes, c: spec.constraints, s: spec.span.anchors });
  if (!sampleBlocks.length) errors.push("The dataset has no blocks to search.");
  for (const id of features) {
    const alternatives = FEATURE_FIELDS[id];
    if (!alternatives) { errors.push(`Feature "${id}" is not defined for this dataset.`); continue; }
    for (const names of alternatives) {
      const missing = sampleBlocks.filter((block) => !blockHas(block, names)).length;
      if (sampleBlocks.length && missing === sampleBlocks.length) {
        errors.push(`This dataset has no "${names[0]}" values, which the pattern needs for ${id}.`);
      } else if (missing > 0) {
        warnings.push(`${missing} of ${sampleBlocks.length} sampled blocks lack "${names[0]}" (needed for ${id}).`);
      }
    }
    if (id === "semantic_change" && sampleBlocks.length &&
        sampleBlocks.every((block) => !(Number(block?.residual_vector_norm) > 0))) {
      errors.push("Semantic change is zero in every sampled block of this dataset (residual_vector_norm was not computed).");
    }
  }

  // Segmentation scheme and derived-feature versions.
  const target = normalizeDatasetMeta(targetMeta);
  const record = saved.reproducibility;
  if (!record) {
    warnings.push("This pattern was saved before segmentation and feature versions were recorded, so they cannot be compared.");
  } else {
    if (record.segmentation !== target.segmentation) {
      errors.push(`Segmentation differs: the pattern uses "${record.segmentation}", this dataset uses "${target.segmentation}".`);
    } else if (record.segmentationAssumed || target.segmentationAssumed) {
      warnings.push(`Segmentation "${target.segmentation}" is assumed (no meta.json declares it); confirm both datasets were cut the same way.`);
    }
    for (const id of features) {
      if (id !== "semantic_change") continue; // only derived features have versions
      const saves = record.featureVersions?.[id];
      const here = target.featureVersions[id];
      if (saves && here && saves !== here) errors.push(`Feature "${id}" was computed differently: pattern "${saves}" vs this dataset "${here}".`);
      else if (!saves || !here) warnings.push(`The version of feature "${id}" is not recorded for ${!saves ? "the pattern" : "this dataset"}, so it cannot be verified.`);
    }
  }
  return { ok: errors.length === 0, errors, warnings };
}

export function selectSearchMode(specEnabled, hasSpec, interpretedQuery) {
  if (specEnabled) return hasSpec ? "spec" : "manual";
  return interpretedQuery?.trim() ? "query" : "manual";
}

function bounds(blocks, axis) {
  let start = Infinity;
  let end = -Infinity;
  for (const block of blocks) {
    if (Number.isFinite(block[`start_${axis}`])) start = Math.min(start, block[`start_${axis}`]);
    if (Number.isFinite(block[`end_${axis}`])) end = Math.max(end, block[`end_${axis}`]);
  }
  return { start, end };
}

export function findSpecSegments(blocks, spec, sessionId) {
  const n = spec.span.min_blocks;
  const context = {
    catalog: FEATURE_CATALOG,
    time: bounds(blocks, "time"),
    progress: bounds(blocks, "progress"),
  };
  const matches = [];
  for (let start = 0; start + n <= blocks.length; start++) {
    const window = blocks.slice(start, start + n);
    if (window[0].residual_vector_norm === 0 || !evaluateSpec(spec, window, context).pass) continue;
    matches.push(window.map((block) => ({ ...block, id: sessionId, segmentId: `${sessionId}_${start}` })));
  }
  return matches;
}

// Spec search derives feature switches from attributes, not the manual controls.
export function specRankingChecks(spec) {
  const weights = weightsFromSpec(spec);
  return {
    source: [weights.s > 0],
    progress: [weights.p > 0],
    semantic: [weights.sem > 0],
    trend: [weights.tr > 0],
  };
}

export function attributeIdsSignature(attributes = []) {
  return JSON.stringify(attributes.map((attribute) => attribute.id));
}

export function prioritySignature(attributes = []) {
  return JSON.stringify(attributes.map((attribute) => [attribute.id, attribute.priority]));
}

export function shouldRerankSpec(prevDraft, nextDraft, rankState) {
  if (!rankState || !nextDraft) return false;
  if (attributeIdsSignature(nextDraft.attributes) !== rankState.attributeIdsSignature) return false;
  const nextPriorities = prioritySignature(nextDraft.attributes);
  const prevPriorities = prevDraft ? prioritySignature(prevDraft.attributes) : rankState.prioritiesSignature;
  return nextPriorities !== prevPriorities;
}

export function createSpecRerankRunner(rankFn) {
  let seq = 0;
  return {
    nextSeq() {
      return ++seq;
    },
    currentSeq() {
      return seq;
    },
    isCurrent(token) {
      return token === seq;
    },
    async run(draft, state, onCommit, token = ++seq) {
      const nextWeights = weightsFromSpec(draft);
      const finalScore = await rankFn(state.patternVectors, state.currentVector, nextWeights);
      if (token !== seq) return { committed: false, seq: token };
      await onCommit(finalScore, token);
      return { committed: token === seq, seq: token };
    },
  };
}

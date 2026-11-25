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

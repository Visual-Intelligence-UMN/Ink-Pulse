<script>
  import { createEventDispatcher } from "svelte";
  import { confirmRatio } from "../lib/specSearch.js";
  import { attributeToRankingKey, weightsFromSpec } from "../lib/ranking.js";

  /** @type {any} */
  export let interpretation = null;
  export let disabled = false;
  export let isEdited = false;
  const dispatch = createEventDispatcher();
  $: draft = interpretation?.draft;
  $: pendingIds = interpretation?.pendingIds ?? [];
  $: explanations = new Map((draft?.explanations ?? []).map(({ target_id, text }) => [target_id, text]));
  $: anchorsById = new Map((draft?.span?.anchors ?? []).map((anchor) => [anchor.id, anchor]));

  let customRatioId = null;
  let customRatioValue = undefined;
  let lastDraftSource = null;

  $: {
    const sourceKey = interpretation ? `${interpretation.llmResponse ?? ""}::${interpretation.userInput ?? ""}` : null;
    if (sourceKey !== lastDraftSource) {
      lastDraftSource = sourceKey;
      customRatioId = null;
    }
  }
  $: if (!draft) customRatioId = null;

  function update(nextDraft, nextPendingIds = interpretation.pendingIds) {
    dispatch("specState", { ...interpretation, draft: nextDraft, pendingIds: nextPendingIds });
  }

  function removeConstraints(ids) {
    if (disabled) return;
    const idSet = new Set(Array.isArray(ids) ? ids : [ids]);
    if (customRatioId && idSet.has(customRatioId)) customRatioId = null;
    update({
      ...draft,
      constraints: draft.constraints.filter((clause) => !idSet.has(clause.id)),
      explanations: draft.explanations.filter(({ target_id }) => !idSet.has(target_id)),
    }, pendingIds.filter((pendingId) => !idSet.has(pendingId)));
  }

  function setGroupPriority(rankingKey, nextPriority) {
    if (disabled) return;
    const changed = (draft?.attributes ?? []).some(
      (entry) => attributeToRankingKey(entry) === rankingKey && entry.priority !== nextPriority,
    );
    if (!changed) return;
    update({
      ...draft,
      attributes: draft.attributes.map((entry) =>
        attributeToRankingKey(entry) === rankingKey ? { ...entry, priority: nextPriority } : entry,
      ),
    });
  }

  function changeMultiplier(id, value) {
    if (disabled || !Number.isFinite(value)) return;
    update(confirmRatio(draft, id, value), pendingIds.filter((pendingId) => pendingId !== id));
  }

  function handleRatioSelect(id, event) {
    if (disabled) return;
    const raw = event.currentTarget.value;
    if (raw === "__custom__") {
      customRatioValue = undefined;
      customRatioId = id;
      return;
    }
    customRatioId = null;
    changeMultiplier(id, Number(raw));
  }

  function applyCustomRatio(id) {
    if (disabled || !Number.isFinite(customRatioValue) || customRatioValue <= 0) return;
    changeMultiplier(id, customRatioValue);
    customRatioId = null;
  }

  const OP_SYMBOL = { "=": "=", "<": "<", "<=": "≤", ">": ">", ">=": "≥" };
  const FEATURE_LABELS = {
    source: "Author",
    progress: "Writing progress",
    semantic_change: "Semantic change",
    time: "Duration",
  };
  const RANK_KEY_META = {
    s: { label: "Source", feature: "source" },
    p: { label: "Writing progress", feature: "progress" },
    sem: { label: "Semantic change", feature: "semantic_change" },
    tr: { label: "Semantic trend", feature: "semantic_change" },
  };

  function sourceLabel(value) {
    if (value === "user") return "Human";
    if (value === "api") return "AI";
    return String(value ?? "");
  }

  function formatOp(op) {
    return OP_SYMBOL[op] ?? op;
  }

  function formatValue(featureId, value) {
    if (featureId === "source") return sourceLabel(value);
    if (!Number.isFinite(value)) return String(value ?? "");
    if (featureId === "progress") {
      return value >= 0 && value <= 1 ? `${+(value * 100).toFixed(1)}%` : `${+value.toFixed(2)}`;
    }
    if (featureId === "time") return `${+value.toFixed(1)}s`;
    return `${+value.toFixed(2)}`;
  }

  function resolveOffset(ref, anchorMap) {
    if (Number.isInteger(ref?.offset)) return ref.offset;
    if (ref?.anchor_id && anchorMap.has(ref.anchor_id)) {
      const anchor = anchorMap.get(ref.anchor_id);
      if (Number.isInteger(anchor?.offset)) return anchor.offset;
    }
    return null;
  }

  function formatBlockRef(ref, anchorMap) {
    if (Number.isInteger(ref?.offset)) return `Block ${ref.offset + 1}`;
    if (ref?.anchor_id) {
      const anchor = anchorMap.get(ref.anchor_id);
      if (Number.isInteger(anchor?.offset)) {
        const tag =
          anchor.predicate?.feature_id === "source" && anchor.predicate?.operator === "="
            ? ` (${sourceLabel(anchor.predicate.value)})`
            : "";
        return `Block ${anchor.offset + 1}${tag}`;
      }
      return `anchor ${ref.anchor_id}`;
    }
    return "block";
  }

  function formatFeatureRef(ref, defaultFeature, anchorMap) {
    const blockText = formatBlockRef(ref, anchorMap);
    const featureId = ref?.feature_id ?? defaultFeature;
    if (featureId !== defaultFeature) {
      return `${FEATURE_LABELS[featureId] ?? featureId} at ${blockText}`;
    }
    return blockText;
  }

  function formatPredicate(pred) {
    if (!pred) return "";
    if (pred.feature_id === "source" && pred.operator === "=") {
      return `${sourceLabel(pred.value)} block`;
    }
    return `${FEATURE_LABELS[pred.feature_id] ?? pred.feature_id} ${formatOp(pred.operator)} ${formatValue(pred.feature_id, pred.value)}`;
  }

  function formatConstraint(clause, anchorMap, expMap) {
    const feat = FEATURE_LABELS[clause.feature_id] ?? clause.feature_id;
    const op = formatOp(clause.operator);
    switch (clause.type) {
      case "source": {
        if (clause.left?.sequence) {
          const seq = Array.isArray(clause.right?.sources)
            ? clause.right.sources.map(sourceLabel).join(" → ")
            : "matches reference";
          return `Author order: ${seq}`;
        }
        return `${formatBlockRef(clause.left, anchorMap)} is ${sourceLabel(clause.right?.value)}`;
      }
      case "scalar":
        return `${feat} at ${formatBlockRef(clause.left, anchorMap)} ${op} ${formatValue(clause.feature_id, clause.right?.value)}`;
      case "pairwise": {
        const leftText = formatBlockRef(clause.left, anchorMap);
        const rightText = formatFeatureRef(clause.right, clause.feature_id, anchorMap);
        return `${feat}: ${leftText} ${op} ${rightText}`;
      }
      case "trend": {
        const who = clause.left?.source ? `${sourceLabel(clause.left.source)} ` : "";
        const dir = clause.operator === ">" ? "increasing" : "decreasing";
        return `${who}${feat.toLowerCase()} trend: ${dir}`;
      }
      case "count":
        return `Count of (${formatPredicate(clause.left?.predicate)}) ${op} ${clause.right?.value}`;
      case "aggregate": {
        const agg = clause.left?.aggregate ?? "value";
        const who = clause.left?.source ? `${sourceLabel(clause.left.source)} ` : "";
        let rightText;
        if (clause.right && "aggregate" in clause.right) {
          const rFeatId = clause.right.feature_id ?? clause.feature_id;
          const rFeat = FEATURE_LABELS[rFeatId] ?? rFeatId;
          const rWho = clause.right.source ? `${sourceLabel(clause.right.source)} ` : "";
          rightText = `${clause.right.aggregate} ${rWho}${rFeat.toLowerCase()}`;
        } else {
          rightText = formatValue(clause.feature_id, clause.right?.value);
        }
        return `${agg} ${who}${feat.toLowerCase()} ${op} ${rightText}`;
      }
      case "session-position": {
        const axisLabel = clause.feature_id === "time" ? "elapsed time" : "writing progress";
        const pct = Number.isFinite(clause.right?.value)
          ? `${+(clause.right.value * 100).toFixed(1)}% of session`
          : String(clause.right?.value);
        return `${formatBlockRef(clause.left, anchorMap)} (${axisLabel}) ${op} ${pct}`;
      }
      default:
        return expMap.get(clause.id) ?? `${feat} (${clause.type})`;
    }
  }

  $: filterView = (() => {
    if (!draft) return { rows: [], fixedAnchors: [] };
    const singleSourceClauses = [];
    const otherClauses = [];
    const sequenceSources = [];
    const coveredSourceOffsets = new Set();

    for (const clause of draft.constraints ?? []) {
      if (clause.type === "source" && clause.left?.sequence) {
        if (Array.isArray(clause.right?.sources)) sequenceSources.push(clause.right.sources);
        otherClauses.push(clause);
      } else if (clause.type === "source" && clause.operator === "=" && clause.right?.value) {
        const off = resolveOffset(clause.left, anchorsById);
        if (Number.isInteger(off)) coveredSourceOffsets.add(`${off}:${clause.right.value}`);
        singleSourceClauses.push({ clause, off });
      } else {
        otherClauses.push(clause);
      }
    }

    const rows = [];
    if (singleSourceClauses.length > 0) {
      singleSourceClauses.sort((a, b) => (a.off ?? 999) - (b.off ?? 999));
      const parts = singleSourceClauses.map(({ clause, off }) =>
        `${Number.isInteger(off) ? `Block ${off + 1}` : formatBlockRef(clause.left, anchorsById)}: ${sourceLabel(clause.right.value)}`,
      );
      rows.push({
        key: `group:source:${singleSourceClauses.map((x) => x.clause.id).join(",")}`,
        kind: "source-group",
        feature: "source",
        badge: "Source",
        ids: singleSourceClauses.map((x) => x.clause.id),
        text: parts.join(", "),
      });
    }

    for (const clause of otherClauses) {
      rows.push({
        key: `clause:${clause.id}`,
        kind: clause.type === "ratio" ? "ratio" : "constraint",
        feature: clause.feature_id,
        badge: featureStyleMap[clause.feature_id]?.label ?? clause.type,
        clause,
        ids: [clause.id],
        text: clause.type === "ratio" ? "" : formatConstraint(clause, anchorsById, explanations),
      });
    }

    // Surface fixed-position anchor predicates that actively filter candidates if not already covered above.
    const fixedAnchors = [];
    for (const anchor of draft.span?.anchors ?? []) {
      if (!Number.isInteger(anchor?.offset) || !anchor?.predicate) continue;
      const isSourceEq = anchor.predicate.feature_id === "source" && anchor.predicate.operator === "=";
      const coveredBySeq = isSourceEq && sequenceSources.some((seq) => seq[anchor.offset] === anchor.predicate.value);
      if (isSourceEq && (coveredBySeq || coveredSourceOffsets.has(`${anchor.offset}:${anchor.predicate.value}`))) {
        continue;
      }
      fixedAnchors.push({
        id: anchor.id,
        feature: anchor.predicate.feature_id,
        badge: featureStyleMap[anchor.predicate.feature_id]?.label ?? "Fixed",
        text: isSourceEq
          ? `Block ${anchor.offset + 1} is ${sourceLabel(anchor.predicate.value)}`
          : `Block ${anchor.offset + 1}: ${formatPredicate(anchor.predicate)}`,
      });
    }

    return { rows, fixedAnchors };
  })();

  $: rankingGroups = (() => {
    if (!draft) return [];
    const weights = weightsFromSpec(draft);
    const grouped = new Map();
    for (const attr of draft.attributes ?? []) {
      const key = attributeToRankingKey(attr);
      if (!key) continue;
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key).push(attr);
    }
    const order = ["s", "p", "sem", "tr"];
    const items = [];
    for (const key of order) {
      const attrs = grouped.get(key);
      if (!attrs || attrs.length === 0) continue;
      const priorities = new Set(attrs.map((a) => a.priority));
      const priority = priorities.has("primary") ? "primary" : "secondary";
      const meta = RANK_KEY_META[key];
      items.push({
        key,
        label: meta.label,
        feature: meta.feature,
        priority,
        mixed: priorities.size > 1,
        weightPct: Math.round((weights[key] ?? 0) * 100),
        count: attrs.length,
      });
    }
    // Primary rows first for faster scanning.
    items.sort((a, b) => (a.priority === b.priority ? 0 : a.priority === "primary" ? -1 : 1));
    return items;
  })();

  export let exp_result = {
    explanations: [],
    filters: []
  };

  let editingRatioIndex = null;
  let ratioInputValue = "";
  let ratioSelections = {};

  const featureStyleMap = {
    source: {
      label: "Source",
      bg: "#e3f2fd",
      color: "#1565c0",
    },
    progress: {
      label: "Progress",
      bg: "#fff3e0",
      color: "#ef6c00",
    },
    semantic_change: {
      label: "Semantic",
      bg: "#e8f5e9",
      color: "#2e7d32",
    },
    time: {
      label: "Time",
      bg: "#f3e5f5",
      color: "#6a1b9a",
    },
  };

  const ratioRegex = /\[([^\]]+)\]|\(([^)]+)\)/g;

  function parseRatioText(text) {
    const parts = [];
    let lastIndex = 0;
    let currentRatio = null;
    let nextId = 0;

    for (const match of text.matchAll(ratioRegex)) {
      if (match.index > lastIndex) {
        parts.push({
          type: "text",
          value: text.slice(lastIndex, match.index),
          id: nextId++,
        });
      }

      if (match[1]) {
        currentRatio = {
          type: "ratio",
          selected: match[1],
          options: [match[1]],
          id: nextId++,
        };
        parts.push(currentRatio);
      } else if (match[2] && currentRatio) {
        const opts = match[2].split(",").map((o) => o.trim());
        currentRatio.options.push(...opts);
      }

      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push({
        type: "text",
        value: text.slice(lastIndex),
        id: nextId++,
      });
    }

    return parts;
  }

  function getUniqueDropdownId(expIndex, partId) {
    return `${expIndex}-${partId}`;
  }

  function startEditingRatio(expIndex, partId, currentValue) {
    const key = getUniqueDropdownId(expIndex, partId);
    editingRatioIndex = key;
    const match = currentValue.match(/^(\d+(?:\.\d+)?)x?$/);
    ratioInputValue = match ? match[1] : currentValue.replace("x", "");
  }

  function handleRatioInput(expIndex, partId, event) {
    if (event.key === "Enter") {
      confirmRatioInput(expIndex, partId);
    } else if (event.key === "Escape") {
      cancelRatioInput();
    }
  }

  function confirmRatioInput(expIndex, partId) {
    const inputNum = parseFloat(ratioInputValue);
    if (isNaN(inputNum) || inputNum <= 0) {
      alert("Please enter a valid positive number");
      return;
    }

    const newValue = `${ratioInputValue}x`;
    const key = getUniqueDropdownId(expIndex, partId);
    ratioSelections = {
      ...ratioSelections,
      [key]: newValue
    };

    editingRatioIndex = null;
    ratioInputValue = "";
  }

  function cancelRatioInput() {
    editingRatioIndex = null;
    ratioInputValue = "";
  }

  function removeExplanation(index) {
    const parts = parseRatioText(exp_result.explanations[index].text);
    parts.forEach((part) => {
      if (part.type === "ratio") {
        const key = getUniqueDropdownId(index, part.id);
        delete ratioSelections[key];
      }
    });

    exp_result.explanations.splice(index, 1);
    if (exp_result.filters && exp_result.filters.length > index) {
      exp_result.filters.splice(index, 1);
    }

    exp_result = { ...exp_result };
    ratioSelections = { ...ratioSelections };
  }

  $: if (exp_result?.explanations) {
    const nextSelections = {};
    exp_result.explanations.forEach((exp, expIndex) => {
      const parts = parseRatioText(exp.text);
      parts.forEach((part) => {
        if (part.type === "ratio") {
          const key = getUniqueDropdownId(expIndex, part.id);
          nextSelections[key] = ratioSelections[key] || part.selected;
        }
      });
    });
    ratioSelections = nextSelections;
  }
</script>

{#if draft}
  <div class="spec-panel" aria-label="Pattern specification">
    <div class="spec-header">
      <span class="spec-title">
        Pattern Rules ({draft.span?.min_blocks ?? "?"} blocks)
      </span>
      {#if isEdited}
        <span class="edited-pill">Changed (click Search)</span>
      {/if}
    </div>

    {#if interpretation?.originalUserInput}
      <div class="prompt-context">
        <div><strong>Original:</strong> {interpretation.originalUserInput}</div>
        {#if interpretation?.userInput}
          <div><strong>Refined:</strong> {interpretation.userInput}</div>
        {/if}
      </div>
    {/if}

    <div class="spec-section">
      <div class="section-label">Filters</div>
      {#if filterView.rows.length === 0 && filterView.fixedAnchors.length === 0}
        <div class="empty-note">No filters applied.</div>
      {:else}
        {#each filterView.rows as row (row.key)}
          <div class="spec-row" data-constraint-type={row.clause?.type ?? "source"}>
            <span
              class="feature-badge"
              style="background: {featureStyleMap[row.feature]?.bg ?? '#eef2f5'}; color: {featureStyleMap[row.feature]?.color ?? '#334155'};"
            >
              {row.badge}
            </span>
            <div class="spec-body">
              {#if row.kind === "ratio"}
                {@const clause = row.clause}
                {@const pending = pendingIds.includes(clause.id)}
                {@const options = [...new Set([clause.right?.value, ...(clause.right?.alternatives ?? [])].filter(Number.isFinite))]}
                <span class="ratio-line">
                  {formatBlockRef(clause.left?.numerator, anchorsById)}
                  {formatOp(clause.operator)}
                  {#if customRatioId === clause.id}
                    <form class="inline-ratio-form" on:submit|preventDefault={() => applyCustomRatio(clause.id)}>
                      <input
                        class="ratio-input"
                        aria-label={`Custom multiplier for ${clause.id}`}
                        type="number"
                        min="0"
                        step="any"
                        required
                        disabled={disabled}
                        bind:value={customRatioValue}
                      />
                      <span class="ratio-unit">×</span>
                      <button type="submit" class="teal-mini-btn" disabled={disabled || !(Number.isFinite(customRatioValue) && customRatioValue > 0)}>Apply</button>
                      <button type="button" class="ghost-mini-btn" disabled={disabled} on:click={() => (customRatioId = null)}>Cancel</button>
                    </form>
                  {:else}
                    <select
                      class="teal-select"
                      class:pending-select={pending}
                      aria-label={`Multiplier for ${clause.id}`}
                      disabled={disabled}
                      value={pending ? "" : String(clause.right?.value ?? "")}
                      on:change={(event) => handleRatioSelect(clause.id, event)}
                    >
                      {#if pending}
                        <option value="" disabled>Pick ×</option>
                      {/if}
                      {#each options as option}
                        <option value={String(option)}>{option}×</option>
                      {/each}
                      <option value="__custom__">Custom…</option>
                    </select>
                  {/if}
                  {formatFeatureRef(clause.left?.denominator, clause.feature_id, anchorsById)}
                </span>
                {#if pending}
                  <span class="pending-pill">
                    {clause.operator === "=" ? "Pick a multiplier to apply" : "Direction only (pick a multiplier)"}
                  </span>
                {/if}
              {:else}
                {row.text}
              {/if}
            </div>
            <button
              type="button"
              class="remove-chip"
              disabled={disabled}
              aria-label={`Remove constraint ${row.ids.join(", ")}`}
              title="Remove filter"
              on:click={() => removeConstraints(row.ids)}
            >
              ×
            </button>
          </div>
        {/each}
        {#each filterView.fixedAnchors as anchor (anchor.id)}
          <div class="spec-row fixed-row">
            <span
              class="feature-badge"
              style="background: {featureStyleMap[anchor.feature]?.bg ?? '#eef2f5'}; color: {featureStyleMap[anchor.feature]?.color ?? '#334155'};"
            >
              {anchor.badge}
            </span>
            <div class="spec-body">{anchor.text}</div>
            <span class="fixed-tag" title="Fixed block check from anchor">Fixed</span>
          </div>
        {/each}
      {/if}
    </div>

    <div class="spec-section">
      <div class="section-label">Ranking Weights</div>
      {#if rankingGroups.length === 0}
        <div class="empty-note">Equal weights (25% each).</div>
      {:else}
        {#each rankingGroups as group (group.key)}
          <div class="spec-row rank-row">
            <span
              class="feature-badge"
              style="background: {featureStyleMap[group.feature]?.bg ?? '#eef2f5'}; color: {featureStyleMap[group.feature]?.color ?? '#334155'};"
            >
              {group.label}
            </span>
            <div class="rank-meta">
              <span class="weight-pct">{group.weightPct}%</span>
              {#if group.mixed}
                <span class="mixed-tag" title="Underlying block attributes had mixed priorities; click to unify">Mixed</span>
              {/if}
            </div>
            <div class="priority-segment" role="group" aria-label={`Priority for ${group.label}`}>
              <button
                type="button"
                class="seg-btn"
                class:active={group.priority === "primary"}
                disabled={disabled}
                aria-pressed={group.priority === "primary"}
                title="Set Primary ranking priority (2× weight)"
                on:click={() => setGroupPriority(group.key, "primary")}
              >
                Primary
              </button>
              <button
                type="button"
                class="seg-btn"
                class:active={group.priority === "secondary"}
                disabled={disabled}
                aria-pressed={group.priority === "secondary"}
                title="Set Secondary ranking priority (1× weight)"
                on:click={() => setGroupPriority(group.key, "secondary")}
              >
                Secondary
              </button>
            </div>
          </div>
        {/each}
      {/if}
    </div>

    {#if draft.unresolved?.length}
      <div class="unresolved-box">
        <div class="unresolved-title">Unresolved</div>
        {#each draft.unresolved as item}
          <div class="unresolved-item"><strong>{item.term}:</strong> {item.message}</div>
        {/each}
      </div>
    {/if}

    <details class="spec-details">
      <summary>Details</summary>
      <div class="details-body">
        {#if draft.explanations?.length}
          <div class="details-heading">Model explanations</div>
          {#each draft.explanations as entry}
            <div class="details-item"><code>{entry.target_id}</code>: {entry.text}</div>
          {/each}
        {/if}
        {#if draft.span?.anchors?.length}
          <div class="details-heading">Anchors (fixed window)</div>
          {#each draft.span.anchors as anchor (anchor.id)}
            <div class="details-item">
              <code>{anchor.id}</code> checks at {Number.isInteger(anchor.offset) ? `Block ${anchor.offset + 1}` : "unbound block"}; selector
              <code>{anchor.selector}</code>{anchor.after ? ` (after ${anchor.after})` : ""} is not used in candidate search yet.
            </div>
          {/each}
        {/if}
        {#if draft.span?.gaps?.length}
          <div class="details-heading">Gaps (not applied in fixed window)</div>
          {#each draft.span.gaps as gap}
            <div class="details-item">
              <code>{gap.left}</code> → <code>{gap.right}</code> ({gap.min_blocks}–{gap.max_blocks} blocks) is not used in search yet.
            </div>
          {/each}
        {/if}
        {#if draft.assumptions?.length}
          <div class="details-heading">Assumptions</div>
          {#each draft.assumptions as note}
            <div class="details-item">{note}</div>
          {/each}
        {/if}
      </div>
    </details>
  </div>
{:else if exp_result?.explanations?.length}
  <div class="explanation-container">
    {#each exp_result.explanations as exp, expIndex}
      <span class="explanation-text">
        {#if featureStyleMap[exp.feature]}
          <span
            class="feature-badge"
            style="
              background: {featureStyleMap[exp.feature].bg};
              color: {featureStyleMap[exp.feature].color};
            "
          >
            {featureStyleMap[exp.feature].label}
          </span>
        {/if}

        <span class="explanation-body">
          {#each parseRatioText(exp.text) as part (part.id)}
            {#if part.type === "text"}
              {part.value}
            {:else if part.type === "ratio"}
              <span class="ratio-wrapper">
                {#if editingRatioIndex === getUniqueDropdownId(expIndex, part.id)}
                  <input
                    type="text"
                    class="ratio-input"
                    bind:value={ratioInputValue}
                    on:keydown={(e) => handleRatioInput(expIndex, part.id, e)}
                    on:blur={() => confirmRatioInput(expIndex, part.id)}
                  />
                  <span class="ratio-input-hint">x</span>
                {:else}
                  <button
                    type="button"
                    class="ratio-selected"
                    aria-haspopup="true"
                    on:click={() =>
                      startEditingRatio(
                        expIndex,
                        part.id,
                        ratioSelections[getUniqueDropdownId(expIndex, part.id)] || part.selected
                      )}
                  >
                    {ratioSelections[getUniqueDropdownId(expIndex, part.id)] || part.selected} ✎
                  </button>
                {/if}
              </span>
            {/if}
          {/each}

          <span
            class="close-button"
            on:click={() => removeExplanation(expIndex)}
          >
            ×
          </span>
        </span>
      </span>
    {/each}
  </div>
{/if}

<style>
  .spec-panel {
    width: 100%;
    max-width: 430px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 13px;
    color: #1f2937;
    line-height: 1.45;
  }

  .spec-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 2px 2px 0;
  }

  .spec-title {
    font-size: 12px;
    font-weight: 600;
    color: #137a7f;
    letter-spacing: 0.01em;
  }

  .edited-pill {
    font-size: 11px;
    font-weight: 600;
    color: #92400e;
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 999px;
    padding: 1px 8px;
    white-space: nowrap;
  }

  .prompt-context {
    background: #f3f9f9;
    border: 1px solid #cce3e4;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
    color: #334155;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .spec-section {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .section-label {
    font-size: 12px;
    font-weight: 600;
    color: #334155;
  }

  .empty-note {
    font-size: 12px;
    color: #64748b;
    padding: 2px 0;
  }

  .spec-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 6px;
    border-radius: 6px;
    background: #f8fafc;
  }

  .spec-row:hover {
    background: #f1f5f9;
  }

  .fixed-row {
    background: #f8fafc;
  }

  .spec-body {
    flex: 1;
    min-width: 0;
    word-wrap: break-word;
  }

  .ratio-line {
    display: inline-flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
  }

  .teal-select {
    font-size: 12px;
    font-weight: 600;
    color: #137a7f;
    background: #e6f4f4;
    border: 1px solid #137a7f;
    border-radius: 999px;
    padding: 1px 8px;
    cursor: pointer;
    font-family: inherit;
    outline: none;
  }

  .teal-select:hover {
    background: #d3eded;
  }

  .pending-select {
    color: #92400e;
    background: #fef3c7;
    border-color: #d97706;
  }

  .inline-ratio-form {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .ratio-unit {
    font-size: 12px;
    color: #475569;
    font-weight: 600;
  }

  .teal-mini-btn {
    font-size: 11px;
    font-weight: 600;
    background: #137a7f;
    color: #fff;
    border: 1px solid #137a7f;
    border-radius: 999px;
    padding: 2px 8px;
    cursor: pointer;
  }

  .teal-mini-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .ghost-mini-btn {
    font-size: 11px;
    font-weight: 600;
    background: transparent;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 999px;
    padding: 2px 8px;
    cursor: pointer;
  }

  .pending-pill {
    display: inline-block;
    margin-top: 3px;
    font-size: 11px;
    font-weight: 600;
    color: #92400e;
    background: #fef3c7;
    border-radius: 4px;
    padding: 1px 6px;
  }

  .remove-chip {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 15px;
    line-height: 1;
    padding: 2px 6px;
    border-radius: 4px;
    cursor: pointer;
  }

  .remove-chip:hover {
    background: #fee2e2;
    color: #b91c1c;
  }

  .fixed-tag {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    background: #e2e8f0;
    border-radius: 999px;
    padding: 1px 7px;
    white-space: nowrap;
  }

  .rank-row {
    justify-content: space-between;
  }

  .rank-meta {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .weight-pct {
    font-size: 12px;
    font-weight: 600;
    color: #334155;
  }

  .mixed-tag {
    font-size: 10px;
    font-weight: 600;
    color: #92400e;
    background: #fef3c7;
    border-radius: 999px;
    padding: 1px 6px;
  }

  .priority-segment {
    display: inline-flex;
    border: 1px solid #137a7f;
    border-radius: 999px;
    overflow: hidden;
    background: #ffffff;
  }

  .seg-btn {
    border: none;
    background: transparent;
    color: #137a7f;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    cursor: pointer;
    font-family: inherit;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  .seg-btn.active {
    background: #137a7f;
    color: #ffffff;
  }

  .seg-btn:not(.active):hover:not(:disabled) {
    background: #e6f4f4;
  }

  .seg-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .unresolved-box {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 8px;
    padding: 7px 9px;
    font-size: 12px;
    color: #78350f;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .unresolved-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #92400e;
  }

  .spec-details {
    font-size: 12px;
    color: #475569;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 8px;
  }

  .spec-details summary {
    cursor: pointer;
    font-weight: 600;
    color: #475569;
    user-select: none;
  }

  .details-body {
    margin-top: 6px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    border-top: 1px solid #e2e8f0;
    padding-top: 6px;
  }

  .details-heading {
    font-size: 11px;
    font-weight: 700;
    color: #334155;
    margin-top: 4px;
  }

  .details-item {
    font-size: 11.5px;
    color: #475569;
    word-wrap: break-word;
  }

  .details-item code {
    background: #e2e8f0;
    border-radius: 3px;
    padding: 0 4px;
    font-size: 11px;
  }

  .explanation-container {
    width: 100%;
    word-wrap: break-word;
    line-height: 1.5;
  }

  .explanation-text {
    display: flex;
    align-items: baseline;
    gap: 6px;
    width: 420px;
    margin-bottom: 6px;
    background-color: white;
    border-radius: 8px;
    padding: 4px;
  }

  .explanation-body {
    flex: 1;
    line-height: 1.6;
  }

  .explanation-text:has(.close-button:hover) {
    background-color: #f0f0f0;
  }

  .close-button {
    cursor: pointer;
    display: inline;
    font-size: 0.8em;
    margin-left: 2px;
  }

  .close-button:hover {
    opacity: 0.9;
  }

  .feature-badge {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    line-height: 1.4;
    white-space: nowrap;
  }

  .ratio-wrapper {
    position: relative;
    display: inline-block;
    margin: 0 4px;
  }

  .ratio-selected {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    line-height: 1.4;
    white-space: nowrap;
    background: #e0e0e0;
    color: #333;
    border: none;
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .ratio-selected:hover {
    background: #d0d0d0;
  }

  .ratio-input {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    line-height: 1.4;
    width: 50px;
    background: #fff;
    color: #333;
    border: 2px solid #137a7f;
    outline: none;
    text-align: center;
    font-family: inherit;
  }

  .ratio-input-hint {
    font-size: 12px;
    color: #666;
    margin-left: 2px;
  }
</style>

<script>
  import { createEventDispatcher } from "svelte";
  import { confirmRatio, describeRatio } from "../lib/specSearch.js";

  /** @type {any} */
  export let interpretation = null;
  export let disabled = false;
  const dispatch = createEventDispatcher();
  $: draft = interpretation?.draft;
  $: pendingIds = interpretation?.pendingIds ?? [];
  $: explanations = new Map(draft?.explanations.map(({ target_id, text }) => [target_id, text]));

  function update(draft, pendingIds = interpretation.pendingIds) {
    dispatch("specState", { ...interpretation, draft, pendingIds });
  }

  function removeConstraint(id) {
    update({
      ...draft,
      constraints: draft.constraints.filter((clause) => clause.id !== id),
      explanations: draft.explanations.filter(({ target_id }) => target_id !== id),
    }, pendingIds.filter((pendingId) => pendingId !== id));
  }

  function flipPriority(attribute) {
    if (disabled) return;
    update({
      ...draft,
      attributes: draft.attributes.map((entry) => entry.id === attribute.id ? {
        ...entry, priority: entry.priority === "primary" ? "secondary" : "primary",
      } : entry),
    });
  }

  function changeMultiplier(id, value) {
    if (!Number.isFinite(value)) return;
    update(confirmRatio(draft, id, value), pendingIds.filter((pendingId) => pendingId !== id));
  }

  let customRatioId = null;
  let customRatioValue = undefined;
  $: if (!draft) customRatioId = null;

  function applyCustomRatio(id) {
    if (!Number.isFinite(customRatioValue) || customRatioValue <= 0) return;
    changeMultiplier(id, customRatioValue);
    customRatioId = null;
  }
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
  <div class="explanation-container" aria-label="Pattern specification">
    {#each draft.constraints as clause (clause.id)}
      <div class="explanation-text" data-constraint-type={clause.type}>
        <span class="feature-badge">{clause.type}</span>
        <div class="explanation-body">
          {#if clause.type === "ratio"}
            {@const pending = pendingIds.includes(clause.id)}
            {@const options = [...new Set([clause.right.value, ...(clause.right.alternatives ?? [])])]}
            {describeRatio(clause, pending)}
            <select aria-label={`Multiplier for ${clause.id}`}
              value={pending ? "" : String(clause.right.value)}
              on:change={(event) => changeMultiplier(clause.id, Number(event.currentTarget.value))}>
              {#if pending}<option value="" disabled>Pick a multiplier</option>{/if}
              {#each options as option}
                <option value={String(option)}>{option}×</option>
              {/each}
            </select>
            {#if customRatioId === clause.id}
              <form on:submit|preventDefault={() => applyCustomRatio(clause.id)}>
                <input class="ratio-input" aria-label={`Custom multiplier for ${clause.id}`}
                  type="number" min="0" step="any" required bind:value={customRatioValue} />
                <button type="submit" disabled={!(customRatioValue > 0)}>Apply</button>
                <button type="button" on:click={() => (customRatioId = null)}>Cancel</button>
              </form>
            {:else}
              <button type="button" on:click={() => {
                customRatioValue = undefined;
                customRatioId = clause.id;
              }}>Custom multiplier</button>
            {/if}
          {:else}
            {explanations.get(clause.id) ?? `${featureStyleMap[clause.feature_id]?.label ?? clause.feature_id} (${clause.type} constraint)`}
          {/if}
        </div>
        <button type="button" class="close-button" aria-label={`Remove constraint ${clause.id}`}
          on:click={() => removeConstraint(clause.id)}>×</button>
      </div>
    {/each}
    {#each draft.attributes as attribute (attribute.id)}
      <div class="explanation-text">
        <span class="feature-badge">{featureStyleMap[attribute.feature_id]?.label ?? attribute.feature_id}</span>
        <span class="explanation-body">{explanations.get(attribute.id) ?? "Ranking attribute"}</span>
        <button type="button" aria-label={`Priority for ${attribute.id}: ${attribute.priority}`}
          title="Toggle primary or secondary ranking priority" disabled={disabled}
          on:click={() => flipPriority(attribute)}>
          {attribute.priority === "primary" ? "Primary" : "Secondary"}
        </button>
      </div>
    {/each}
    {#each draft.unresolved as item}
      <div class="explanation-text"><span class="explanation-body"><strong>{item.term}:</strong> {item.message}</span></div>
    {/each}
    {#each draft.span.anchors as anchor (anchor.id)}
      <div class="explanation-text"><span class="explanation-body">
        Anchor {anchor.id} checks its predicate at block {anchor.offset + 1}; selector
        {anchor.selector}{anchor.after ? ` (${anchor.after})` : ""} is not used in search yet.
      </span></div>
    {/each}
    {#each draft.span.gaps as gap}
      <div class="explanation-text"><span class="explanation-body">
        Gap {gap.left} → {gap.right} ({gap.min_blocks}–{gap.max_blocks} blocks) is not used in search yet.
      </span></div>
    {/each}
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
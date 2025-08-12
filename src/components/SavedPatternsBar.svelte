<script>
  import { createEventDispatcher } from "svelte";
  import PatternIcon from "./PatternIcon.svelte";
  import { clearAllPatterns } from "./cache.js";

  export let patterns = [];
  export let activePatternId = null;
  export let maxVisible = 8;

  const dispatch = createEventDispatcher();

  function handlePatternClick(event) {
    dispatch("pattern-click", event.detail);
  }

  function handlePatternContextMenu(event) {
    dispatch("pattern-contextmenu", event.detail);
  }

  function showMorePatterns() {
    dispatch("show-more-patterns");
  }

  async function handleClearAll() {
    if (
      confirm(
        "Are you sure you want to clear all saved patterns? This action cannot be undone."
      )
    ) {
      const success = await clearAllPatterns();
      if (success) {
        // 通知父组件数据已清空
        dispatch("patterns-cleared");
      }
    }
  }

  $: visiblePatterns = patterns.slice(1, patterns.length);
  $: remainingCount = 0;
</script>

<div class="saved-patterns-bar">
  <!-- <span class="patterns-label">📌 Saved Patterns:</span> -->

  {#if patterns.length === 0}
    <span class="no-patterns">No saved patterns yet</span>
  {:else}
    <div class="patterns-container">
      {#each visiblePatterns as pattern (pattern.id)}
        <PatternIcon
          {pattern}
          isActive={activePatternId === pattern.id}
          on:click={handlePatternClick}
          on:contextmenu={handlePatternContextMenu}
        />
      {/each}

      {#if remainingCount > 0}
        <button class="more-patterns-btn" on:click={showMorePatterns}>
          +{remainingCount}
        </button>
      {/if}

      <button
        class="clear-all-btn"
        on:click={handleClearAll}
        title="Clear all saved patterns"
      >
        Clear All
      </button>
    </div>
  {/if}
</div>

<style>
  .saved-patterns-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    font-size: 14px;
  }

  .patterns-label {
    font-weight: 500;
    color: #333;
    white-space: nowrap;
  }

  .no-patterns {
    color: #666;
    font-style: italic;
    font-size: 13px;
  }

  .patterns-container {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .more-patterns-btn {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 11px;
    color: #666;
    background-color: #f0f0f0;
    border: 1px dashed #ccc;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .more-patterns-btn:hover {
    background-color: #e0e0e0;
    transform: scale(1.05);
  }

  .clear-all-btn {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    color: #d32f2f;
    background-color: #ffebee;
    border: 1px solid #ffcdd2;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
  }

  .clear-all-btn:hover {
    background-color: #ffcdd2;
    border-color: #ef9a9a;
    transform: scale(1.05);
  }
</style>

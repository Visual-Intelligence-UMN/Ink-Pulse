<script>
  import { createEventDispatcher } from 'svelte';
  import PatternIcon from './PatternIcon.svelte';
  
  export let patterns = [];
  export let activePatternId = null;
  export let maxVisible = 8;
  
  const dispatch = createEventDispatcher();
  
  function handlePatternClick(event) {
    dispatch('pattern-click', event.detail);
  }
  
  function handlePatternContextMenu(event) {
    dispatch('pattern-contextmenu', event.detail);
  }
  
  function showMorePatterns() {
    dispatch('show-more-patterns');
  }
  
  $: visiblePatterns = patterns
    .filter(p => p.id !== "pattern_0")
    .slice(0, maxVisible);
  $: remainingCount = Math.max(0, patterns.length - maxVisible);
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
</style>
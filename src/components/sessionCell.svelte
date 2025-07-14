<script>
  import SemanticExpansionCircle from "../components/scoreIcon.svelte";
  import ZoomoutChart from "../components/zoomoutChart.svelte";
  import PatternIconSmall from "./PatternIconSmall.svelte";
  import { createEventDispatcher } from 'svelte';

  export let sessionData;
  export let onRowClick;
  export let onCategoryIconClick;
  export let chartRefs;
  export let getPromptCode;
  export let getCategoryIcon;
  export let colIndex = Infinity;
  export let showPatterns = false;
  export let patterns = [];
  export let activePatternId = null;

  const dispatch = createEventDispatcher();
  
  function getSessionPatterns(sessionId) {
    if (!patterns || patterns.length === 0) return [];
    
    return patterns.filter(pattern => {
      if (!pattern.pattern || pattern.pattern.length === 0) return false;
      return pattern.pattern.some(session => session.sessionId === sessionId);
    });
  }

  function handlePatternClick(event) {
    dispatch('pattern-click', event.detail);
  }

  function handlePatternContextMenu(event) {
    dispatch('pattern-contextmenu', event.detail);
  }

  $: sessionPatterns = sessionData ? getSessionPatterns(sessionData.sessionId) : [];
</script>

{#if sessionData}
  <td class="topic-cell">
    <button
      class="topic-icon-btn"
      on:click|stopPropagation={() =>
        onCategoryIconClick(getPromptCode(sessionData.sessionId))}
      title={getPromptCode(sessionData.sessionId)}
      type="button"
    >
      {getCategoryIcon(getPromptCode(sessionData.sessionId))}
    </button>
  </td>

  <td class="score-cell">
    <SemanticExpansionCircle
      llmJudgeScore={sessionData.llmScore}
      size={40}
      sessionId={sessionData.sessionId}
    />
  </td>

  {#if showPatterns}
    <td class="pattern-cell">
      <div class="pattern-icons-container">
        {#each sessionPatterns as pattern (pattern.id)}
          <PatternIconSmall 
            {pattern}
            isActive={activePatternId === pattern.id}
            on:click={handlePatternClick}
            on:contextmenu={handlePatternContextMenu}
          />
        {/each}
      </div>
    </td>
  {/if}

  <td class="activity-cell" class:add-right-border={colIndex === 0 || colIndex === 1}>
    <div class="mini-chart" on:click={() => onRowClick(sessionData)}>
      <ZoomoutChart
        bind:this={chartRefs[sessionData.sessionId]}
        sessionId={sessionData.sessionId}
        similarityData={sessionData.similarityData}
        on:containerClick={() => {}}
      />
    </div>
  </td>

  {#if colIndex < 2}
    <td class="spacer-cell"></td>
  {/if}

{:else}
  <td class="empty-cell"></td>
  <td class="empty-cell"></td>
  {#if showPatterns}
    <td class="empty-cell"></td>
  {/if}
  <td class="empty-cell"></td>
{/if}

<style>
  td {
    border-bottom: 1px solid #ccc;
    padding: 10px;
  }

  .pattern-cell {
    width: 80px;
    min-width: 60px;
    vertical-align: middle;
  }

  .pattern-icons-container {
    display: flex;
    align-items: center;
    gap: 2px;
    flex-wrap: wrap;
  }

  .activity-cell {
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .activity-cell:hover {
    background-color: rgba(0, 0, 0, 0.02);
  }

  .activity-cell.add-right-border {
    border-right: 1px solid #ddd;
  }

  .topic-cell {
    text-align: center;
  }

  .topic-icon-btn {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s ease;
  }

  .topic-icon-btn:hover {
    background-color: rgba(0, 0, 0, 0.05);
    transform: scale(1.1);
  }

  .score-cell {
    text-align: center;
    vertical-align: middle;
  }

  .empty-cell {

  }

  .spacer-cell {

  }
</style>
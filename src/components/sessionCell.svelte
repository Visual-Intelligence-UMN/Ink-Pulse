<script>
  import SemanticExpansionCircle from "../components/scoreIcon.svelte";
  import ZoomoutChart from "../components/zoomoutChart.svelte";
  export let sessionData;
  export let onRowClick;
  export let onCategoryIconClick;
  export let chartRefs;
  export let getPromptCode;
  export let getCategoryIcon;
</script>

{#if sessionData}
  <td class="activity-cell">
    <div class="mini-chart" on:click={() => onRowClick(sessionData)}>
      <ZoomoutChart
        bind:this={chartRefs[sessionData.sessionId]}
        sessionId={sessionData.sessionId}
        similarityData={sessionData.similarityData}
        on:containerClick={() => {}}
      />
    </div>
  </td>

  <td class="topic-cell">
    <button
      class="topic-icon-btn"
      on:click|stopPropagation={() =>
        onCategoryIconClick(getPromptCode(sessionData.sessionId))
      }
      title={getPromptCode(sessionData.sessionId)}
      type="button"
    >
      {getCategoryIcon(getPromptCode(sessionData.sessionId))}
    </button>
  </td>

  <td class="score-cell">
    <SemanticExpansionCircle 
      llmJudgeScore={sessionData.llmScore}
      size={16}
      sessionId={sessionData.sessionId}
    />
  </td>
{:else}
  <td class="empty-cell"></td>
  <td class="empty-cell"></td>
  <td class="empty-cell"></td>
{/if}

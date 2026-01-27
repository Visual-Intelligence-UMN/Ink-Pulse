<script>
  import SemanticExpansionCircle from "../components/scoreIcon.svelte";
  import ZoomoutChart from "../components/zoomoutChart.svelte";
  import PatternIconSmall from "./PatternIconSmall.svelte";
  import { createEventDispatcher } from "svelte";

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
  export let noRightBorder = false;
  export let highlightPatterns = null;

  const dispatch = createEventDispatcher();

  function getSessionPatterns(sessionId) {
    if (!patterns || patterns.length === 0) return [];

    return patterns.filter((pattern) => {
      if (!pattern.pattern || pattern.pattern.length === 0) return false;
      return pattern.pattern.some((session) => session.sessionId === sessionId);
    });
  }

  function handlePatternClick(event) {
    dispatch("pattern-click", event.detail);
  }

  function handlePatternContextMenu(event) {
    dispatch("pattern-contextmenu", event.detail);
  }

  $: sessionPatterns = sessionData
    ? getSessionPatterns(sessionData.sessionId)
    : [];
</script>

{#if sessionData && sessionData.sessionId}
  <td class="topic-cell">
    <button
      class="topic-icon-btn"
      on:click|stopPropagation={() =>
        onCategoryIconClick(getPromptCode(sessionData.sessionId))}
      title={getPromptCode(sessionData.sessionId)}
      type="button"
    >
      {@html getCategoryIcon(getPromptCode(sessionData.sessionId))}
    </button>
  </td>

  <td class="score-cell">
    <SemanticExpansionCircle
      llmJudgeScore={sessionData.llmScore}
      size={30}
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

  <td
    class="activity-cell"
    class:add-right-border={(colIndex === 0 || colIndex === 1) &&
      !noRightBorder}
  >
    <div
      class="mini-chart"
      role="button"
      tabindex="0"
      on:click={() => onRowClick(sessionData)}
      on:keydown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onRowClick(sessionData);
        }
      }}
    >
      <ZoomoutChart
        bind:this={chartRefs[sessionData.sessionId]}
        sessionId={sessionData.sessionId}
        similarityData={sessionData.similarityData}
        on:containerClick={() => {}}
        {highlightPatterns}
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

  /* Beautiful styling for topic letters with dynamic colors */
  :global(.topic-letters) {
    font-family:
      "Inter",
      "SF Pro Display",
      "Segoe UI",
      "Roboto",
      -apple-system,
      sans-serif;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.5px;

    /* Fallback color for browsers that don't support CSS variables */
    color: #667eea;

    /* Dynamic gradient text effect using CSS variables */
    background: linear-gradient(
      135deg,
      var(--topic-color-primary, #667eea) 0%,
      var(--topic-color-secondary, #764ba2) 100%
    );
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    /* Enhanced typography */
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;

    /* Subtle shadow for depth using dynamic color */
    filter: drop-shadow(
      0 1px 2px
        color-mix(in srgb, var(--topic-color-primary, #667eea) 30%, transparent)
    );

    display: inline-block;
    transform: translateZ(0);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .topic-icon-btn:hover :global(.topic-letters) {
    /* Fallback hover color */
    color: var(--topic-color-hover, #f093fb);

    /* Dynamic hover gradient */
    background: linear-gradient(
      135deg,
      var(--topic-color-hover, #f093fb) 0%,
      var(--topic-color-primary, #f5576c) 100%
    );
    background-clip: text;
    -webkit-background-clip: text;
    transform: scale(1.08) translateZ(0);
    filter: drop-shadow(
      0 2px 4px
        color-mix(in srgb, var(--topic-color-hover, #f093fb) 40%, transparent)
    );
  }

  .score-cell {
    text-align: center;
    vertical-align: middle;
  }
</style>

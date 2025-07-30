<script>
  import { createEventDispatcher } from 'svelte';
  import SessionCell from './sessionCell.svelte';
  import { getCategoryIcon } from './topicIcons.js';
  import ScoreSummaryChart from './scoreSummaryChart.svelte';
  import PercentageChart from './percentageChart.svelte'
  import LengthChart from './lengthChart.svelte';
  import OverallSemScoreChart from './overallSemScoreChart.svelte';
  import PatternChartPreview from './patternChartPreview.svelte';
  
  export let pattern;
  export let sessions;
  export let chartRefs = {};
  export let percentageData;
  export let lengthData;
  export let searchPatternSet;
  const init = searchPatternSet.find(p => p.id === "pattern_0");
  let scoreSummary = init.scoreSummary;
  let percentageSummaryData = init.percentageSummaryData;
  let lengthSummaryData = init.lengthSummaryData;
  let overallSemScoreData = init.overallSemScoreData;
  let overallSemScoreSummaryData = init.overallSemScoreSummaryData;
  let flag = "overall";
  let title = [];
  
  const dispatch = createEventDispatcher();
  
  function handleBack() {
    dispatch('back');
  }
  
  function handleApplyPattern() {
    dispatch('apply-pattern', { pattern });
  }
  
  function handleEditPattern() {
    dispatch('edit-pattern', { pattern });
  }
  
  function handleDeletePattern() {
    dispatch('delete-pattern', { pattern });
  }
  
  function handleRowClick(sessionData) {
    dispatch('row-click', { sessionData });
  }
  
  function getPromptCode(sessionId) {
    const found = sessions.find((s) => s.session_id === sessionId);
    return found?.prompt_code ?? "";
  }
  
  function getScoreDisplay(score) {
    if (!score) return 'N/A';
    const stars = '⭐'.repeat(Math.floor(score / 20)) + '☆'.repeat(5 - Math.floor(score / 20));
    return `${score.toFixed(1)} ${stars}`;
  }

  function handleSelectChange(event) {
    const selectedValue = event.target.value;
    if (selectedValue == "pattern_0") {
      flag = "overall";
      title = [pattern.name, searchPatternSet.find(p => p.id === selectedValue).name];
      scoreSummary = init.scoreSummary;
      percentageSummaryData = init.percentageSummaryData;
      lengthSummaryData = init.lengthSummaryData;
      overallSemScoreData = init.overallSemScoreData;
      overallSemScoreSummaryData = init.overallSemScoreSummaryData;
    } 
    else {
      flag = selectedValue;
      title = [pattern.name, searchPatternSet.find(p => p.id === selectedValue).name]
      let select = searchPatternSet.find(p => p.id === selectedValue);
      const patternSessions = select.pattern || [];
      const temp = {};
      for (const session of patternSessions) {
        const score = Number(session.llmScore);
        temp[score] = (temp[score] || 0) + 1;
      }
      scoreSummary = Object.fromEntries(
        Object.entries(temp).map(([k, v]) => [Number(k), v])
      );
      percentageSummaryData = select.pattern;
      lengthSummaryData = select.pattern;
      overallSemScoreSummaryData = select.pattern;
    }
    
  }

  $: patternSessions = pattern?.pattern || [];
  let scoreCount = {};
  $: {
    const temp = {};
    for (const session of patternSessions) {
      const score = Number(session.llmScore);
      temp[score] = (temp[score] || 0) + 1;
    }
    scoreCount = Object.fromEntries(
      Object.entries(temp).map(([k, v]) => [Number(k), v])
    );
  }
  let selectedId = "pattern_0";
</script>

<div class="pattern-detail-container">
  <div class="pattern-detail-header">
    <button class="back-button" on:click={handleBack}>
      ← Back
    </button>
    <h2>Pattern "{pattern?.name}" Details</h2>
    <button class="close-button" on:click={handleBack}>✕</button>
  </div>
  
  <div class="pattern-info">
    <div class="pattern-icon-large" style="background-color: {pattern?.color}">
      {pattern?.name?.slice(0, 2).toUpperCase() || '?'}
    </div>
    <div class="pattern-stats">
      <span>📊 {patternSessions.length} sessions</span>
      <span>📅 Created: {pattern?.metadata?.createdAt ? new Date(pattern.metadata.createdAt).toLocaleDateString() : 'Recently'}</span>
      <div style="display: flex; align-items: center; gap: 10px;">
        <span>⚖️ 
          <span style="width: 10px; height: 10px; background-color: {pattern.color}; border-radius: 50%; display: inline-block;"
          aria-label="color dot"></span>
          {pattern.name}</span>
        <span>VS</span>
        <select id="pattern-select" bind:value={selectedId} on:change={handleSelectChange}>
          {#each searchPatternSet as pattern}
            <option value={pattern.id}>{pattern.name}</option>
          {/each}
        </select>
      </div>
      <span></span>
    </div>
  </div>

  <div class="pattern-item" >
    <div class="pattern-header">
      <h5>Session: {pattern.searchDetail.sessionId.slice(0, 4)}</h5>
    </div>
    <div class="pattern-details">
      <div>
        Semantic Change: {pattern.searchDetail.dataRange.scRange.min.toFixed(
          2
        )} - {pattern.searchDetail.dataRange.scRange.max.toFixed(2)}
      </div>
      <div>
        Progress Range: {pattern.searchDetail.dataRange.progressRange.min.toFixed(
          2
        )}% - {pattern.searchDetail.dataRange.progressRange.max.toFixed(2)}%
      </div>
      <div>
        Counts: {pattern.searchDetail.count}
      </div>
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
      <div class="pattern-chart-preview small-preview">
        <PatternChartPreview
        sessionId = {pattern.searchDetail.sessionId}
        data={pattern.searchDetail.data}
        wholeData={pattern.searchDetail.wholeData}
        selectedRange={pattern.searchDetail.range}
        bind:this={chartRefs[pattern.searchDetail.sessionId]}
        />
      </div>
      <div style="margin-top: 15px; margin-left:10px; width: 40%">
        <div
          style="display: flex; align-items: center; font-size: 13px; color: #5f6368;"
        >
          <input
            type="checkbox"
            class="readonly"
            checked={pattern.searchDetail.flag.isProgressChecked}
            disabled
          />
          Writing Progress
          <div style="flex: 1;"></div>
        </div>
        <div
          style="display: flex; align-items: center; font-size: 13px; color: #5f6368;"
        >
          <input
            type="checkbox"
            class="readonly"
            checked={pattern.searchDetail.flag.isTimeChecked}
            disabled />
          Time
          <div style="flex: 1"></div>
        </div>
        <div
          style="font-size: 13px; color: #5f6368;"
        >
          <input
            type="checkbox"
            class="readonly"
            checked={pattern.searchDetail.flag.isSourceChecked}
            disabled
          />
          Source(human/AI)
          <label
            class="switch"
            style="transform: translateY(4px);"
          >
            <input
              type="checkbox"
              class="readonly"
              checked={pattern.searchDetail.flag.isExactSearchSource}
              disabled
              hidden
            />
            <span class="slider readonly"></span>
          </label>
        </div>
        <div style="font-size: 13px; color: #5f6368;">
          <div>
            <input
              type="checkbox"
              class="readonly"
              checked={pattern.searchDetail.flag.isSemanticChecked}
              disabled
            />
            Semantic Expansion
          </div>
          <div style="margin-left: 20px; color: #5f6368;">
            <div>
              <input
                type="checkbox"
                class="readonly"
                checked={pattern.searchDetail.flag.isValueRangeChecked}
                disabled
              />
              Value Range
            </div>
            <div>
              <input
                type="checkbox"
                class="readonly"
                checked={pattern.searchDetail.flag.isValueTrendChecked}
                disabled
              />
              Value Trend
              <label
                class="switch"
                style="transform: translateY(4px);"
              >
                <input
                  type="checkbox"
                  class="readonly"
                  checked={pattern.searchDetail.flag.isExactSearchTrend}
                  disabled
                  hidden
                />
                <span class="slider readonly"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div style="display: flex; justify-content: center;">
    <ScoreSummaryChart
      rawData = {scoreSummary}
      nowData = {scoreCount}
      {title}
    />
  </div>
  <div style="display: flex; justify-content: center;">
    <PercentageChart
      {patternSessions}
      {percentageSummaryData}
      {percentageData}
      {flag}
      {title}
    />
  </div>
  <div style="display: flex; justify-content: center;">
    <LengthChart
      {patternSessions}
      {lengthData}
      {lengthSummaryData}
      {flag}
      {title}
    />
  </div>
  <div style="display: flex; justify-content: center;">
    <OverallSemScoreChart
      {patternSessions}
      {overallSemScoreData}
      {overallSemScoreSummaryData}
      {flag}
      {title}
    />
  </div>
  
  <div class="table-container">
    <table class="pattern-sessions-table">
      <thead>
        <tr>
          <th style="width: 100%">Activity</th>
        </tr>
        <tr>
        </tr>
      </thead>
      <tbody>
        {#each patternSessions as sessionData, _ (sessionData.sessionId)}
          <tr class="session-row" on:click={() => handleRowClick(sessionData)}>
            <td class="activity-cell">
              <SessionCell
                {sessionData}
                {chartRefs}
                onRowClick={handleRowClick}
                onCategoryIconClick={() => {}}
                {getPromptCode}
                {getCategoryIcon}

              />
            </td>
          </tr>
        {/each}
        
        {#if patternSessions.length === 0}
          <tr>
            <td colspan="1" class="empty-state">
              No sessions found in this pattern
            </td>
          </tr>
        {/if}
      </tbody>
    </table>
  </div>
  
  <div class="action-buttons">
    <button class="btn btn-primary" on:click={handleApplyPattern}>
      Apply This Pattern
    </button>
    <button class="btn btn-secondary" on:click={handleEditPattern}>
      Edit Pattern
    </button>
    <button class="btn btn-danger" on:click={handleDeletePattern}>
      Delete Pattern
    </button>
  </div>
</div>

<style>
  .pattern-detail-container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    min-height: 100vh;
    overflow: visible;
  }
  
  .pattern-detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e0e0e0;
  }
  
  .pattern-detail-header h2 {
    margin: 0;
    font-size: 24px;
    color: #333;
  }
  
  .back-button, .close-button {
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    padding: 8px 12px;
    border-radius: 4px;
    transition: background-color 0.2s ease;
  }
  
  .back-button:hover, .close-button:hover {
    background-color: #f0f0f0;
  }
  
  .pattern-info {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 25px;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
  }
  
  .pattern-icon-large {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
    color: white;
  }
  
  .pattern-stats {
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 14px;
    color: #666;
  }
  
  .table-container {
    background: white;
    border-radius: 8px;
    overflow: visible;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 25px;
    max-height: none;
  }
  
  .pattern-sessions-table {
    width: 100%;
    border-collapse: collapse;
  }
  
  .pattern-sessions-table thead {
    background-color: #f8f9fa;
  }
  
  .pattern-sessions-table th {
    padding: 15px;
    text-align: left;
    font-weight: 600;
    color: #333;
    border-bottom: 2px solid #e0e0e0;
  }
  
  .pattern-sessions-table tbody {
    max-height: none;
    overflow: visible;
  }
  
  .session-row {
    cursor: pointer;
    transition: background-color 0.2s ease;
    margin-bottom: 0px;
  }
  
  .session-row:hover {
    background-color: #f8f9fa;
  }
  
  .session-row:not(:last-child) {
    border-bottom: 1px solid #e0e0e0;
  }
  
  .activity-cell {
    vertical-align: top;
  }
  
  .topic-cell {
    padding: 15px;
    vertical-align: middle;
  }
  
  .topic-content {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .topic-icon {
    font-size: 18px;
  }
  
  .topic-name {
    font-weight: 500;
    color: #333;
  }
  
  .score-cell {
    padding: 15px;
    vertical-align: middle;
    font-size: 14px;
  }
  
  .empty-state {
    padding: 40px;
    text-align: center;
    color: #666;
    font-style: italic;
  }
  
  .action-buttons {
    display: flex;
    gap: 12px;
    justify-content: center;
    padding-top: 20px;
  }
  
  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .btn-primary {
    background-color: #007bff;
    color: white;
  }
  
  .btn-primary:hover {
    background-color: #0056b3;
    transform: translateY(-1px);
  }
  
  .btn-secondary {
    background-color: #6c757d;
    color: white;
  }
  
  .btn-secondary:hover {
    background-color: #545b62;
    transform: translateY(-1px);
  }
  
  .btn-danger {
    background-color: #dc3545;
    color: white;
  }
  
  .btn-danger:hover {
    background-color: #c82333;
    transform: translateY(-1px);
  }

   .pattern-item {
    background-color: #f8f9fa;
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 12px;
  }
  
   .pattern-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

    .pattern-details {
    font-size: 13px;
    color: #5f6368;
    margin-bottom: 10px;
  }

    .pattern-chart-preview {
    width: 240px;
    height: 192px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    margin-top: 10px;
    background-color: white;
  }

  .readonly {
    opacity: 0.5;

  }

  input:checked+.slider {
  background-color: #ffbbcc;
}

input:checked+.slider::before {
  transform: translateX(11px);
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.2s;
  border-radius: 28px;
}

.slider::before {
  position: absolute;
  content: "";
  height: 11px;
  width: 11px;
  left: 1.5px;
  bottom: 1.5px;
  background-color: white;
  transition: 0.2s;
  border-radius: 50%;
}

.switch {
  position: relative;
  display: inline-block;  /* or inline-flex */
  width: 26px;             /* or whatever width you need */
  height: 14px;
  margin-left: 3px;
}
  
  
</style>
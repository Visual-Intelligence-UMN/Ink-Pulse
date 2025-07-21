<script>
  import { createEventDispatcher } from 'svelte';
  import SessionCell from './sessionCell.svelte';
  import { getCategoryIcon } from './topicIcons.js';
  import ScoreSummaryChart from './scoreSummaryChart.svelte';
  
  export let pattern;
  export let sessions;
  export let chartRefs = {};
  export let scoreSummary;
  
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
  
  $: patternSessions = pattern?.pattern || [];
  $: scoreCount = {};
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
      <span></span>
    </div>
  </div>

  <div style="width: 100%; display: flex; justify-content: center;">
    <ScoreSummaryChart 
      rawData = {scoreSummary}
      nowData = {scoreCount}
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
                colIndex={0}
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
  }
  
  .session-row:hover {
    background-color: #f8f9fa;
  }
  
  .session-row:not(:last-child) {
    border-bottom: 1px solid #e0e0e0;
  }
  
  .activity-cell {
    padding: 10px 15px;
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
  
  
</style>
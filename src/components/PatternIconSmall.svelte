<script>
  import { createEventDispatcher } from 'svelte';
  
  export let pattern;
  export let isActive = false;
  
  const dispatch = createEventDispatcher();
  
  function handleClick() {
    dispatch('click', { pattern });
  }
  
  function handleContextMenu(event) {
    event.preventDefault();
    dispatch('contextmenu', { pattern, event });
  }
  

  function getDisplayText(name) {
    if (!name) return '?';
    return name.length <= 2 ? name.toUpperCase() : name.slice(0, 2).toUpperCase();
  }
  

  function getAverageScore(pattern) {
    if (!pattern.pattern || pattern.pattern.length === 0) return 0;
    const total = pattern.pattern.reduce((sum, session) => sum + (session.llmScore || 0), 0);
    return (total / pattern.pattern.length).toFixed(1);
  }
</script>

<div 
  class="pattern-icon-small" 
  class:active={isActive}
  style="background-color: {pattern.color}"
  on:click={handleClick}
  on:contextmenu={handleContextMenu}
  title="Pattern '{pattern.name}' - {pattern.pattern.length} sessions - Avg Score: {getAverageScore(pattern)}"
>
  {getDisplayText(pattern.name)}
</div>

<style>
  .pattern-icon-small {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 9px;
    color: white;
    margin-right: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    user-select: none;
  }
  
  .pattern-icon-small:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
  
  .pattern-icon-small.active {
    box-shadow: 0 0 0 1px #fff, 0 0 0 2px var(--pattern-color);
    transform: scale(1.05);
  }
</style>
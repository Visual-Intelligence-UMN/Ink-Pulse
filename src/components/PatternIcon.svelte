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
  
  // 获取首字母或前两个字符
  function getDisplayText(name) {
    if (!name) return '?';
    return name.length <= 2 ? name.toUpperCase() : name.slice(0, 2).toUpperCase();
  }
  
  // 计算平均分数
  function getAverageScore(pattern) {
    if (!pattern.pattern || pattern.pattern.length === 0) return 0;
    const total = pattern.pattern.reduce((sum, session) => sum + (session.llmScore || 0), 0);
    return (total / pattern.pattern.length).toFixed(1);
  }
</script>

<div 
  class="pattern-icon" 
  class:active={isActive}
  style="background-color: {pattern.color}"
  on:click={handleClick}
  on:contextmenu={handleContextMenu}
  title="Pattern '{pattern.name}' - {pattern.pattern.length} sessions - Avg Score: {getAverageScore(pattern)}"
>
  {getDisplayText(pattern.name)}
</div>

<style>
  .pattern-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 12px;
    color: white;
    margin-right: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    user-select: none;
  }
  
  .pattern-icon:hover {
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .pattern-icon.active {
    box-shadow: 0 0 0 2px #fff, 0 0 0 4px var(--pattern-color);
    transform: scale(1.05);
  }
</style>
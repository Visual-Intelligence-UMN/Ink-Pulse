<script>
  import { createEventDispatcher } from "svelte";
  import "../components/styles.css";
  import { base } from '$app/paths';
  
  let apiKey = "";
  let inputMessage = "";
  let openSetting = false;
  const dispatch = createEventDispatcher();
  let showSavedMessage = false;
  let result = {
    explanations: [],
    filters: []
  };
  export let pattern;
  pattern = pattern.data
  const signal = convertPatternToSignal(pattern);
  let openRatioIndex = null;
  let ratioSelections = {};
  
  let userInput = ''
  const SYSTEM_PROMPT = `
    You are an interpretation engine for Human–AI collaborative writing analysis.

    The user provides:
    1. A natural-language observation about a selected part of a writing session
    2. A structured pattern extracted from the selected region of a chart

    Your responsibility is NOT to compute numeric values or perform database search.
    Your responsibility IS to:
    - Identify which system-defined features are important
    - Explain those features in clear, user-friendly language
    - Express relationships between features in a way that can later be translated into database queries

    INPUT ASSUMPTIONS

    - The provided pattern is authoritative and already computed.
    - Do NOT invent numeric thresholds.
    - Treat all comparisons as RELATIVE (e.g., Human > AI).

    SYSTEM FEATURES

    You may ONLY reason about the following features:

    - source: who is writing: human or AI, and in what order

    - progress: relative amount of writing contributed by each source

    - semantic_change: relative novelty of content

    - time: ordering of writing segments

    EXPRESSION OF MAGNITUDE

    When describing how much larger, smaller, or stronger one side is than another,
    you MAY express magnitude using selectable ratio-style markers embedded directly
    in the explanation text.

    Use the following syntax EXACTLY:

    - [3x] (2x, 4x)

    Rules:
    - Exactly ONE option must be wrapped in square brackets [] (default)
    - All other options must be wrapped in parentheses ()

    Examples:
    - "The human contributes [1.5x] (2x, 3x) more writing than the AI."
    - "The AI introduces a [3x] (2x, 2.5x) stronger semantic shift."

    OUTPUT A — Feature-Based Explanations

    Produce a list of explanations.

    Rules:
    - Each explanation MUST correspond to EXACTLY ONE feature
    - Use non-technical, user-facing language

    Each explanation should describe:
    - What happened
    - Why this feature is relevant

    OUTPUT B — Searchable Feature Relations

    For each explanation in OUTPUT A, produce ONE corresponding searchable relation.

    Rules:
    - CRITICAL: There MUST be exactly one filter for each explanation - the arrays must be the same length
    - Each relation MUST map one-to-one to an explanation at the same index
    - Use relative comparisons only (>, <, =)
    - Use Human(...) and AI(...), e.g., Human(progress) > AI(progress), for source-specific aggregation
    - Use trends/directions (increasing, decreasing, stable) to represent multi-block patterns

    How to handle the "source" feature:
    - When explaining source patterns (e.g., "Human writes first, then AI responds"), you MUST still create a corresponding filter
    - For source filters, set relation to null or "source_pattern"
    - The source pattern itself will be handled separately by the source constraint logic

    Position information:
    - For trends (increasing, decreasing, stable):
        - Indicate which part of the selected sequence the trend applies to using "span":
            - "prefix": continuous blocks of the same source at the start
            - "suffix": continuous blocks of the same source at the end
            - "full": entire selected sequence
    - For comparisons (>, <, =):
        - Indicate which blocks are compared using:
            - "l_position": "first", "last", "prev"
            - "r_position": "first", "last", "prev"

    Constraints:
    - MANDATORY: The order and the number of the JSON objects in FormattedFilter MUST EXACTLY match the order and the number of Explanations
    - If there are 3 explanations, there MUST be 3 filters
    - If there are 5 explanations, there MUST be 5 filters
    - Output RAW JSON ONLY
    - Do NOT wrap the response in Markdown.

    OUTPUT FORMAT:

    {
      "Explanations": [
        {
          "feature": "<feature_name>",
          "text": "<user-friendly explanation>"
        }
      ],
      "FormattedFilter": [
        {
          "feature": "<feature_name>",
          "relation": "<searchable relation or null for source>",
          "span": "<prefix/suffix/full or null>",
          "l_position": "<first/last/prev or null>",
          "r_position": "<first/last/prev or null>"
        }
      ]
    }

    EXAMPLE 1 - With source feature:
    {
      "Explanations": [
        {
          "feature": "source",
          "text": "The human writes first, followed by the AI."
        },
        {
          "feature": "progress",
          "text": "The human contributes [2x] (3x, 4x) more writing than the AI."
        }
      ],
      "FormattedFilter": [
        {
          "feature": "source",
          "relation": null,
          "span": null,
          "l_position": null,
          "r_position": null
        },
        {
          "feature": "progress",
          "relation": "Human(progress) > AI(progress)",
          "span": "full",
          "l_position": null,
          "r_position": null
        }
      ]
    }

    EXAMPLE 2 - Without source feature:
    {
      "Explanations": [
        {
          "feature": "progress",
          "text": "The human contributes [2x] (3x, 4x) more writing than the AI."
        },
        {
          "feature": "time",
          "text": "The AI takes [1.5x] (2x, 2.5x) longer to write."
        }
      ],
      "FormattedFilter": [
        {
          "feature": "progress",
          "relation": "Human(progress) > AI(progress)",
          "span": "full",
          "l_position": null,
          "r_position": null
        },
        {
          "feature": "time",
          "relation": "AI(time) > Human(time)",
          "span": "full",
          "l_position": null,
          "r_position": null
        }
      ]
    }
  `;

  const featureStyleMap = {
    source: {
      label: 'Source',
      bg: '#e3f2fd',
      color: '#1565c0'
    },
    progress: {
      label: 'Progress',
      bg: '#fff3e0',
      color: '#ef6c00'
    },
    semantic_change: {
      label: 'Semantic',
      bg: '#e8f5e9',
      color: '#2e7d32'
    },
    time: {
      label: 'Time',
      bg: '#f3e5f5',
      color: '#6a1b9a'
    }
  };
  
  function round2(num) {
    return Math.round(num * 100) / 100;
  }
  
  function convertPatternToSignal(pattern) {
    if (!pattern || pattern.length === 0) return null;
    const sourceTrend = pattern.map(block => block.source);
    const progressDiff = [];
    const timeDiff = [];
    const semanticDiff = [];
    for (let i = 0; i < pattern.length; i++) {
      progressDiff.push(
        round2(pattern[i].endProgress - pattern[i].startProgress)
      );
      timeDiff.push(
        round2(pattern[i].endTime - pattern[i].startTime)
      );
      semanticDiff.push(
        round2(pattern[i].residual_vector_norm)
      );
    }
    
    return {
      sourceTrend,
      progress: progressDiff,
      time: timeDiff,
      semantic_change: semanticDiff
    };
  }
  
  async function sendMessageToAPI(userInput) {
    const messages = [
      {
        role: "system",
        content: SYSTEM_PROMPT
      },
      {
        role: "user",
        content: JSON.stringify({
          userObservation: userInput,
          selectedPattern: signal
        })
      }
    ];
    const response = await fetch(`${base}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        apiKey,
        messages
      })
    });
    const data = await response.json();
    if (!data.choices || data.choices.length === 0) {
      throw new Error(data.error?.message || 'No choices returned from API');
    }
    
    return data.choices[0].message.content;
  }
  
  async function handleSendMessage() {
    if (inputMessage.trim() === "") return;
    console.log("Sending message:", inputMessage);
    try {
      const raw = await sendMessageToAPI(inputMessage);
      const parsed = JSON.parse(raw);
      result = {
        explanations: parsed.Explanations || [],
        filters: parsed.FormattedFilter || []
      };
      ratioSelections = {};
      result.explanations.forEach((exp, expIndex) => {
        const parts = parseRatioText(exp.text);
        parts.forEach(part => {
          if (part.type === 'ratio') {
            const key = getUniqueDropdownId(expIndex, part.id);
            ratioSelections[key] = part.selected;
          }
        });
      });
      
      sendParsedFilters();
    } catch (err) {
      console.error("Send failed:", err);
      result = { explanations: err.message, filters: [] };
    }
  }
  
  function toggleSettingsWindow() {
    openSetting = !openSetting;
  }
  
  function handleSetApiKey() {
    if (apiKey.trim() === "") {
      showSavedMessage = false;
      toggleSettingsWindow();
      dispatch('setKey', apiKey);
    } else {
      showSavedMessage = true;
      toggleSettingsWindow();
      dispatch('setKey', apiKey);
    }
  }
  
  function handleAnimationEnd() {
    showSavedMessage = false;
  }
  
  let textareaEl;
  function autoResize() {
    textareaEl.style.height = 'auto';
    textareaEl.style.height = textareaEl.scrollHeight + 'px';
  }
  
  function removeExplanation(index) {
    const parts = parseRatioText(result.explanations[index].text);
    parts.forEach(part => {
      if (part.type === 'ratio') {
        const key = getUniqueDropdownId(index, part.id);
        delete ratioSelections[key];
      }
    });
    
    result.explanations.splice(index, 1);
    if (result.filters && result.filters.length > index) {
      result.filters.splice(index, 1);
    }
    result = { ...result };
    sendParsedFilters();
  }
  
  function parseFilterObject(filter) {
    if (!filter) return null;
    if (typeof filter === 'string') {
      console.warn('Filter is a string:', filter);
      return null;
    }
    return filter;
  }
  
  const ratioRegex = /\[([^\]]+)\]|\(([^)]+)\)/g;
  function parseRatioText(text) {
    const parts = [];
    let lastIndex = 0;
    let currentRatio = null;
    let nextId = 0;
    for (const match of text.matchAll(ratioRegex)) {
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          value: text.slice(lastIndex, match.index),
          id: nextId++
        });
      }
      if (match[1]) {
        currentRatio = {
          type: 'ratio',
          selected: match[1],
          options: [match[1]],
          id: nextId++
        };
        parts.push(currentRatio);
      } else if (match[2] && currentRatio) {
        const opts = match[2].split(',').map(o => o.trim());
        currentRatio.options.push(...opts);
      }
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        value: text.slice(lastIndex),
        id: nextId++
      });
    }
    
    return parts;
  }
  
  function parseAllFilters(filters) {
    const parsed = filters.map(parseFilterObject).filter(f => f !== null);
    return parsed;
  }
  
  function sendParsedFilters() {
    const parsedFilters = parseAllFilters(result.filters);
    const explanationsWithRatios = result.explanations.map((exp, expIndex) => {
      const parts = parseRatioText(exp.text);
      let reconstructedText = '';
      const ratioInfo = [];
      parts.forEach(part => {
        if (part.type === 'text') {
          reconstructedText += part.value;
        } else if (part.type === 'ratio') {
          const key = getUniqueDropdownId(expIndex, part.id);
          const selectedValue = ratioSelections[key] || part.selected;
          reconstructedText += `(${selectedValue})`;
          ratioInfo.push({
            selected: selectedValue,
            options: part.options
          });
        }
      });
      
      return {
        feature: exp.feature,
        text: reconstructedText,
        ratios: ratioInfo.length > 0 ? ratioInfo : undefined
      };
    });
    const filtersWithRatio = parsedFilters.map((filter, i) => {
      const explanation = explanationsWithRatios[i];
      let ratio = null;
      if (explanation?.ratios && explanation.ratios.length > 0) {
        const ratioStr = explanation.ratios[0].selected;
        const match = ratioStr.match(/(\d+(?:\.\d+)?)x/);
        ratio = match ? parseFloat(match[1]) : null;
      }
      
      return {
        ...filter,
        ratio: ratio
      };
    });
    
    console.log("Sending - explanations:", explanationsWithRatios, "filters with ratio:", filtersWithRatio);
    
    dispatch('parsedFilters', { 
      explanations: explanationsWithRatios, 
      filters: filtersWithRatio
    });
  }

  function selectRatioOption(expIndex, partId, option) {
    const key = getUniqueDropdownId(expIndex, partId);
    ratioSelections[key] = option;
    result.explanations[expIndex].text = result.explanations[expIndex].text.replace(
      new RegExp(`\\[${escapeRegex(parseRatioText(result.explanations[expIndex].text).find(p => p.id === partId)?.selected || '')}\\]`),
      `[${option}]`
    );
    result = { ...result };
    openRatioIndex = null;
    sendParsedFilters();
  }

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function getUniqueDropdownId(expIndex, partId) {
    return `${expIndex}-${partId}`;
  }
</script>

<div class="chat-content">
  <div class="header">
    <h3>Interpretation</h3>
    <div class="header-actions">
      <button on:click={toggleSettingsWindow} class="settings-btn">⚙</button>
    </div>
  </div>
  {#if openSetting}
    <div class="panel">
      <h4>API Key</h4>
      <input type="text" bind:value={apiKey} placeholder="Enter OpenAI API Key"
         style="width: 100%; padding: 0.5rem; margin-bottom: 1rem;" />
      <button on:click={handleSetApiKey} style="width: 100%; padding: 0.5rem; background-color: #137a7f;
         color: white; border: none; border-radius: 4px; cursor: pointer;">Save API Key</button>
    </div>
  {/if}
  <div class="input-area">
    <textarea
      bind:this={textareaEl}
      bind:value={inputMessage}
      placeholder="Enter message..."
      rows="1"
      on:input={autoResize}
      on:keydown={(e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSendMessage();
        }
      }}
    />
  </div>
  <div style="margin-top: 0.5rem;">
    <button on:click={handleSendMessage} class="send-btn">Check</button>
  </div>
  {#if result?.explanations}
      <div class="explanation-container">
        {#each result.explanations as exp, expIndex}
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
            {#each parseRatioText(exp.text) as part (part.id)}
              {#if part.type === 'text'}
                {part.value}
              {:else if part.type === 'ratio'}
                {#if part.options.length > 1}
                  <span class="ratio-wrapper">
                    <button
                      type="button"
                      class="ratio-selected"
                      aria-haspopup="listbox"
                      aria-expanded={openRatioIndex === getUniqueDropdownId(expIndex, part.id)}
                      on:click={() => openRatioIndex = openRatioIndex === getUniqueDropdownId(expIndex, part.id) ? null : getUniqueDropdownId(expIndex, part.id)}
                    >
                      {part.selected} ▾
                    </button>
                    
                    {#if openRatioIndex === getUniqueDropdownId(expIndex, part.id)}
                      <ul class="ratio-menu" role="listbox">
                        {#each part.options as opt}
                          <li
                            role="option"
                            aria-selected={opt === part.selected}
                            class="ratio-item {opt === part.selected ? 'active' : ''}"
                            on:click={() => selectRatioOption(expIndex, part.id, opt)}
                          >
                            {opt}
                          </li>
                        {/each}
                      </ul>
                    {/if}
                  </span>
                {:else}
                  {part.selected}
                {/if}
              {/if}
            {/each}
            <span class="close-button" on:click={() => removeExplanation(expIndex)}>
              ×
            </span>
          </span>
        {/each}
      </div>
  {/if}
  <ul class="filter-list">
    {#each result.filters as filter}
      <li>
        {filter.relation}
        
        {filter.span ? `(span: ${filter.span})` : ''}
        {filter.l_position ? `(lhs: ${filter.l_position})` : ''}
        {filter.r_position ? `(rhs: ${filter.r_position})` : ''}
      </li>
    {/each}
  </ul>
</div>

{#if showSavedMessage}
    <div class="saved-message" on:animationend={handleAnimationEnd}>
        API Key has been successfully set.
    </div>
{/if}

<style>
  .settings-btn {
    background-color: transparent;
    border: none;
    font-size: 20px;
    color: #333;
    cursor: pointer;
  }
  
  .settings-btn {
    font-size: 24px;
    padding: 5px;
    cursor: pointer;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    border-radius: 8px 8px 0 0;
    height: 10px;
  }
  
  .chat-content {
    background-color: white;
    padding: 1rem;
    border-radius: 8px;
    max-width: 400px;
    margin: auto;
  }
  
  .input-area {
    display: flex;
    gap: 0.5rem;
  }
  
  .input-area textarea {
    width: 100%;
    padding: 0.5rem;
    border-radius: 4px;
    resize: none;
    overflow-y: hidden;
    line-height: 1.4;
    box-sizing: border-box;
  }
  
  input[type="text"] {
    width: 90%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
  }
  
  .send-btn {
    padding: 0.5rem 1rem;
    background-color: #137a7f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }
  
  .send-btn:hover {
    opacity: 0.9
  }
  
  .panel {
    border-radius: 6px;
    margin-bottom: 0.5rem;
  }
  
  .explanation-container {
    max-width: 400px;
    word-wrap: break-word;
    line-height: 1.5;
  }
  
  .explanation-text {
    display: inline;
    margin-right: 5px;
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
    opacity: 0.9
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
  
  .ratio-menu {
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 1000;
    background: white;
    border-radius: 8px;
    padding: 4px 0;
    min-width: 60px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    border: 1px solid #e0e0e0;
    margin-top: 2px;
  }
  
  .ratio-item {
    list-style: none;
    padding: 6px 12px;
    font-size: 12px;
    cursor: pointer;
    color: #333;
  }
  
  .ratio-item:hover {
    background: #f0f0f0;
  }
  
  .ratio-item.active {
    color: #666;
    font-weight: 700;
    background: #f8f8f8;
  }
  
  .filter-list {
    list-style: none;
    padding: 0;
    margin-top: 1rem;
  }
  
  .filter-list li {
    padding: 0.5rem;
    margin: 0.25rem 0;
    background: #f5f5f5;
    border-radius: 4px;
    font-size: 0.9em;
  }
</style>
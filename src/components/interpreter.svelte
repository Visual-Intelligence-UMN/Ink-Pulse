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
    - Do NOT recompute statistics.
    - Do NOT invent numeric thresholds.
    - Treat all comparisons as RELATIVE (e.g., Human > AI).

    SYSTEM FEATURES

    You may ONLY reason about the following features:

    - source  
      (who is writing: human or AI, and in what order)

    - progress  
      (relative amount of writing contributed by each source)

    - semantic_change  
      (relative novelty of content, 0–1 scale)

    - time  
      (ordering of writing segments)

    OUTPUT A — Feature-Based Explanations

    Produce a list of explanations.

    Rules:
    - Each explanation MUST correspond to EXACTLY ONE feature
    - Each explanation must be independently removable
    - Do NOT combine multiple features in a single explanation
    - Use non-technical, user-facing language
    - Do NOT mention numbers, ranges, SQL, or filters

    Each explanation should describe:
    - What happened
    - Why this feature is relevant

    OUTPUT B — Searchable Feature Relations

    For each explanation in OUTPUT A, produce ONE corresponding searchable relation.

    Rules:
    - One relation per line
    - Each relation MUST map one-to-one to an explanation
    - Use relative comparisons only (>, <, =)
    - Use Human(...) and AI(...) for source-specific aggregation
    - Use trends/directions (increasing, decreasing, stable) to represent multi-block patterns

    Position information (NEW):
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
    - Do NOT use raw numbers or ranges
    - Do NOT invent new fields
    - Only use the system features: source, progress, semantic_change, time
    - The order of the JSON objects in FormattedFilter MUST match the order of Explanations
    - Output RAW JSON only
    - If a feature cannot be expressed as a searchable relation, do NOT include it
    - If no valid relations can be produced, return: "FormattedFilter": ["ERROR"]

    OUTPUT FORMAT:

    Return a JSON object with EXACTLY this structure:

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
          "relation": "<searchable relation>", 
          "span": "<prefix/suffix/full>",
          "l_position": "<first/last/prev>",
          "r_position": "<first/last/prev>"
        }
      ]
    }

    Examples:

    - AI writing + Human writing
    - Human(progress) > AI(progress), l_position: last, r_position: prev
    - Human(semantic_change) decreasing, span: prefix
    - Human(progress) increasing, span: full

    OUTPUT FORMAT

    Return a JSON object with EXACTLY this structure:

    {
      "Explanations": [
        {
          "feature": "<feature_name>",
          "text": "<user-friendly explanation>"
        }
      ],
      "FormattedFilter": [
        "<searchable relation matching explanation 1>",
        "<searchable relation matching explanation 2>"
      ]
    }

    CONSTRAINTS

    - The order of Explanations MUST match the order of FormattedFilter
    - If a feature cannot be expressed as a searchable relation, do NOT include it
    - If no valid relations can be produced, return:
      "FormattedFilter": ["ERROR"]
    - Output RAW JSON only.
    - Do NOT wrap the response in Markdown.
  `
  const featureStyleMap = {
    source: { color: '#2980b9', fontWeight: 'bold' },
    progress: { color: '#e67e22', fontWeight: 'bold' },
    semantic_change: { color: '#27ae60', fontWeight: 'bold' },
    time: { color: '#8e44ad', fontWeight: 'bold' }
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
    for (let i = 1; i < pattern.length; i++) {
      progressDiff.push(
        round2(pattern[i].endProgress - pattern[i - 1].endProgress)
      );
      timeDiff.push(
        round2(pattern[i].endTime - pattern[i - 1].endTime)
      );
      semanticDiff.push(
        round2(pattern[i].residual_vector_norm - pattern[i - 1].residual_vector_norm)
      );
    }

    return {
      sourceTrend,
      progressDiff,
      timeDiff,
      semanticDiff
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
      // console.log("Raw response:", raw);

      const parsed = JSON.parse(raw);
      console.log("Parsed response:", parsed);

      result = {
        explanations: parsed.Explanations || [],
        filters: parsed.FormattedFilter || []
      };

      sendParsedFiltersToParent();
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
    result.explanations.splice(index, 1);
    if (result.filters && result.filters.length > index) {
      result.filters.splice(index, 1);
    }
    result = { ...result };
    sendParsedFiltersToParent();
  }

  function parseFilterObject(filter) {
    if (!filter || !filter.relation) return null;

    const mainMatch = filter.relation.match(/^(\w+)\(([\w_]+)\)\s*(>|<|=)\s*(\w+)\(([\w_]+)\)/);
    if (!mainMatch) return null;

    return {
      l_source: mainMatch[1],
      l_feature: mainMatch[2],
      operator: mainMatch[3],
      r_source: mainMatch[4],
      r_feature: mainMatch[5],
      span: filter.span || null,
      l_position: filter.l_position || null,
      r_position: filter.r_position || null
    };
  }

  function parseAllFilters(filters) {
    return filters.map(parseFilterObject).filter(f => f !== null);
  }

  function sendParsedFiltersToParent() {
    const parsedFilters = parseAllFilters(result.filters);
    const explanations = result.explanations;
    dispatch('parsedFilters', { explanations, filters: parsedFilters });
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
        {#each result.explanations as exp, index (index)}
          <span
            class="explanation-text"
            style="color: {featureStyleMap[exp.feature]?.color}; font-weight: {featureStyleMap[exp.feature]?.fontWeight}"
          >
            {exp.text}<span class="close-button" on:click={() => removeExplanation(index)}>×</span>
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
</style>

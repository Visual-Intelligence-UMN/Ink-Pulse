<script>
  import { createEventDispatcher, onMount } from "svelte";
  import sourceColorManager from "./sourceColorManager.js";
  import "../components/styles.css";

  export let show = false;
  export let knownSources = [];

  const dispatch = createEventDispatcher();

  let sourceColors = {};
  let originalColors = {};

  $: if (show) {
    loadColors();
  }

  function loadColors() {
    sourceColors = {};
    knownSources.forEach((source) => {
      sourceColors[source] = sourceColorManager.getColor(source);
    });
    originalColors = { ...sourceColors };
  }

  function handleColorChange(source, event) {
    sourceColors[source] = event.target.value;
  }

  function handleSave() {
    // save all modified colors
    Object.entries(sourceColors).forEach(([source, color]) => {
      if (color !== originalColors[source]) {
        sourceColorManager.setCustomColor(source, color);
      }
    });
    dispatch("save");
    handleClose();
  }

  function handleReset(source) {
    sourceColorManager.resetColor(source);
    sourceColors[source] = sourceColorManager.getColor(source);
  }

  function handleResetAll() {
    sourceColorManager.resetAllColors();
    loadColors();
  }

  function handleClose() {
    dispatch("close");
    show = false;
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      handleClose();
    }
  }

  function handleKeydown(event) {
    if (event.key === "Escape") {
      handleClose();
    }
  }

  // format source name for display
  function formatSourceName(source) {
    const nameMap = {
      user: "Human",
      api: "AI",
    };
    return nameMap[source] || source.charAt(0).toUpperCase() + source.slice(1);
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show}
  <div class="dialog-backdrop" on:click={handleBackdropClick}>
    <div class="settings-container">
      <div class="settings-header">
        <h3 class="settings-title">Source Color Settings</h3>
        <button class="dialog-close" on:click={handleClose} aria-label="Close">
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M15 5L5 15M5 5L15 15"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>

      <div class="settings-content">
        <p class="settings-description">
          Customize colors for different data sources. Changes will be applied
          to all charts.
        </p>

        <div class="source-list">
          {#each knownSources as source (source)}
            <div class="source-item">
              <div class="source-info">
                <div class="source-name">{formatSourceName(source)}</div>
                <div class="source-id">({source})</div>
              </div>

              <div class="color-controls">
                <div
                  class="color-preview"
                  style="background-color: {sourceColors[source]}"
                ></div>
                <label class="color-input-wrapper">
                  <input
                    type="color"
                    value={sourceColors[source]}
                    on:input={(e) => handleColorChange(source, e)}
                    class="color-input"
                  />
                </label>
                <button
                  class="btn-reset-single"
                  on:click={() => handleReset(source)}
                  title="Reset to default color"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M3 8a5 5 0 0 1 9.9-1M13 8A5 5 0 0 1 3.1 9M13 3v4h-4M3 13V9h4"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </button>
              </div>
            </div>
          {/each}
        </div>

        {#if knownSources.length === 0}
          <div class="empty-state">
            <p>
              No data sources detected yet. Load some data to customize colors.
            </p>
          </div>
        {/if}
      </div>

      <div class="settings-actions">
        <button class="btn btn-secondary" on:click={handleResetAll}>
          Reset All
        </button>
        <div class="actions-right">
          <button class="btn btn-cancel" on:click={handleClose}>
            Cancel
          </button>
          <button class="btn btn-primary" on:click={handleSave}>
            Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .dialog-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease-out;
  }

  .settings-container {
    background: white;
    border-radius: 16px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    width: 100%;
    max-width: 600px;
    max-height: 80vh;
    margin: 16px;
    animation: slideIn 0.3s ease-out;
    border: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
  }

  .settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 24px 16px 24px;
    border-bottom: 1px solid #e5e7eb;
  }

  .settings-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #111827;
  }

  .dialog-close {
    background: none;
    border: none;
    padding: 8px;
    border-radius: 8px;
    cursor: pointer;
    color: #6b7280;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .dialog-close:hover {
    background: #f3f4f6;
    color: #374151;
  }

  .settings-content {
    padding: 24px;
    overflow-y: auto;
    flex: 1;
  }

  .settings-description {
    margin: 0 0 20px 0;
    font-size: 14px;
    line-height: 1.5;
    color: #6b7280;
  }

  .source-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .source-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    background: #f9fafb;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    transition: all 0.2s ease;
  }

  .source-item:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
  }

  .source-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .source-name {
    font-size: 16px;
    font-weight: 500;
    color: #111827;
  }

  .source-id {
    font-size: 12px;
    color: #6b7280;
    font-family: monospace;
  }

  .color-controls {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .color-preview {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    border: 2px solid #e5e7eb;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .color-input-wrapper {
    position: relative;
    width: 40px;
    height: 40px;
    cursor: pointer;
  }

  .color-input {
    position: absolute;
    width: 100%;
    height: 100%;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    opacity: 0;
  }

  .color-input-wrapper::before {
    content: "🎨";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 20px;
    pointer-events: none;
  }

  .btn-reset-single {
    background: none;
    border: 1px solid #d1d5db;
    padding: 8px;
    border-radius: 8px;
    cursor: pointer;
    color: #6b7280;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn-reset-single:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
    color: #374151;
  }

  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #6b7280;
    font-style: italic;
  }

  .settings-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid #e5e7eb;
  }

  .actions-right {
    display: flex;
    gap: 12px;
  }

  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-secondary {
    background: #f9fafb;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .btn-secondary:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  .btn-cancel {
    background: #f9fafb;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .btn-cancel:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  .btn-primary {
    background: #137a7f;
    color: white;
  }

  .btn-primary:hover {
    background: #0f6267;
    transform: translateY(-1px);
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-16px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @media (max-width: 640px) {
    .settings-container {
      margin: 16px;
      max-width: none;
    }

    .source-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }

    .color-controls {
      width: 100%;
      justify-content: flex-end;
    }

    .settings-actions {
      flex-direction: column;
    }

    .actions-right {
      width: 100%;
    }

    .btn {
      width: 100%;
    }
  }
</style>

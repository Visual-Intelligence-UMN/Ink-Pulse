<script>
  // Edit pattern dialog
  import { createEventDispatcher } from "svelte";

  export let show = false;
  export let pattern = null;

  // Type assertion to help TypeScript understand pattern structure
  $: currentPattern = pattern;

  const dispatch = createEventDispatcher();

  let inputValue = "";
  let inputElement;
  let isValid = true;
  let errorMessage = "";

  $: if (show && pattern && typeof pattern === "object" && "name" in pattern) {
    inputValue = pattern["name"] || "";
    // Focus the input when dialog opens
    setTimeout(() => {
      if (inputElement) {
        inputElement.focus();
        inputElement.select();
      }
    }, 100);
  }

  function validateInput(value) {
    if (!value || !value.trim()) {
      return { valid: false, message: "Pattern name cannot be empty" };
    }
    if (value.trim().length < 2) {
      return {
        valid: false,
        message: "Pattern name must be at least 2 characters long",
      };
    }
    if (value.trim().length > 50) {
      return {
        valid: false,
        message: "Pattern name must be less than 50 characters",
      };
    }
    return { valid: true, message: "" };
  }

  function handleInput() {
    const validation = validateInput(inputValue);
    isValid = validation.valid;
    errorMessage = validation.message;
  }

  function handleSave() {
    const validation = validateInput(inputValue);
    if (!validation.valid) {
      isValid = false;
      errorMessage = validation.message;
      return;
    }

    const trimmedValue = inputValue.trim();
    if (trimmedValue === pattern["name"]) {
      handleCancel(); // No changes, just close
      return;
    }

    dispatch("save", {
      pattern,
      newName: trimmedValue,
    });
    show = false;
  }

  function handleCancel() {
    dispatch("cancel");
    show = false;
    inputValue = "";
    isValid = true;
    errorMessage = "";
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      handleCancel();
    }
  }

  function handleKeydown(event) {
    if (event.key === "Escape") {
      handleCancel();
    } else if (event.key === "Enter") {
      event.preventDefault();
      handleSave();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show && pattern}
  <div class="dialog-backdrop" on:click={handleBackdropClick}>
    <div class="dialog-container">
      <div class="dialog-header">
        <h3 class="dialog-title">Edit Pattern Name</h3>
        <button class="dialog-close" on:click={handleCancel} aria-label="Close">
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

      <div class="dialog-content">
        <div class="dialog-icon">
          <svg
            width="48"
            height="48"
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx="24"
              cy="24"
              r="22"
              fill="#dbeafe"
              stroke="#60a5fa"
              stroke-width="2"
            />
            <path
              d="M18 24h12M18 18h12M18 30h8"
              stroke="#2563eb"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>

        <div class="form-group">
          <label for="pattern-name" class="form-label">Pattern Name</label>
          <input
            id="pattern-name"
            type="text"
            class="form-input"
            class:error={!isValid}
            bind:value={inputValue}
            bind:this={inputElement}
            on:input={handleInput}
            placeholder="Enter pattern name..."
            maxlength="50"
          />
          {#if !isValid && errorMessage}
            <div class="error-message">
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle
                  cx="8"
                  cy="8"
                  r="7"
                  fill="#fee2e2"
                  stroke="#fca5a5"
                  stroke-width="1"
                />
                <path
                  d="M8 4v4M8 10h.01"
                  stroke="#dc2626"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              {errorMessage}
            </div>
          {/if}
        </div>
      </div>

      <div class="dialog-actions">
        <button class="btn btn-secondary" on:click={handleCancel}>
          Cancel
        </button>
        <button
          class="btn btn-primary"
          on:click={handleSave}
          disabled={!isValid || !inputValue.trim()}
        >
          Save Changes
        </button>
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

  .dialog-container {
    background: white;
    border-radius: 16px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    width: 100%;
    max-width: 450px;
    margin: 16px;
    animation: slideIn 0.3s ease-out;
    border: 1px solid #e5e7eb;
  }

  .dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 24px 0 24px;
  }

  .dialog-title {
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

  .dialog-content {
    padding: 24px;
    text-align: center;
  }

  .dialog-icon {
    margin-bottom: 20px;
    display: flex;
    justify-content: center;
  }

  .form-group {
    margin-bottom: 16px;
    text-align: left;
  }

  .form-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: #374151;
    margin-bottom: 8px;
  }

  .form-input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #d1d5db;
    border-radius: 8px;
    font-size: 16px;
    transition: all 0.2s ease;
    box-sizing: border-box;
  }

  .form-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .form-input.error {
    border-color: #dc2626;
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
    font-size: 14px;
    color: #dc2626;
  }

  .dialog-actions {
    display: flex;
    gap: 12px;
    padding: 0 24px 24px 24px;
    justify-content: flex-end;
  }

  .btn {
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 100px;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }

  .btn-secondary {
    background: #f9fafb;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  .btn-primary {
    background: #3b82f6;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #2563eb;
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

  /* Responsive design */
  @media (max-width: 640px) {
    .dialog-container {
      margin: 16px;
      max-width: none;
    }

    .dialog-actions {
      flex-direction: column-reverse;
    }

    .btn {
      width: 100%;
    }
  }
</style>

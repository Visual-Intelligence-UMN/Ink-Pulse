<script>
  // Delete pattern dialog
  import { createEventDispatcher } from "svelte";

  export let show = false;
  export let title = "Confirm Action";
  export let message = "Are you sure you want to proceed?";
  export let confirmText = "OK";
  export let cancelText = "Cancel";
  export let variant = "danger"; // 'danger', 'warning', 'info'

  const dispatch = createEventDispatcher();

  function handleConfirm() {
    dispatch("confirm");
    show = false;
  }

  function handleCancel() {
    dispatch("cancel");
    show = false;
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
      handleConfirm();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show}
  <div class="dialog-backdrop" on:click={handleBackdropClick}>
    <div
      class="dialog-container"
      class:danger={variant === "danger"}
      class:warning={variant === "warning"}
      class:info={variant === "info"}
    >
      <div class="dialog-header">
        <h3 class="dialog-title">{title}</h3>
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
          {#if variant === "danger"}
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
                fill="#fee2e2"
                stroke="#fca5a5"
                stroke-width="2"
              />
              <path
                d="M24 14v12M24 30h.01"
                stroke="#dc2626"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          {:else if variant === "warning"}
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
                fill="#fef3cd"
                stroke="#fbbf24"
                stroke-width="2"
              />
              <path
                d="M24 14v12M24 30h.01"
                stroke="#d97706"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          {:else}
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
                d="M24 14v12M24 30h.01"
                stroke="#2563eb"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          {/if}
        </div>

        <p class="dialog-message">{message}</p>
      </div>

      <div class="dialog-actions">
        <button class="btn btn-secondary" on:click={handleCancel}>
          {cancelText}
        </button>
        <button
          class="btn btn-primary"
          class:btn-danger={variant === "danger"}
          on:click={handleConfirm}
        >
          {confirmText}
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
    max-width: 400px;
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
    margin-bottom: 16px;
    display: flex;
    justify-content: center;
  }

  .dialog-message {
    margin: 0;
    font-size: 16px;
    line-height: 1.5;
    color: #4b5563;
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
    min-width: 80px;
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

  .btn-primary {
    background: #3b82f6;
    color: white;
  }

  .btn-primary:hover {
    background: #2563eb;
    transform: translateY(-1px);
  }

  .btn-danger {
    background: #dc2626;
    color: white;
  }

  .btn-danger:hover {
    background: #b91c1c;
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

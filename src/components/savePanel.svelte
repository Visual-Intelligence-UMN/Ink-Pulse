<script>
  import { createEventDispatcher } from "svelte";
  import "../components/styles.css";

  export let name = "";
  export let color = "#66ccff";

  const dispatch = createEventDispatcher();
  let nameInput = name;
  let colorInput = color;

  function save() {
    dispatch("save", {
      name: nameInput || "Default",
      color: colorInput,
    });
  }

  function close() {
    dispatch("close");
  }
</script>

<div class="save-panel">
  <div class="save-panel-content">
    <h3 style="text-align: center;">Save Pattern</h3>
    <div style="display: flex; flex-direction: column; gap: 1rem;">
      <label>
        Pattern Name:
        <input type="text" bind:value={nameInput} placeholder="Name" />
      </label>
      <div style="display: flex; align-items: center; gap: 1rem;">
        <span>Color:</span>
        <label class="color-wrapper">
          <div
            class="color-circle"
            style="background-color: {colorInput}"
          ></div>
          <input type="color" bind:value={colorInput} class="color-overlay" />
        </label>
      </div>
    </div>
    <div style="text-align: center;">
      <button class="search-pattern-button" on:click={save}>Save</button>
      <button class="delete-pattern-button" on:click={close}>Exit</button>
    </div>
  </div>
</div>

<style>
  .save-panel {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.3);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 700;
  }

  .save-panel-content {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    min-width: 300px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    z-index: 700;
  }

  .color-wrapper {
    position: relative;
    width: 20px;
    height: 20px;
  }

  .color-circle {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    box-shadow: 0 0 2px rgba(0, 0, 0, 0.3);
  }

  .color-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    opacity: 0;
    cursor: pointer;
  }
</style>

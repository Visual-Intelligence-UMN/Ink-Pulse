<script>
  import { createEventDispatcher } from "svelte";
  import "../components/styles.css";
  import RangeSlider from 'svelte-range-slider-pips';

  export let weights;

  const dispatch = createEventDispatcher();

  // 每个 slider 的独立变量
  let s = 0, t = 0, p = 0, tr = 0, sem = 0;
  let initialized = false;

  // 初始化：只做一次
  $: if (!initialized && $weights) {
    s = $weights.s ?? 0;
    t = $weights.t ?? 0;
    p = $weights.p ?? 0;
    tr = $weights.tr ?? 0;
    sem = $weights.sem ?? 0;
    initialized = true;
  }

  const min = -5;
  const max = 5;
  const step = 0.01;

  function save() {
    const newWeights = { s, t, p, tr, sem };
    weights.set(newWeights);
    dispatch("save", { weights: newWeights });
  }

  function close() {
    dispatch("close");
  }
</script>

<div class="panel">
  <div class="panel-content">
    <h3 style="text-align: center;">Weights</h3>
    <div style="display: flex; flex-direction: column; gap: 1rem;">
      
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
        <label>Source:</label>
        <RangeSlider bind:value={s} min={min} max={max} step={step} float />
      </div>

      <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
        <label>Time:</label>
        <RangeSlider bind:value={t} min={min * 0.01} max={max * 0.01} step={step * 0.1} precision={4} float />
      </div>

      <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
        <label>Progress:</label>
        <RangeSlider bind:value={p} min={min} max={max} step={step} float />
      </div>

      <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
        <label>Trend:</label>
        <RangeSlider bind:value={tr} min={min} max={max} step={step} float />
      </div>

      <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
        <label>Semantic Score:</label>
        <RangeSlider bind:value={sem} min={min} max={max} step={step} float />
      </div>

      <div style="text-align: center;">
        <button class="search-pattern-button" on:click={save}>Save</button>
        <button class="delete-pattern-button" on:click={close}>Exit</button>
      </div>
    </div>
  </div>
</div>

<style>
  .panel {
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

  .panel-content {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    min-width: 100px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    z-index: 700;
  }
</style>

<script lang="ts">
  import { onMount, onDestroy, afterUpdate } from "svelte";
  import { createEventDispatcher } from "svelte";
  import * as d3 from "d3";
  import sourceColorManager from "./sourceColorManager.js";

  const dispatch = createEventDispatcher();

  export let similarityData;
  export let sessionId;
  export let highlightPatterns: number[] | null = null; // NEW

  // NEW: explicit opacity maps
  const opacitySettings = {
    settings_1: { 0: 0.3, 1: 1 },
    settings_2: { 0: 0.3, 1: 0.5, 2: 1 },
    settings_3: {
      0: 0.1,
      1: 0.3,
      2: 0.7,
      3: 1,
      4: 1,
      5: 1,
      6: 1,
      7: 1,
      8: 1,
      9: 1,
      10: 1,
    },
  };

  let showPrompt = true;
  let height = 20;

  let canvasEl: HTMLCanvasElement;
  let context: CanvasRenderingContext2D | null = null;

  let observer: IntersectionObserver;
  let isVisible = false;

  function handleContainerClick() {
    dispatch("containerClick", { sessionId });
  }

  function renderCanvas() {
    if (!similarityData || !canvasEl || !isVisible) return;

    const processedData = similarityData.map((item) => ({
      text_length: item.sentence,
      startProgress: item.start_progress * 100,
      endProgress: item.end_progress * 100,
      residual_vector_norm: item.residual_vector_norm ?? 0,
      source: item.source,
    }));

    const textLength =
      processedData[processedData.length - 1]?.text_length || 1;
    const width = 100 * textLength;

    const xScale = d3.scaleLinear().domain([0, 100]).range([0, width]);
    const yScale = d3.scaleLinear().domain([0, 1]).range([0, height]);
    const opacityScale = d3.scaleLinear().domain([0, 1]).range([0.3, 1]);

    const dpr = 5;
    canvasEl.width = width * dpr;
    canvasEl.height = height * dpr;
    canvasEl.style.width = width + "px";
    canvasEl.style.height = height + "px";

    context = canvasEl.getContext("2d");
    if (!context) return;

    context.setTransform(1, 0, 0, 1, 0, 0);
    context.scale(dpr, dpr);
    context.clearRect(0, 0, canvasEl.width, canvasEl.height);

    // --- NEW: decide which settings to use if highlightPatterns is present ---
    let opacityMap: Record<number, number> | null = null;
    if (highlightPatterns) {
      const maxVal = Math.max(...highlightPatterns);
      if (maxVal <= 1) opacityMap = opacitySettings.settings_1;
      else if (maxVal === 2) opacityMap = opacitySettings.settings_2;
      else opacityMap = opacitySettings.settings_3;
    }

    for (let i = 0; i < processedData.length; i++) {
      const d = processedData[i];
      const isFirst = i === 0;
      const hideFirst = isFirst && !showPrompt;
      const barY = yScale(hideFirst ? 0 : 1);
      const barHeight =
        yScale(0) - yScale(hideFirst ? 0 : d.residual_vector_norm);
      const barX = xScale(d.startProgress);
      const barWidth = xScale(d.endProgress) - barX;

      context.fillStyle = sourceColorManager.getColor(d.source);

      if (opacityMap) {
        // NEW: use highlightPatterns to set opacity
        const level = highlightPatterns[i] ?? 0;
        context.globalAlpha = opacityMap[level] ?? 1;
      } else {
        // default behavior
        context.globalAlpha = opacityScale(d.residual_vector_norm);
      }

      context.fillRect(barX, barY, barWidth, barHeight);
      context.strokeStyle = context.fillStyle;
      context.lineWidth = 0.1;
      context.strokeRect(barX, barY, barWidth, barHeight);
    }

    context.globalAlpha = 1;
  }

  function setupObserver() {
    observer = new IntersectionObserver(
      ([entry]) => {
        isVisible = entry.isIntersecting;
        if (isVisible) renderCanvas();
      },
      { threshold: 0.1 }
    );
    if (canvasEl) observer.observe(canvasEl);
  }

  onMount(setupObserver);
  afterUpdate(() => {
    if (isVisible) renderCanvas();
  });
  onDestroy(() => {
    if (observer && canvasEl) observer.unobserve(canvasEl);
  });
</script>

<div class="chart-container" on:click={handleContainerClick}>
  <div style="margin-top: 30px">
    <canvas bind:this={canvasEl} data-session-id={sessionId}></canvas>
  </div>
</div>

<style>
  .chart-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    cursor: pointer;
    width: 150px;
    height: 10px;
  }
</style>

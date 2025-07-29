<script lang="ts">
  import { onMount, onDestroy, afterUpdate } from "svelte";
  import { createEventDispatcher } from "svelte";
  import * as d3 from "d3";

  const dispatch = createEventDispatcher();

  export let similarityData;
  export let sessionId;

  let showPrompt = true;
  let height = 20;

  let canvasEl: HTMLCanvasElement;
  let context: CanvasRenderingContext2D | null = null;

  let observer: IntersectionObserver;
  let isVisible = false;
  let lastDataHash = "";

  function handleContainerClick() {
    dispatch("containerClick", { sessionId });
  }

  function hashData(data) {
    try {
      return JSON.stringify(data);
    } catch {
      return "";
    }
  }

  function renderCanvas() {
    if (!similarityData || !canvasEl || !isVisible) return;

    const dataHash = hashData(similarityData);
    if (dataHash === lastDataHash) return;
    lastDataHash = dataHash;

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

    for (const d of processedData) {
      const isFirst = processedData.indexOf(d) === 0;
      const hideFirst = isFirst && !showPrompt;
      const barY = yScale(hideFirst ? 0 : 1);
      const barHeight = yScale(0) - yScale(hideFirst ? 0 : d.residual_vector_norm);
      const barX = xScale(d.startProgress);
      const barWidth = xScale(d.endProgress) - barX;

      context.fillStyle = d.source === "user" ? "#66C2A5" : "#FC8D62";
      context.globalAlpha = opacityScale(d.residual_vector_norm);
      if (isFirst) {
        context.fillStyle = "#e8e8e8";
        context.globalAlpha = 1; 
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
      { threshold: 0.1 },
    );

    if (canvasEl) observer.observe(canvasEl);
  }

  onMount(() => {
    setupObserver();
  });

  afterUpdate(() => {
    if (isVisible) renderCanvas();
  });

  onDestroy(() => {
    if (observer && canvasEl) {
      observer.unobserve(canvasEl);
    }
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

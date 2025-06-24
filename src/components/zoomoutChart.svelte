<script lang="ts">
  import { onMount, createEventDispatcher } from "svelte";
  import * as d3 from "d3";

  const dispatch = createEventDispatcher();
  
  export let similarityData;
  let height = 10;
  const margin = { top: 0, right: 0, bottom: 0, left: 0 };

  let canvasEl;
  let context: CanvasRenderingContext2D;

  export let sessionId;
  export let sessionTopic;

  function handleContainerClick() {
    dispatch('containerClick', { sessionId });
  }

  function renderCanvas() {
    if (!similarityData || !canvasEl) return;

    const processedData = similarityData.map((item) => ({
      text: item.sentence,
      startProgress: item.start_progress * 100,
      endProgress: item.end_progress * 100,
      residual_vector_norm: item.residual_vector_norm,
      source: item.source,
    }));
    const textLength = processedData[processedData.length - 1]["text"].length / 3000;
    let width = 100 * textLength;
    
    const xScale = d3
      .scaleLinear()
      .domain([0, 100])
      .range([0, width - margin.left - margin.right]);
    const yScale = d3.scaleLinear().domain([1, 0]).range([0, height]);
    const opacityScale = d3.scaleLinear().domain([0, 1]).range([0.3, 1]);

    const canvas = canvasEl;
    context = canvas.getContext("2d");

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    context.setTransform(dpr, 0, 0, dpr, 0, 0);

    context.clearRect(0, 0, width, height);

    for (let i = 0; i < processedData.length; i++) {
      const d = processedData[i];
      const isFirst = i === 0;
      const barY = yScale(isFirst ? 0 : 1);
      const barHeight = yScale(0) - yScale(isFirst ? 0 : 1);
      const barX = xScale(d.startProgress);
      const barWidth = xScale(d.endProgress) - barX;

      context.fillStyle = d.source === "user" ? "#66C2A5" : "#FC8D62";
      context.globalAlpha = opacityScale(d.residual_vector_norm);
      context.fillRect(barX, barY, barWidth, barHeight);
      context.strokeStyle = d.source === "user" ? "#66C2A5" : "#FC8D62";
      context.lineWidth = 0.1;
      context.strokeRect(barX, barY, barWidth, barHeight);
    }

    context.globalAlpha = 1;
  }

  onMount(() => {
    renderCanvas();
  });
</script>

<div class="chart-container" on:click={handleContainerClick}>
  <!-- <div class="session-label">{sessionTopic} - {sessionId.slice(0, 4)}</div> -->
  <div style="margin-top: 30px">
    <canvas bind:this={canvasEl} data-session-id={sessionId}></canvas>
  </div>
</div>

<style>
  .session-label {
    width: 350px;
    font-size: 12px;
    font-family: "Poppins", sans-serif;
    margin-top: 35px;
  }

  .chart-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    cursor: pointer;
    width: 150px;
    height: 10px;
  }
</style>
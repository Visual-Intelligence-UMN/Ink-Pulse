<script lang="ts">
  import { onMount } from "svelte";

  export let percentageSummaryData;
  export let percentageData;
  export let patternSessions;
  export let flag;
  export let title;

  const NOWColor = '#015dc6';
  const overallColor = '#bf1818';

  let canvasEl: HTMLCanvasElement;

  function drawChart() {
    if (!canvasEl) return;
    const dpr = 3;

    const width = 300;
    const height = 200;

    canvasEl.width = width * dpr;
    canvasEl.height = height * dpr;
    canvasEl.style.width = width + "px";
    canvasEl.style.height = height + "px";

    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const paddingTop = 20;
    const paddingBottom = 40;
    const paddingLeft = 50;
    const tickLength = 6;
    const ySteps = 5;
    const maxStart = 100;
    const step = 10;
    const binCount = maxStart / step;

    const labels = Array.from({ length: binCount }, (_, i) => `${i * step}-${(i + 1) * step}`);
    const overallCounts = new Array(binCount).fill(0);
    const highlightCounts = new Array(binCount).fill(0);
    if (flag === "overall") {
      const tempCounts = Object.values(percentageSummaryData).map(Number);
      for (let i = 0; i < Math.min(tempCounts.length, binCount); i++) {
        overallCounts[i] = tempCounts[i];
      }
    } else {
      const aiRatioMap = new Map(percentageData.map(([id, ai]) => [id, ai]));
      const processedSessionIds = new Set<string>();
      percentageSummaryData.forEach((session) => {
        if (processedSessionIds.has(session.sessionId)) return;
        processedSessionIds.add(session.sessionId);

        const aiRatio = aiRatioMap.get(session.sessionId);
        if (typeof aiRatio !== 'number') return;

        const binIndex = Math.min(Math.floor(aiRatio * 10), binCount - 1);
        overallCounts[binIndex]++;
      });
    }

    const aiRatioMap = new Map(percentageData.map(([id, ai]) => [id, ai]));
    const processedSessionIds = new Set<string>();

    patternSessions.forEach((session) => {
      if (processedSessionIds.has(session.sessionId)) return;
      processedSessionIds.add(session.sessionId);

      const aiRatio = aiRatioMap.get(session.sessionId);
      if (typeof aiRatio !== 'number') return;

      const binIndex = Math.min(Math.floor(aiRatio * 10), binCount - 1);
      highlightCounts[binIndex]++;
    });

    ctx.clearRect(0, 0, width, height);
    const barWidth = (width - paddingLeft) / binCount;
    ctx.strokeStyle = "#000";
    ctx.fillStyle = "#000";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      const percent = (i * 100 / ySteps).toFixed(0) + "%";
      ctx.beginPath();
      ctx.moveTo(paddingLeft - tickLength, y);
      ctx.lineTo(paddingLeft, y);
      ctx.stroke();
      ctx.fillText(percent, paddingLeft - tickLength - 5, y);
    }

    ctx.beginPath();
    ctx.moveTo(paddingLeft, paddingTop);
    ctx.lineTo(paddingLeft, height - paddingBottom);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(width, height - paddingBottom);
    ctx.stroke();

    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.font = "7px sans-serif";

    for (let i = 0; i < binCount; i++) {
      const x = paddingLeft + i * barWidth + barWidth / 2;
      ctx.beginPath();
      ctx.moveTo(x, height - paddingBottom);
      ctx.lineTo(x, height - paddingBottom + tickLength);
      ctx.stroke();

      ctx.fillText(labels[i], x, height - paddingBottom + tickLength + 3);
    }

    ctx.font = "10px sans-serif";
    ctx.fillText("AI Ratio", paddingLeft + (width - paddingLeft) / 2, height - paddingBottom + tickLength + 20);

    const highlightTotal = patternSessions.length;
    for (let i = 0; i < binCount; i++) {
      if (highlightCounts[i] === 0) continue;
      const freq = highlightCounts[i] / highlightTotal;
      const barHeight = freq * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + barWidth * 0.25;
      const y = height - paddingBottom - barHeight;

      ctx.fillStyle = NOWColor;
      ctx.fillRect(x, y, barWidth * 0.3, barHeight);
    }

    const overallTotal = overallCounts.reduce((a, b) => a + b, 0);
    for (let i = 0; i < binCount; i++) {
      if (overallCounts[i] === 0) continue;
      const freq = overallCounts[i] / overallTotal;
      const barHeight = freq * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + barWidth * 0.55;
      const y = height - paddingBottom - barHeight;

      ctx.fillStyle = overallColor;
      ctx.fillRect(x, y, barWidth * 0.3, barHeight);
    }

    const legendX = width - 10;
    const legendY = 15;
    const legendBoxSize = 12;
    const legendSpacing = 5;
    ctx.font = "12px sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    ctx.fillStyle = NOWColor;
    ctx.fillRect(legendX - legendBoxSize, legendY, legendBoxSize, legendBoxSize);
    ctx.fillStyle = "#000";
    ctx.fillText(title[0], legendX - legendBoxSize - legendSpacing, legendY + legendBoxSize / 2);
    ctx.fillStyle = overallColor;
    ctx.fillRect(legendX - legendBoxSize, legendY + legendBoxSize + legendSpacing, legendBoxSize, legendBoxSize);
    ctx.fillStyle = "#000";
    ctx.fillText(title[1], legendX - legendBoxSize - legendSpacing, legendY + legendBoxSize + legendSpacing + legendBoxSize / 2);
  }


  onMount(() => {
    drawChart();
  });

  $: if (percentageSummaryData && percentageData && patternSessions) {
    drawChart();
  }
</script>

<canvas bind:this={canvasEl} />

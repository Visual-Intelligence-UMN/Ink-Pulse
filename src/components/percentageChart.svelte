<script lang="ts">
  import { onMount } from "svelte";

  export let percentageSummaryData;
  export let percentageData;
  export let patternSessions;

  const overallColor = '#015dc6';
  const NOWColor = "#bf1818";

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

    const labels = Object.keys(percentageSummaryData);
    const counts = Object.values(percentageSummaryData).map(Number);
    const totalCount = counts.reduce((a, b) => a + b, 0);

    const paddingTop = 20;
    const paddingBottom = 40;
    const paddingLeft = 50;
    const tickLength = 6;

    ctx.clearRect(0, 0, width, height);

    const barWidth = (width - paddingLeft) / labels.length;

    ctx.strokeStyle = "#000";
    ctx.fillStyle = "#000";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
        const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
        const percent = (i * 100 / ySteps).toFixed(0) + "%";

        ctx.beginPath();
        ctx.moveTo(paddingLeft - tickLength, y);
        ctx.lineTo(paddingLeft, y);
        ctx.stroke();

        ctx.fillText(percent, paddingLeft - tickLength - 5, y);
    }

    ctx.strokeStyle = "#000";
    ctx.lineWidth = 1;
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
    const maxStart = 100;
    const step = 10;
    const maxIndex = Math.floor(maxStart / step);

    for (let i = 0; i < labels.length && i < maxIndex; i++) {
        const x = paddingLeft + i * barWidth + barWidth / 2;
        ctx.beginPath();
        ctx.moveTo(x, height - paddingBottom);
        ctx.lineTo(x, height - paddingBottom + tickLength);
        ctx.stroke();

        ctx.font = "7px sans-serif";

        const start = i * step;
        let end = start + step;
        if (end > maxStart) end = maxStart;

        const labelText = `${start}-${end}`;

        ctx.fillText(labelText, x, height - paddingBottom + tickLength + 3);
    }
    ctx.font = "10px sans-serif";
    ctx.save();
    ctx.restore();
    const xAxisLabel = "AI Ratio";
    ctx.fillText(xAxisLabel, paddingLeft + (width - paddingLeft) / 2, height - paddingBottom + tickLength + 20);

    counts.forEach((count, i) => {
      const freq = count / totalCount;
      const barHeight = freq * (height - paddingBottom - paddingTop);
      const x = paddingLeft + i * barWidth + barWidth * 0.15;
      const y = height - paddingBottom - barHeight;

      ctx.fillStyle = overallColor;
      ctx.fillRect(x, y, barWidth * 0.3, barHeight);
    });

    const aiRatioMap = new Map(percentageData.map(([id, ai]) => [id, ai]));
    const processedSessionIds = new Set<string>();
    const highlightCounts = new Array(labels.length).fill(0);

    patternSessions.forEach((session) => {
      if (processedSessionIds.has(session.sessionId)) return;
      processedSessionIds.add(session.sessionId);

      const aiRatio = aiRatioMap.get(session.sessionId) as number;
      if (aiRatio === undefined) return;

      const binIndex = Math.min(Math.floor(aiRatio * 10), labels.length - 1);
      highlightCounts[binIndex]++;
    });

    highlightCounts.forEach((count, i) => {
      if (count === 0) return;

      const freq = count / patternSessions.length;
      const barHeight = freq * (height - paddingBottom - paddingTop);
      const x = paddingLeft + i * barWidth + barWidth * 0.55;
      const y = height - paddingBottom - barHeight;

      ctx.fillStyle = NOWColor;
      ctx.fillRect(x, y, barWidth * 0.3, barHeight);
    });
  }

  onMount(() => {
    drawChart();
  });

  $: if (percentageSummaryData && percentageData && patternSessions) {
    drawChart();
  }
</script>

<canvas bind:this={canvasEl} />

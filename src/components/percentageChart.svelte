<script lang="ts">
  import { onMount } from "svelte";
  import jStat from 'jstat';

  export let percentageSummaryData;
  export let percentageData;
  export let patternSessions;
  export let flag;
  export let title;

  const NOWColor = '#999999';
  const overallColor = '#ffffff';

  let canvasEl: HTMLCanvasElement;

  function drawChart() {
    if (!canvasEl) return;
    const dpr = 2;
    const width = 200;
    const height = 175;

    canvasEl.width = width * dpr;
    canvasEl.height = height * dpr;
    canvasEl.style.width = width + "px";
    canvasEl.style.height = height + "px";

    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const paddingTop = 40;
    const paddingBottom = 45;
    const paddingLeft = 50;
    const tickLength = 3;
    const ySteps = 5;
    const maxStart = 100;
    const step = 10;
    const binCount = maxStart / step;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(paddingLeft, 0, width - paddingLeft, height - paddingBottom);
    ctx.strokeStyle = "#ccc";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(paddingLeft, 0);
    ctx.lineTo(width, 0);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(width, 0);
    ctx.lineTo(width, height - paddingBottom);
    ctx.stroke();

    function getAdjustedOverallCounts(percentageData, patternSessions) {
      const removedIds = new Set(patternSessions.map(s => s.sessionId));
      const processedIds = new Set<string>();
      const counts = new Array(binCount).fill(0);
      const values: number[] = [];

      percentageData.forEach(([id, ai]) => {
        if (removedIds.has(id)) return;
        if (processedIds.has(id)) return;
        processedIds.add(id);

        if (typeof ai !== "number") return;

        const binIndex = Math.min(Math.floor(ai * 10), binCount - 1);
        counts[binIndex]++;
        values.push(ai * 100);
      });

      return { counts, values };
    }

    const labels = Array.from({ length: binCount }, (_, i) => `${i * step}-${(i + 1) * step}`);
    const overallCounts = new Array(binCount).fill(0);
    const highlightCounts = new Array(binCount).fill(0);
    let overallValues: number[] = [];
    let highlightValues: number[] = [];

    if (flag === "overall") {
      const { counts, values } = getAdjustedOverallCounts(percentageData, patternSessions);
      overallValues = values;
      for (let i = 0; i < Math.min(counts.length, binCount); i++) overallCounts[i] = counts[i];
    } else {
      const aiRatioMap = new Map(percentageData.map(([id, ai]) => [id, ai]));
      const processedSessionIds = new Set<string>();
      const values: number[] = [];

      percentageSummaryData.forEach((session) => {
        if (processedSessionIds.has(session.sessionId)) return;
        processedSessionIds.add(session.sessionId);

        const aiRatio = aiRatioMap.get(session.sessionId);
        if (typeof aiRatio !== 'number') return;

        const binIndex = Math.min(Math.floor(aiRatio * 10), binCount - 1);
        overallCounts[binIndex]++;
        values.push(aiRatio * 100);
      });

      overallValues = values;
    }

    const aiRatioMap = new Map(percentageData.map(([id, ai]) => [id, ai]));
    const processedSessionIds = new Set<string>();
    const highlightValuesTmp: number[] = [];

    patternSessions.forEach((session) => {
      if (processedSessionIds.has(session.sessionId)) return;
      processedSessionIds.add(session.sessionId);
      const aiRatio = aiRatioMap.get(session.sessionId);
      if (typeof aiRatio !== 'number') return;
      const binIndex = Math.min(Math.floor(aiRatio * 10), binCount - 1);
      highlightCounts[binIndex]++;
      highlightValuesTmp.push(aiRatio * 100);
    });
    highlightValues = highlightValuesTmp;

    ctx.strokeStyle = "#999999";
    ctx.lineWidth = 0.5;
    const barWidth = (width - paddingLeft) / binCount;

    ctx.font = "10px sans-serif";
    ctx.fillStyle = "#000";
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

    ctx.font = "7px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let i = 0; i < binCount; i++) {
      const x = paddingLeft + i * barWidth + barWidth / 2;
      const textY = height - paddingBottom + tickLength + 3;
      const angle = -Math.PI / 4;
      ctx.save();
      ctx.translate(x, textY);
      ctx.rotate(angle);
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(labels[i], 0, 0);
      ctx.restore();
    }

    ctx.font = "10px sans-serif";
    ctx.fillText("AI Ratio(%)", paddingLeft + (width - paddingLeft) / 2, height - paddingBottom + tickLength + 20);

    const bw = 0.4;
    const highlightOffset = (barWidth - 2 * barWidth * bw) / 2;
    const overallOffset = highlightOffset + barWidth * bw;

    const highlightTotal = highlightValues.length;
    for (let i = 0; i < binCount; i++) {
      if (highlightCounts[i] === 0) continue;
      const freq = highlightCounts[i] / highlightTotal;
      const barHeight = freq * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + highlightOffset;
      const y = height - paddingBottom - barHeight;
      ctx.fillStyle = NOWColor;
      ctx.fillRect(x, y, barWidth * bw, barHeight);
      ctx.strokeStyle = NOWColor;
      ctx.lineWidth = 0.3;
      ctx.strokeRect(x, y, barWidth * bw, barHeight);
    }

    function createStripedPattern(ctx, color = NOWColor) {
      const size = 8;
      const patternCanvas = document.createElement('canvas');
      patternCanvas.width = size;
      patternCanvas.height = size;
      const pctx = patternCanvas.getContext('2d');
      if (!pctx) return null;
      pctx.strokeStyle = color;
      pctx.lineWidth = 1;
      pctx.beginPath();
      pctx.moveTo(0, size);
      pctx.lineTo(size, 0);
      pctx.stroke();
      return ctx.createPattern(patternCanvas, 'repeat');
    }

    const overallTotal = overallValues.length;
    for (let i = 0; i < binCount; i++) {
      if (overallCounts[i] === 0) continue;
      const freq = overallCounts[i] / overallTotal;
      const barHeight = freq * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + overallOffset;
      const y = height - paddingBottom - barHeight;
      ctx.fillStyle = createStripedPattern(ctx);;
      ctx.fillRect(x, y, barWidth * bw, barHeight);
      ctx.strokeStyle = NOWColor;
      ctx.lineWidth = 0.3;
      ctx.strokeRect(x, y, barWidth * bw, barHeight);
    }

    const overallMean = overallValues.reduce((a, b) => a + b, 0) / overallValues.length;
    const highlightMean = highlightValues.reduce((a, b) => a + b, 0) / highlightValues.length;

    let pValue = null;
    if (overallValues.length > 1 && highlightValues.length > 1) {
      const mean1 = jStat.mean(overallValues);
      const mean2 = jStat.mean(highlightValues);
      const var1 = jStat.variance(overallValues, true);
      const var2 = jStat.variance(highlightValues, true);
      const n1 = overallValues.length;
      const n2 = highlightValues.length;

      const t = (mean1 - mean2) / Math.sqrt(var1 / n1 + var2 / n2);
      const df = Math.pow(var1 / n1 + var2 / n2, 2) /
                ((Math.pow(var1 / n1, 2) / (n1 - 1)) + (Math.pow(var2 / n2, 2) / (n2 - 1)));

      pValue = 2 * (1 - jStat.studentt.cdf(Math.abs(t), df));
    }


    const legendY = 15;
    let displayP;
    if (pValue !== null) {
      ctx.fillStyle = "#000";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      if (pValue < 1e-16) {
        displayP = "p<1e-16";
      } else {
        displayP = `p=${pValue.toExponential(2)}`;
      }
      ctx.fillText(displayP, width - 140, legendY + 30);
    }

    const topContainerHeight = paddingTop;
    ctx.fillStyle = "#f5f5f5";
    ctx.fillRect(500, 0, width - paddingLeft, topContainerHeight);

    function drawStdErrorBar(ctx, values, color, y) {
      if (!values || values.length < 3) return;

      const mean = jStat.mean(values);
      const stdDev = jStat.stdev(values);

      const meanX = paddingLeft + (mean / 100) * (width - paddingLeft);

      const stdDevPx = (stdDev / 100) * (width - paddingLeft);

      ctx.strokeStyle = color;
      ctx.lineWidth = 1;

      ctx.beginPath();
      ctx.moveTo(meanX - stdDevPx, y);
      ctx.lineTo(meanX + stdDevPx, y);
      ctx.stroke();

      const errorBarHeight = 3;
      ctx.beginPath();
      ctx.moveTo(meanX - stdDevPx, y - errorBarHeight);
      ctx.lineTo(meanX - stdDevPx, y + errorBarHeight);
      ctx.moveTo(meanX + stdDevPx, y - errorBarHeight);
      ctx.lineTo(meanX + stdDevPx, y + errorBarHeight);
      ctx.stroke();

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(meanX, y, 2.5, 0, 2 * Math.PI);
      ctx.fill();

      return meanX;
    }

    const overallMeanX = drawStdErrorBar(ctx, overallValues, "#666", topContainerHeight - 5);
    const highlightMeanX = drawStdErrorBar(ctx, highlightValues, "#000", topContainerHeight - 25);
    ctx.strokeStyle = "#ccc";
    ctx.lineWidth = 1;
    ctx.strokeRect(paddingLeft, 0, width - paddingLeft, topContainerHeight);
    ctx.fillStyle = "#000";
    ctx.textBaseline = "top";
    ctx.textAlign = "left";
    ctx.fillText(`avg(${title[0]})=${highlightMean.toFixed(2)}`, highlightMeanX / 2, 0);
    ctx.fillStyle = "#666";
    ctx.fillText(`avg(${title[1]})=${overallMean.toFixed(2)}`, overallMeanX / 2, 20);
  }

  onMount(() => {
    drawChart();
  });

  $: if (percentageSummaryData && percentageData && patternSessions) {
    drawChart();
  }
</script>

<canvas bind:this={canvasEl} style="margin-top: 20px;"/>

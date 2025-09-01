<script>
  import { onMount } from 'svelte';
  import jStat from 'jstat';

  let canvas;

  export let rawData;
  export let nowData;
  export let title;
  export let flag;

  const width = 200;
  const height = 175;
  const paddingLeft = 50;
  const paddingBottom = 40;
  const paddingTop = 20;
  const NOWColor = '#999999';
  const dpr = 2;

  let labels = [];
  let rawBarHeights = [];
  let nowBarHeights = [];

  function meanFromCounts(data) {
    let sum = 0;
    let total = 0;
    for (const [scoreStr, count] of Object.entries(data)) {
      const score = Number(scoreStr);
      sum += score * count;
      total += count;
    }
    return total > 0 ? sum / total : 0;
  }

  function drawMeanLine(ctx, mean, color, label, labels, barHeights, offset = 3, side = "center") {
    if (!labels.length) return;

    let closestIndex = 0;
    let minDiff = Infinity;
    labels.forEach((lab, i) => {
      const diff = Math.abs(lab - mean);
      if (diff < minDiff) {
        minDiff = diff;
        closestIndex = i;
      }
    });

    const barTop = height - paddingBottom - barHeights[closestIndex];
    const topY = barTop - offset;

    const binCount = labels.length;
    const barGroupWidth = (width - paddingLeft) / binCount;
    const barWidth = barGroupWidth * 0.4;
    let barGroupCenter = paddingLeft + closestIndex * barGroupWidth + barGroupWidth / 2;

    if (side === "left") {
      barGroupCenter -= barWidth / 2;
    } else if (side === "right") {
      barGroupCenter += barWidth / 2;
    }

    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(barGroupCenter, topY);
    ctx.lineTo(barGroupCenter, barTop);
    ctx.stroke();

    ctx.fillStyle = color;
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText(`${label}=${mean.toFixed(2)}`, barGroupCenter, topY - 10);
  }

  function getAdjustedRaw(raw, now, flag) {
    if (flag != "overall") return { ...raw };

    const adjusted = {};
    for (const key of Object.keys(raw)) {
      const rawCount = raw[key] ?? 0;
      const nowCount = now[key] ?? 0;
      const diff = rawCount - nowCount;
      if (diff > 0) {
        adjusted[key] = diff;
      }
    }
    return adjusted;
  }

  function drawChart() {
    if (!canvas) return;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const adjustedRawData = getAdjustedRaw(rawData, nowData, flag);

    labels = Array.from(
      new Set([...Object.keys(adjustedRawData), ...Object.keys(nowData)].map(Number))
    ).sort((a, b) => a - b);

    const rawTotal = Object.values(adjustedRawData).reduce((a, b) => a + b, 0);
    const nowTotal = Object.values(nowData).reduce((a, b) => a + b, 0);

    const ySteps = 5;
    ctx.fillStyle = "#000";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.strokeStyle = "#999999";
    ctx.lineWidth = 0.5;
    const tickLength = 3;

    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      const percent = (i * 100 / ySteps) + "%";
      ctx.fillText(percent, paddingLeft - 10, y);
      ctx.beginPath();
      ctx.moveTo(paddingLeft - tickLength, y);
      ctx.lineTo(paddingLeft, y);
      ctx.stroke();
    }

    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(width, height - paddingBottom);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(paddingLeft, paddingTop);
    ctx.stroke();

    const binCount = labels.length;
    const barGroupWidth = (width - paddingLeft) / binCount;
    const barWidth = barGroupWidth * 0.4;

    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = "#000";
    labels.forEach((label, i) => {
      const x = paddingLeft + i * barGroupWidth + barGroupWidth / 2;
      ctx.fillText(label.toString(), x, height - paddingBottom + 5);
    });

    ctx.fillText("Score", paddingLeft + (width - paddingLeft) / 2, height - paddingBottom + 25);

    function createStripedPattern(ctx, color = NOWColor) {
      const size = 8;
      const patternCanvas = document.createElement('canvas');
      patternCanvas.width = size;
      patternCanvas.height = size;
      const pctx = patternCanvas.getContext('2d');
      pctx.strokeStyle = color;
      pctx.lineWidth = 1;
      pctx.beginPath();
      pctx.moveTo(0, size);
      pctx.lineTo(size, 0);
      pctx.stroke();
      return ctx.createPattern(patternCanvas, 'repeat');
    }

    labels.forEach((label, i) => {
      const rawCount = adjustedRawData[label] ?? 0;
      const nowCount = nowData[label] ?? 0;
      const rawHeight = rawTotal > 0 ? (rawCount / rawTotal) * (height - paddingTop - paddingBottom) : 0;
      const nowHeight = nowTotal > 0 ? (nowCount / nowTotal) * (height - paddingTop - paddingBottom) : 0;
      const barGroupCenter = paddingLeft + i * barGroupWidth + barGroupWidth / 2;

      rawBarHeights[i] = rawHeight;
      nowBarHeights[i] = nowHeight;

      const nowX = barGroupCenter - barWidth;
      ctx.fillStyle = NOWColor;
      ctx.fillRect(nowX, height - paddingBottom - nowHeight, barWidth, nowHeight);
      ctx.strokeStyle = "#999999";
      ctx.strokeRect(nowX, height - paddingBottom - nowHeight, barWidth, nowHeight);

      const rawX = barGroupCenter;
      ctx.fillStyle = createStripedPattern(ctx);
      ctx.fillRect(rawX, height - paddingBottom - rawHeight, barWidth, rawHeight);
      ctx.strokeStyle = "#999999";
      ctx.lineWidth = 0.3;
      ctx.strokeRect(rawX, height - paddingBottom - rawHeight, barWidth, rawHeight);

      ctx.beginPath();
      ctx.moveTo(barGroupCenter, height - paddingBottom);
      ctx.lineTo(barGroupCenter, height - paddingBottom + tickLength);
      ctx.stroke();
    });

    const legendY = 15;
    ctx.font = "10px sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";

    const rawMean = meanFromCounts(adjustedRawData);
    const nowMean = meanFromCounts(nowData);
    drawMeanLine(ctx, rawMean, "#666666", "x\u0305", labels, rawBarHeights, 3, "right");
    drawMeanLine(ctx, nowMean, "#000000", "x\u0305", labels, nowBarHeights, 3, "left");

    function countsToArray(data) {
      const arr = [];
      for (const [scoreStr, count] of Object.entries(data)) {
        const score = Number(scoreStr);
        for (let i = 0; i < count; i++) arr.push(score);
      }
      return arr;
    }

    const rawArr = countsToArray(adjustedRawData);
    const nowArr = countsToArray(nowData);
    let pValue = null;
    if (rawArr.length > 1 && nowArr.length > 1) {
      const mean1 = jStat.mean(rawArr);
      const mean2 = jStat.mean(nowArr);
      const var1 = jStat.variance(rawArr, true);
      const var2 = jStat.variance(nowArr, true);
      const n1 = rawArr.length;
      const n2 = nowArr.length;

      const t = (mean1 - mean2) / Math.sqrt(var1 / n1 + var2 / n2);

      const df = Math.pow(var1 / n1 + var2 / n2, 2) /
                ((Math.pow(var1 / n1, 2) / (n1 - 1)) + (Math.pow(var2 / n2, 2) / (n2 - 1)));

      pValue = 2 * (1 - jStat.studentt.cdf(Math.abs(t), df));
    }

    if (typeof pValue === "number") {
      ctx.fillStyle = "#000";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(`p = ${pValue.toExponential(2)}`, width - 140, legendY);
    }
  }

  onMount(() => {
    drawChart();
  });

  $: if (rawData && nowData) {
    drawChart();
  }
</script>

<canvas bind:this={canvas}></canvas>

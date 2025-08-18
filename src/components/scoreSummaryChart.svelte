<script>
  import { onMount } from 'svelte';

  let canvas;

  export let rawData;
  export let nowData;
  export let title;

  const width = 300;
  const height = 200;
  const paddingLeft = 50;
  const paddingBottom = 40;
  const paddingTop = 20;
  const overallColor = '#bf1818';
  const NOWColor = "#015dc6";
  const dpr = 2;

  let labels = [];

  function drawChart() {
    if (!canvas) return;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    labels = Array.from(
      new Set([...Object.keys(rawData), ...Object.keys(nowData)].map(Number))
    ).sort((a, b) => a - b);
    const rawTotal = Object.values(rawData).reduce((a, b) => a + b, 0);
    const nowTotal = Object.values(nowData).reduce((a, b) => a + b, 0);
    const ySteps = 5;
    ctx.fillStyle = "#000";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      const percent = (i * 100 / ySteps) + "%";
      ctx.fillText(percent, paddingLeft - 10, y);
      ctx.beginPath();
      ctx.moveTo(paddingLeft - 6, y);
      ctx.lineTo(paddingLeft, y);
      ctx.stroke();
    }

    ctx.strokeStyle = "#000";
    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(width, height - paddingBottom);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(paddingLeft, paddingTop);
    ctx.stroke();
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.font = "10px sans-serif";

    const binCount = labels.length;
    const barGroupWidth = (width - paddingLeft) / binCount;
    const barWidth = barGroupWidth * 0.2;

    labels.forEach((label, i) => {
      const x = paddingLeft + i * barGroupWidth + barGroupWidth / 2;
      ctx.fillText(label.toString(), x, height - paddingBottom + 5);
    });

    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.font = "10px sans-serif";
    ctx.fillStyle = "#000";
    ctx.fillText("Score", paddingLeft + (width - paddingLeft) / 2, height - paddingBottom + 15);

    labels.forEach((label, i) => {
      const rawCount = rawData[label] ?? 0;
      const nowCount = nowData[label] ?? 0;
      const rawHeight = rawTotal > 0 ? (rawCount / rawTotal) * (height - paddingTop - paddingBottom) : 0;
      const nowHeight = nowTotal > 0 ? (nowCount / nowTotal) * (height - paddingTop - paddingBottom) : 0;
      const barGroupCenter = paddingLeft + i * barGroupWidth + barGroupWidth / 2;
      const nowX = barGroupCenter - barWidth;

      ctx.fillStyle = NOWColor;
      ctx.fillRect(nowX, height - paddingBottom - nowHeight, barWidth, nowHeight);

      const rawX = barGroupCenter;
      ctx.fillStyle = overallColor;
      ctx.fillRect(rawX, height - paddingBottom - rawHeight, barWidth, rawHeight);
    });

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

  $: if (rawData && nowData) {
    drawChart();
  }
</script>

<canvas bind:this={canvas}></canvas>

<script>
  import { onMount } from 'svelte';

  let canvas;

  export let rawData;
  export let nowData;

  const width = 300;
  const height = 200;
  const padding = 0;
  const overallColor = '#015dc6';
  const NOWColor = "#bf1818";
  const dpr = 3;
  const displayWidth = width;
  const displayHeight = height;

  let labels = [];

  function drawChart() {
    if (!canvas) return;
    canvas.width = displayWidth * dpr;
    canvas.height = displayHeight * dpr;
    canvas.style.width = `${displayWidth}px`;
    canvas.style.height = `${displayHeight}px`;

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    labels = Array.from(
      new Set([...Object.keys(rawData), ...Object.keys(nowData)].map(Number))
    ).sort((a, b) => b - a);

    const getPercentages = (data) => {
      const values = labels.map(label => data[label] || 0);
      const total = values.reduce((a, b) => a + b, 0) || 1;
      return values.map(v => (v / total) * 100);
    };

    const rawPercent = getPercentages(rawData);
    const nowPercent = getPercentages(nowData);

    const tickLength = 6;
    const leftMargin = 50;
    const bottomMargin = 40;

    const violinHeight = (height - padding - bottomMargin) / labels.length;
    const chartBottomY = padding + labels.length * violinHeight;

    const xPoints = [
      leftMargin + (width - leftMargin) / 3,
      leftMargin + 2 * (width - leftMargin) / 3,
    ];
    
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(leftMargin, padding);
    ctx.lineTo(leftMargin, chartBottomY);
    ctx.stroke();

    ctx.font = '12px sans-serif';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'right';
    labels.forEach((label, i) => {
      const y = padding + i * violinHeight + violinHeight / 2;
      ctx.beginPath();
      ctx.moveTo(leftMargin - tickLength, y);
      ctx.lineTo(leftMargin, y);
      ctx.stroke();
      ctx.fillText(label, leftMargin - tickLength - 5, y);
    });

    ctx.beginPath();
    ctx.moveTo(leftMargin, chartBottomY);
    ctx.lineTo(width, chartBottomY);
    ctx.stroke();

    ctx.textBaseline = 'top';
    ctx.textAlign = 'center';
    const xLabels = ['Overall', 'Now'];
    xPoints.forEach((x, i) => {
      ctx.beginPath();
      ctx.moveTo(x, chartBottomY);
      ctx.lineTo(x, chartBottomY + tickLength);
      ctx.stroke();
      ctx.fillText(xLabels[i], x, chartBottomY + tickLength + 3);
    });

    function drawViolin(y, percent, xPos, color) {
      const maxWidth = violinHeight / 2;
      const heightSteps = 50;
      const density = [];
      for (let i = 0; i <= heightSteps; i++) {
        const t = i / heightSteps;
        const bell = Math.exp(-((t - 0.5) ** 2) * 8);
        density.push((percent / 100) * maxWidth * bell);
      }
      ctx.beginPath();
      ctx.moveTo(xPos, y);
      for (let i = 0; i <= heightSteps; i++) {
        const dy = (i / heightSteps) * violinHeight;
        const dx = -density[i];
        ctx.lineTo(xPos + dx, y + dy);
      }
      for (let i = heightSteps; i >= 0; i--) {
        const dy = (i / heightSteps) * violinHeight;
        const dx = density[i];
        ctx.lineTo(xPos + dx, y + dy);
      }
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
    }

    labels.forEach((_, i) => {
      const y = padding + i * violinHeight;
      drawViolin(y, rawPercent[i], xPoints[0], overallColor);
      drawViolin(y, nowPercent[i], xPoints[1], NOWColor);
    });
  }

  onMount(() => {
    drawChart();
  });

  $: if (rawData && nowData) {
    drawChart();
  }
</script>

<canvas bind:this={canvas}></canvas>


<script>
  import { onMount } from 'svelte';

  let canvas;

  export let rawData = {};
  export let nowData = {};

  const width = 400;
  const height = 200;
  const padding = 50;
  const overallColor = '#015dc6';
  const NOWColor = "#bf1818";

  let labels = [];

  onMount(() => {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, width, height);

    labels = Array.from(
      new Set([...Object.keys(rawData), ...Object.keys(nowData)].map(Number))
    ).sort((a, b) => a - b);

    const getPercentages = (data) => {
      const values = labels.map(label => data[label] || 0);
      const total = values.reduce((a, b) => a + b, 0) || 1;
      return values.map(v => (v / total) * 100);
    };

    const rawPercent = getPercentages(rawData);
    const nowPercent = getPercentages(nowData);

    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.stroke();

    const yStep = 20;
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#333';
    ctx.textBaseline = 'middle';

    for (let i = 0; i <= 100; i += yStep) {
      const y = height - padding - (i / 100) * (height - 2 * padding);
      ctx.beginPath();
      ctx.moveTo(padding - 5, y);
      ctx.lineTo(padding, y);
      ctx.stroke();
      ctx.fillText(i + '%', padding - 35, y);
    }

    const xStep = (width - 2 * padding) / (labels.length - 1);
    labels.forEach((label, i) => {
      const x = padding + i * xStep;
      ctx.beginPath();
      ctx.moveTo(x, height - padding);
      ctx.lineTo(x, height - padding + 5);
      ctx.stroke();
      ctx.fillText(label, x - 6, height - padding + 15);
    });

    function drawLine(percentages, color) {
      ctx.beginPath();
      percentages.forEach((p, i) => {
        const x = padding + i * xStep;
        const y = height - padding - (p / 100) * (height - 2 * padding);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    drawLine(rawPercent, overallColor);
    drawLine(nowPercent, NOWColor);

    drawLegend(ctx);
  });

  function drawLegend(ctx) {
    const legendItems = [
      { color: NOWColor, text: 'NOW pattern distribution' },
      { color: overallColor, text: 'Overall pattern distribution' }
    ];

    ctx.font = '14px sans-serif';
    ctx.textBaseline = 'middle';
    const legendWidth = 180;
    const startX = width - padding - legendWidth;
    const startY = padding - 30;

    legendItems.forEach(({ color, text }, i) => {
      const y = startY + i * 28;
      ctx.fillStyle = color;
      ctx.fillRect(startX, y, 24, 14);
      ctx.fillStyle = '#333';
      ctx.fillText(text, startX + 34, y + 7);
    });
  }
</script>

<canvas bind:this={canvas} width={width} height={height}></canvas>

<script>
  import { onMount } from 'svelte';

  let canvas;

  export let rawData;
  export let nowData;
  export let title;

  const width = 300;
  const height = 200;
  const padding = 0;
  const overallColor = '#bf1818';
  const NOWColor = "#015dc6";
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

    const allValues = [
      ...Object.entries(rawData).flatMap(([val, cnt]) => Array(cnt).fill(Number(val))),
      ...Object.entries(nowData).flatMap(([val, cnt]) => Array(cnt).fill(Number(val)))
    ];

    const globalMin = Math.min(...allValues);
    const globalMax = Math.max(...allValues);

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
    const xLabels = [title[0], title[1]];
    xPoints.forEach((x, i) => {
      ctx.beginPath();
      ctx.moveTo(x, chartBottomY);
      ctx.lineTo(x, chartBottomY + tickLength);
      ctx.stroke();
      ctx.fillText(xLabels[i], x, chartBottomY + tickLength + 3);
    });

    const scaleY = (val) => {
      const top = padding;
      const bottom = chartBottomY;
      const ratio = (val - globalMin) / (globalMax - globalMin || 1);
      return bottom - ratio * (bottom - top);
    };

    function drawBoxPlot(y, dataValue, xPos, color) {
      const values = Object.entries(dataValue).flatMap(([label, count]) => {
        return Array(count).fill(Number(label));
      }).sort((a, b) => a - b);

      const getQuantile = (arr, q) => {
        const pos = (arr.length - 1) * q;
        const base = Math.floor(pos);
        const rest = pos - base;
        if (arr.length === 0) return 0;
        if ((arr[base + 1] !== undefined)) {
          return arr[base] + rest * (arr[base + 1] - arr[base]);
        } else {
          return arr[base];
        }
      };

      const min = values[0] ?? 0;
      const max = values[values.length - 1] ?? 0;
      const q1 = getQuantile(values, 0.25);
      const median = getQuantile(values, 0.5);
      const q3 = getQuantile(values, 0.75);

      const boxTop = scaleY(q3);
      const boxBottom = scaleY(q1);
      const boxHeight = boxBottom - boxTop;

      const lineY = scaleY(median);
      const whiskerTop = scaleY(max);
      const whiskerBottom = scaleY(min);
      const boxWidth = violinHeight / 2;

      ctx.fillStyle = color + '33';
      ctx.fillRect(xPos - boxWidth / 2, boxTop, boxWidth, boxHeight);

      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.strokeRect(xPos - boxWidth / 2, boxTop, boxWidth, boxHeight);

      ctx.strokeStyle = '#000';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(xPos - boxWidth / 2, lineY);
      ctx.lineTo(xPos + boxWidth / 2, lineY);
      ctx.stroke();

      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(xPos, boxTop);
      ctx.lineTo(xPos, whiskerTop);
      ctx.moveTo(xPos, boxBottom);
      ctx.lineTo(xPos, whiskerBottom);
      ctx.stroke();

      const capWidth = boxWidth / 2.5;
      ctx.beginPath();
      ctx.moveTo(xPos - capWidth, whiskerTop);
      ctx.lineTo(xPos + capWidth, whiskerTop);
      ctx.moveTo(xPos - capWidth, whiskerBottom);
      ctx.lineTo(xPos + capWidth, whiskerBottom);
      ctx.stroke();
    }

    labels.forEach((_, i) => {
      const y = padding + i * violinHeight;
      drawBoxPlot(y, nowData, xPoints[0], NOWColor);
      drawBoxPlot(y, rawData, xPoints[1], overallColor);
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

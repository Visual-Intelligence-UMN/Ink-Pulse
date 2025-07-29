<script lang="ts">
  import { onMount } from "svelte";

  export let patternSessions;
  export let lengthData;
  export let lengthSummaryData;

  const overallColor = '#015dc6';
  const NOWColor = "#bf1818";
  const overallPoint = '#4d6aca'

  let canvasEl: HTMLCanvasElement;

  function drawChart() {
    if (!canvasEl) return;
    const dpr = 3;

    const width = 500;
    const height = 300;

    canvasEl.width = width * dpr;
    canvasEl.height = height * dpr;
    canvasEl.style.width = width + "px";
    canvasEl.style.height = height + "px";

    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.clearRect(0, 0, width, height);

    const paddingLeft = 60;
    const paddingBottom = 50;
    const paddingTop = 30;
    const paddingRight = 60;

    const binCount = lengthSummaryData.length;
    const barWidth = (width - paddingLeft - paddingRight) / binCount;

    const totalCount = lengthSummaryData.reduce((acc, item) => acc + item[1], 0);
    const bins = lengthSummaryData.map(item => {
      const [minStr, maxStr] = item[0].split('-');
      return {
        label: item[0],
        min: Number(minStr),
        max: Number(maxStr),
        count: item[1],
        percent: item[1] / totalCount,
      };
    });

    const maxLength = Math.max(
      ...patternSessions.map(s => (s.similarityData?.[0]?.sentence ?? 0) * 3000),
      ...bins.map(b => b.max)
    );

    ctx.fillStyle = "#000";
    ctx.font = "7px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    bins.forEach((bin, i) => {
      const x = paddingLeft + i * barWidth + barWidth / 2;
      ctx.fillText(bin.label, x, height - paddingBottom + 5);
    });

    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.font = "12px sans-serif";
    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      const percentLabel = (i * 100 / ySteps) + "%";
      ctx.fillText(percentLabel, paddingLeft - 10, y);
    }

    ctx.font = "10px sans-serif";
    ctx.save();
    ctx.restore();
    const xAxisLabel = "Content Length";
    ctx.fillText(xAxisLabel, paddingLeft + (width - paddingLeft) / 2, height - paddingBottom + 20);

    ctx.strokeStyle = "#000";
    ctx.beginPath();
    ctx.moveTo(paddingLeft, paddingTop);
    ctx.lineTo(paddingLeft, height - paddingBottom);
    ctx.stroke();

    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      const lengthLabel = Math.round(i * maxLength / ySteps).toString();
      ctx.fillText(lengthLabel, width - paddingRight + 10, y);
    }

    ctx.beginPath();
    ctx.moveTo(width - paddingRight, paddingTop);
    ctx.lineTo(width - paddingRight, height - paddingBottom);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(width - paddingRight, height - paddingBottom);
    ctx.stroke();
    ctx.fillStyle = overallColor;
    bins.forEach((bin, i) => {
      const barHeight = bin.percent * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + barWidth * 0.1;
      const y = height - paddingBottom - barHeight;
      const bw = barWidth * 0.8;
      ctx.fillRect(x, y, bw, barHeight);
    });

    ctx.fillStyle = overallPoint;
    lengthData.forEach(session => {
      const length = session;
      if (length === undefined) return;

      const binIndex = bins.findIndex(b => length >= b.min && length < b.max);
      if (binIndex === -1) return;

      const x = paddingLeft + binIndex * barWidth + Math.random() * barWidth;

      const y = height - paddingBottom - (length / maxLength) * (height - paddingTop - paddingBottom);

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, 2 * Math.PI);
      ctx.fill();
    });

    ctx.fillStyle = NOWColor;
    patternSessions.forEach(session => {
      const val = session.similarityData?.[0]?.sentence;
      if (val === undefined) return;
      const length = val * 3000;

      const binIndex = bins.findIndex(b => length >= b.min && length < b.max);
      if (binIndex === -1) return;

      const x = paddingLeft + binIndex * barWidth + Math.random() * barWidth;

      const y = height - paddingBottom - (length / maxLength) * (height - paddingTop - paddingBottom);

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, 2 * Math.PI);
      ctx.fill();
    });
  }

  onMount(() => {
    drawChart();
  });

  $: if (patternSessions && lengthData && lengthSummaryData) {
    drawChart();
  }
</script>

<canvas bind:this={canvasEl} />

<script lang="ts">
  import { onMount } from "svelte";

  export let patternSessions;
  export let overallSemScoreData;
  export let overallSemScoreSummaryData;
  export let flag;
  export let title;

  const overallColor = "#bf1818";
  const NOWColor = '#015dc6';

  let canvasEl: HTMLCanvasElement;

  function drawChart() {
    if (!canvasEl) return;
    const dpr = 3;
    const width = 450;
    const height = 200;

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

    const maxScore = 36;
    const fixedBinLabels = [
      "0-3", "3-6", "6-9", "9-12", "12-15",
      "15-18", "18-21", "21-24", "24-27", "27-30", "30-33", "33-36"
    ];

    let bins = fixedBinLabels.map(label => {
      const [minStr, maxStr] = label.split("-");
      return {
        label,
        min: Number(minStr),
        max: Number(maxStr),
        count: 0,
        percent: 0,
      };
    });

    let nowBins = fixedBinLabels.map(label => {
      const [minStr, maxStr] = label.split('-');
      return {
        label,
        min: Number(minStr),
        max: Number(maxStr),
        count: 0,
        nowPercent: 0,
      };
    });

    if (flag === "overall") {
      overallSemScoreSummaryData.forEach(([label, count]) => {
        const binIndex = bins.findIndex(b => b.label === label);
        if (binIndex !== -1) bins[binIndex].count = count;
      });
    } else {
      overallSemScoreSummaryData.forEach((session: any) => {
        const Id = session.sessionId;
        const scoreEntry = overallSemScoreData.find(([id, _]) => id === Id);
        if (!scoreEntry) return;
        const score = scoreEntry[1];
        const binIndex = bins.findIndex(b => score >= b.min && score < b.max);
        if (binIndex !== -1) bins[binIndex].count++;
      });
    }
    const totalCount = bins.reduce((acc, b) => acc + b.count, 0);
    bins.forEach(b => {
      b.percent = totalCount > 0 ? b.count / totalCount : 0;
    });

    patternSessions.forEach(session => {
      const Id = session.sessionId;
      const scoreEntry = overallSemScoreData.find(([id, _]) => id === Id);
      if (!scoreEntry) return;
      const score = scoreEntry[1];
      const binIndex = nowBins.findIndex(b => score >= b.min && score < b.max);
      if (binIndex !== -1) nowBins[binIndex].count++;
    });

    const nowTotalCount = nowBins.reduce((acc, b) => acc + b.count, 0);
    nowBins.forEach(b => {
      b.nowPercent = nowTotalCount > 0 ? b.count / nowTotalCount : 0;
    });

    ctx.fillStyle = "#000";
    ctx.font = "7px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    const binCount = bins.length;
    const barWidth = (width - paddingLeft - paddingRight) / binCount;

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
      const percent = (i * 100 / ySteps) + "%";
      ctx.fillText(percent, paddingLeft - 10, y);
      ctx.beginPath();
      ctx.moveTo(paddingLeft - 6, y);
      ctx.lineTo(paddingLeft, y);
      ctx.stroke();
    }

    ctx.font = "10px sans-serif";
    ctx.fillText("Overall Sem Score", paddingLeft + (width - paddingLeft) / 2, height - paddingBottom + 20);
    ctx.strokeStyle = "#000";
    ctx.beginPath();
    ctx.moveTo(paddingLeft, paddingTop);
    ctx.lineTo(paddingLeft, height - paddingBottom);
    ctx.stroke();
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      const scoreLabel = Math.round(i * maxScore / ySteps).toString();
      ctx.fillText(scoreLabel, width - paddingRight + 10, y);
    }

    ctx.beginPath();
    ctx.moveTo(width - paddingRight, paddingTop);
    ctx.lineTo(width - paddingRight, height - paddingBottom);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(width - paddingRight, height - paddingBottom);
    ctx.stroke();

    ctx.fillStyle = NOWColor;
    nowBins.forEach((bin, i) => {
      const barHeight = bin.nowPercent * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + barWidth * 0.1;
      const y = height - paddingBottom - barHeight;
      const bw = barWidth * 0.2;
      ctx.fillRect(x, y, bw, barHeight);
    });

    ctx.fillStyle = overallColor;
    bins.forEach((bin, i) => {
      const barHeight = bin.percent * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + barWidth * 0.1 + (barWidth * 0.4) / 2;
      const y = height - paddingBottom - barHeight;
      const bw = barWidth * 0.2;
      ctx.fillRect(x, y, bw, barHeight);
    });

    const legendX = 85;
    const legendY = 25;
    const legendBoxSize = 12;
    const legendSpacing = 5;
    ctx.font = "12px sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "left";
    ctx.fillStyle = NOWColor;
    ctx.fillRect(legendX - legendBoxSize, legendY, legendBoxSize, legendBoxSize);
    ctx.fillStyle = "#000";
    ctx.fillText(title[0], legendX + legendBoxSize - legendSpacing, legendY + legendBoxSize / 2);
    ctx.fillStyle = overallColor;
    ctx.fillRect(legendX - legendBoxSize, legendY + legendBoxSize + legendSpacing, legendBoxSize, legendBoxSize);
    ctx.fillStyle = "#000";
    ctx.fillText(title[1], legendX + legendBoxSize - legendSpacing, legendY + legendBoxSize + legendSpacing + legendBoxSize / 2);
  }

  onMount(() => {
    drawChart();
  });

  $: if (patternSessions && overallSemScoreData && overallSemScoreSummaryData && flag) {
    drawChart();
  }
</script>

<canvas bind:this={canvasEl} />

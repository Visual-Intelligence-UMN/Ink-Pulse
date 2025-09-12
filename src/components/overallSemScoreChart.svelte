<script lang="ts">
  import { onMount } from "svelte";
  import jStat from 'jstat';

  export let patternSessions;
  export let overallSemScoreData;
  export let overallSemScoreSummaryData;
  export let flag;
  export let title;

  const NOWColor = '#999999';
  const overallColor = '#ffffff';

  let canvasEl: HTMLCanvasElement;

  function drawChart() {
    if (!canvasEl) return;
    const dpr = 2;
    const width = 250;
    const height = 175;

    canvasEl.width = width * dpr;
    canvasEl.height = height * dpr;
    canvasEl.style.width = width + "px";
    canvasEl.style.height = height + "px";

    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const paddingLeft = 40;
    const paddingBottom = 45;
    const paddingTop = 40;
    const paddingRight = 0;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "#ccc";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(paddingLeft, 0);
    ctx.lineTo(width - paddingRight, 0);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(width - paddingRight, 0);
    ctx.lineTo(width - paddingRight, height - 40);
    ctx.stroke();
    const fixedBinLabels = [
      "0-3", "3-6", "6-9", "9-12", "12-15",
      "15-18", "18-21", "21-24", "24-27", "27-30", "30-33", "33-36"
    ];

    const binCount = fixedBinLabels.length;
    const barWidthRatio = 0.4;

    const bins = fixedBinLabels.map(label => {
      const [minStr, maxStr] = label.split("-").map(Number);
      return { label, min: minStr, max: maxStr, count: 0, percent: 0 };
    });
    const nowBins = fixedBinLabels.map(label => {
      const [minStr, maxStr] = label.split("-").map(Number);
      return { label, min: minStr, max: maxStr, count: 0, nowPercent: 0 };
    });

    const scoreMap: Map<string, number> = new Map(
      overallSemScoreData.map(([id, score]) => [id, score])
    );

    const removedIds = new Set(patternSessions.map(s => s.session_id));
    const overallArr = [];
    const highlightArr = [];
    if (flag === "overall") {
      overallSemScoreData.forEach(([id, score]) => {
        if (removedIds.has(id)) return;
        const bin = bins.find(b => score >= b.min && score < b.max);
        if (bin) bin.count++;
        overallArr.push(score);
      });
    } else {
      overallSemScoreSummaryData.forEach(session => {
        const score = scoreMap.get(session.sessionId);
        if (score == null) return;
        const bin = bins.find(b => score >= b.min && score < b.max);
        if (bin) bin.count++;
        overallArr.push(score);
      });
    }

    patternSessions.forEach(s => {
      const score = scoreMap.get(s.sessionId);
      if (score === undefined) return;
      const bin = nowBins.find(b => score >= b.min && score < b.max);
      if (bin) bin.count++;
      highlightArr.push(score);
    });

    const totalCount = bins.reduce((acc, b) => acc + b.count, 0);
    bins.forEach(b => b.percent = totalCount > 0 ? b.count / totalCount : 0);
    const nowTotalCount = nowBins.reduce((acc, b) => acc + b.count, 0);
    nowBins.forEach(b => b.nowPercent = nowTotalCount > 0 ? b.count / nowTotalCount : 0);

    ctx.fillStyle = "#000";
    ctx.font = "7px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const barWidth = (width - paddingLeft - paddingRight) / binCount;
    bins.forEach((bin, i) => {
      const x = paddingLeft + i * barWidth + barWidth / 2;
      const y = height - paddingBottom + 5;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(-Math.PI / 4);
      ctx.textAlign = "right";
      ctx.fillText(bin.label, 0, 0);
      ctx.restore();
    });

    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.font = "10px sans-serif";
    const ySteps = 5;
    const tickLength = 3;
    ctx.strokeStyle = "#999999";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      ctx.fillStyle = "#000";
      ctx.fillText((i * 100 / ySteps) + "%", paddingLeft - 10, y);
      ctx.beginPath();
      ctx.moveTo(paddingLeft - tickLength, y);
      ctx.lineTo(paddingLeft, y);
      ctx.stroke();
    }

    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Accumulative semantic scores", paddingLeft + (width - paddingLeft - paddingRight) / 2, height - paddingBottom + 35);

    ctx.beginPath();
    ctx.moveTo(paddingLeft, paddingTop);
    ctx.lineTo(paddingLeft, height - paddingBottom);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(width - paddingRight, height - paddingBottom);
    ctx.stroke();

    const offset = (barWidth - 2 * barWidthRatio * barWidth) / 2;
    nowBins.forEach((bin, i) => {
      const barHeight = bin.nowPercent * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + offset;
      const y = height - paddingBottom - barHeight;
      ctx.fillStyle = NOWColor;
      ctx.fillRect(x, y, barWidth * barWidthRatio, barHeight);
    });

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

    ctx.fillStyle = createStripedPattern(ctx);
    bins.forEach((bin, i) => {
      const barHeight = bin.percent * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + offset + barWidth * barWidthRatio;
      const y = height - paddingBottom - barHeight;
      ctx.fillRect(x, y, barWidth * barWidthRatio, barHeight);
      ctx.strokeStyle = NOWColor;
      ctx.lineWidth = 0.3;
      ctx.strokeRect(x, y, barWidth * barWidthRatio, barHeight);
    });

    let overallScores;
    if (flag === "overall") {
      overallScores = overallSemScoreData
        .filter(([id, _]) => !removedIds.has(id))
        .map(([_, score]) => score);
    } else {
      overallScores = overallSemScoreSummaryData
        .map(s => scoreMap.get(s.sessionId))
        .filter((score): score is number => score !== undefined);
    }

    const nowScores = patternSessions
      .map(s => scoreMap.get(s.sessionId))
      .filter((score): score is number => score !== undefined);

    const overallMean = overallScores.reduce((a,b)=>a+b,0)/overallScores.length;
    const highlightMean = nowScores.reduce((a,b)=>a+b,0)/nowScores.length;

    let pValue = null;
    if (overallScores.length > 1 && nowScores.length > 1) {
      const mean1 = jStat.mean(overallScores);
      const mean2 = jStat.mean(nowScores);
      const var1 = jStat.variance(overallScores, true);
      const var2 = jStat.variance(nowScores, true);
      const n1 = overallScores.length;
      const n2 = nowScores.length;

      const t = (mean1 - mean2) / Math.sqrt(var1 / n1 + var2 / n2);

      const df = Math.pow(var1 / n1 + var2 / n2, 2) /
                ((Math.pow(var1 / n1, 2) / (n1 - 1)) + (Math.pow(var2 / n2, 2) / (n2 - 1)));

      pValue = 2 * (1 - jStat.studentt.cdf(Math.abs(t), df));
    }

    const legendY = 30;
    ctx.font = "10px sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    let displayP;
    if (pValue !== null){
      ctx.fillStyle = "#000";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      if (pValue < 1e-16) {
        displayP = "p<1e-16";
      } else {
        displayP = `p=${pValue.toExponential(2)}`;
      }
      ctx.fillText(displayP, width - 200, legendY + 20);
    }

    function drawStdErrorBar(ctx, values, color, y) {
      if (!values || values.length < 3) return;

      const mean = jStat.mean(values);
      const stdDev = jStat.stdev(values);

      const totalRange = 36;
      const meanX = paddingLeft + (mean / totalRange) * (width - paddingLeft - paddingRight);
      const stdDevPx = (stdDev / totalRange) * (width - paddingLeft - paddingRight);

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

    const topContainerHeight = paddingTop;
    ctx.fillStyle = "#f5f5f5";
    ctx.fillRect(500, 0, width - paddingLeft - paddingRight + 50, topContainerHeight);

    ctx.strokeStyle = "#ccc";
    ctx.lineWidth = 1;
    ctx.strokeRect(40, 0, width, topContainerHeight);

    const overallMeanX = drawStdErrorBar(ctx, overallArr, "#666", topContainerHeight - 5);
    const highlightMeanX = drawStdErrorBar(ctx, highlightArr, "#000", topContainerHeight - 25);

    ctx.fillText(`avg(${title[0]})=${highlightMean.toFixed(2)}`, highlightMeanX / 2, topContainerHeight - 35);
    ctx.fillStyle = "#666";
    ctx.fillText(`avg(${title[1]})=${overallMean.toFixed(2)}`, overallMeanX / 2, topContainerHeight - 15);
  }

  onMount(() => {
    drawChart();
  });

  $: if (patternSessions && overallSemScoreData && overallSemScoreSummaryData && flag) {
    drawChart();
  }
</script>

<canvas bind:this={canvasEl} />

<script lang="ts">
  import { onMount } from "svelte";
  import jStat from 'jstat';

  export let patternSessions;
  export let lengthData;
  export let lengthSummaryData;
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
    const paddingBottom = 40;
    const paddingTop = 20;
    const paddingRight = 0;

    const fixedBinLabels = [
      "500-1000", "1000-1500", "1500-2000", "2000-2500", "2500-3000",
      "3000-3500", "3500-4000", "4000-4500", "4500-5000", "5000-5500", "5500-6000"
    ];

    let bins = fixedBinLabels.map(label => {
      const [minStr, maxStr] = label.split('-');
      return { label, min: Number(minStr), max: Number(maxStr), count: 0, percent: 0 };
    });
    let nowBins = fixedBinLabels.map(label => {
      const [minStr, maxStr] = label.split('-');
      return { label, min: Number(minStr), max: Number(maxStr), count: 0, nowPercent: 0 };
    });

    const overallArr = [];
    const highlightArr = [];
    const removedIds = new Set(patternSessions.map(s => s.session_id));

    if (flag === "overall") {
      lengthData.forEach(session => {
        const val = session.sentence ?? null;
        if (val == null) return;
        if (removedIds.has(session.session_id)) return;

        const length = val;
        const binIndex = bins.findIndex(b => length >= b.min && length < b.max);
        if (binIndex !== -1) bins[binIndex].count++;
        overallArr.push(length);
      });
    } else {
      lengthSummaryData.forEach(session => {
        const val = session.similarityData?.[session.similarityData.length - 1]?.sentence ?? null;
        if (val == null) return;

        const length = val * 3000;
        const binIndex = bins.findIndex(b => length >= b.min && length < b.max);
        if (binIndex !== -1) bins[binIndex].count++;
        overallArr.push(length);
      });
    }

    patternSessions.forEach(session => {
      const val = session.similarityData?.[session.similarityData.length - 1]?.sentence;
      if (val == null) return;
      const length = val * 3000;
      const binIndex = nowBins.findIndex(b => length >= b.min && length < b.max);
      if (binIndex !== -1) nowBins[binIndex].count++;
      highlightArr.push(length);
    });

    const totalCount = bins.reduce((acc, b) => acc + b.count, 0);
    bins.forEach(b => { b.percent = totalCount > 0 ? b.count / totalCount : 0; });

    const nowTotalCount = nowBins.reduce((acc, b) => acc + b.count, 0);
    nowBins.forEach(b => { b.nowPercent = nowTotalCount > 0 ? b.count / nowTotalCount : 0; });

    ctx.fillStyle = "#000";
    ctx.font = "6px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    const binCount = bins.length;
    const barWidth = (width - paddingLeft - paddingRight) / binCount;
    const barWidthRatio = 0.4;
    const totalBarsWidth = 2 * barWidth * barWidthRatio;
    const offset = (barWidth - totalBarsWidth) / 2;

    bins.forEach((bin, i) => {
      const x = paddingLeft + i * barWidth + barWidth / 2;
      const y = height - paddingBottom + 5;
      const angle = -Math.PI / 4;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.textAlign = "right";
      ctx.fillText(bin.label, 0, 0);
      ctx.restore();
    });

    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.font = "10px sans-serif";
    const ySteps = 5;
    const tickLength = 3;
    for (let i = 0; i <= ySteps; i++) {
      const y = height - paddingBottom - (i * (height - paddingTop - paddingBottom) / ySteps);
      const percent = (i * 100 / ySteps) + "%";
      ctx.fillText(percent, paddingLeft - 10, y);
      ctx.beginPath();
      ctx.strokeStyle = "#999999";
      ctx.lineWidth = 0.5;
      ctx.moveTo(paddingLeft - tickLength, y);
      ctx.lineTo(paddingLeft, y);
      ctx.stroke();
    }
    ctx.textAlign = "center";
    ctx.fillText("Content Length", paddingLeft + (width - paddingLeft - paddingRight) / 2, height - paddingBottom + 35);
    ctx.beginPath();
    ctx.moveTo(paddingLeft, paddingTop);
    ctx.lineTo(paddingLeft, height - paddingBottom);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(paddingLeft, height - paddingBottom);
    ctx.lineTo(width - paddingRight, height - paddingBottom);
    ctx.stroke();

    ctx.fillStyle = NOWColor;
    nowBins.forEach((bin, i) => {
      const barHeight = bin.nowPercent * (height - paddingTop - paddingBottom);
      const x = paddingLeft + i * barWidth + offset;
      const y = height - paddingBottom - barHeight;
      const bw = barWidth * barWidthRatio;
      ctx.fillRect(x, y, bw, barHeight);
      const middleX = x + bw;
      const tickYStart = height - paddingBottom;
      const tickYEnd = tickYStart + 3;
      ctx.beginPath();
      ctx.moveTo(middleX, tickYStart);
      ctx.lineTo(middleX, tickYEnd);
      ctx.stroke();
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
      const bw = barWidth * barWidthRatio;
      ctx.fillRect(x, y, bw, barHeight);
      ctx.strokeStyle = NOWColor;
      ctx.lineWidth = 0.3;
      ctx.strokeRect(x, y, bw, barHeight);
    });

    const overallMean = overallArr.reduce((a,b)=>a+b,0) / (overallArr.length||1);
    const highlightMean = highlightArr.reduce((a,b)=>a+b,0) / (highlightArr.length||1);

    let pValue = null;
    if (overallArr.length > 1 && highlightArr.length > 1) {
      const mean1 = jStat.mean(overallArr);
      const mean2 = jStat.mean(highlightArr);
      const var1 = jStat.variance(overallArr, true);
      const var2 = jStat.variance(highlightArr, true);
      const n1 = overallArr.length;
      const n2 = highlightArr.length;

      const t = (mean1 - mean2) / Math.sqrt(var1/n1 + var2/n2);
      const df = Math.pow(var1/n1 + var2/n2, 2) /
                ((Math.pow(var1/n1,2)/(n1-1)) + (Math.pow(var2/n2,2)/(n2-1)));
      const pValueTwoTailed = 2 * (1 - jStat.studentt.cdf(Math.abs(t), df));

      pValue = pValueTwoTailed;
    }

    function drawMeanLine(mean, color, label, side: "left"|"right") {
      let closestIndex = 0;
      let minDiff = Infinity;
      bins.forEach((b, i) => {
        const mid = (b.min + b.max)/2;
        const diff = Math.abs(mid - mean);
        if(diff < minDiff){ minDiff = diff; closestIndex = i;}
      });
      const barHeights = side==="left" ? nowBins.map(b=>b.nowPercent*(height-paddingTop-paddingBottom))
                                       : bins.map(b=>b.percent*(height-paddingTop-paddingBottom));
      const barTop = height - paddingBottom - barHeights[closestIndex];
      const topY = barTop - 3;
      const barGroupCenter = paddingLeft + closestIndex * barWidth + barWidth/2 + (side==="left"? -barWidth*barWidthRatio/2 : barWidth*barWidthRatio/2);

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

    drawMeanLine(overallMean, "#666666", "x\u0305", "right");
    drawMeanLine(highlightMean, "#000000", "x\u0305", "left");

    const legendY = 30;
    ctx.font = "10px sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";

    if (pValue !== null) {
      ctx.fillStyle = "#000";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`p=${pValue.toExponential(2)}`, width - 200, legendY - 10);
    }

  }

  onMount(() => {
    drawChart();
  });

  $: if (patternSessions && lengthData && lengthSummaryData && flag) {
    drawChart();
  }
</script>

<canvas bind:this={canvasEl} />

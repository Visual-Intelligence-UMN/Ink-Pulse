<script lang="ts">
  import { onMount } from 'svelte';
  import jStat from 'jstat';

  // --- Component Props ---
  /** The key to extract from data items (e.g., "length", "judge_score") */
  export let featureName: string;
  /** The "highlight" dataset. Items are { session_id, value } */
  export let data: { session_id: string, value: string | number }[] = [];
  /** The "comparison" dataset. Structure depends on `flag`. */
  export let patternData: any[] | Set<any> = [];
  /** The "universe" of all session data, used when flag is not 'overall'. */
  export let featureData: { session_id: string, [key: string]: any }[] = [];
  /** Controls how `patternData` is interpreted. */
  export let flag: 'overall' | string;
  /** Legend titles for the plots: [0] = highlight (data), [1] = comparison (patternData) */
  export let title: [string, string] = ['Group 1', 'Group 2'];

  const binSizes: Record<string, number> = {
    judge_score: 1,
    length: 500,
    AI_ratio: 0.1,
    sum_semantic_score: 3
  };

  const binSize = binSizes[featureName] ?? 1; // default to 1 if featureName not found


  // --- Charting Constants ---
  const HIGHLIGHT_COLOR = '#999999'; // Color for the 'data' group
  const PADDING_LEFT = 40;
  const PADDING_BOTTOM = 45;
  const PADDING_TOP = 40;
  const PADDING_RIGHT = 0;
  const CHART_WIDTH = 250;
  const CHART_HEIGHT = 175;
  const DPR = 2; // Device Pixel Ratio for crisp canvas

  // --- Svelte Bindings ---
  let canvasEl: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;

  // --- Reactive Data Processing ---
  let highlightArr: number[] = [];
  let overallArr: number[] = [];

  $: {
    // Process the "highlight" group (from `data` prop)
    // The `value` is already extracted.
    highlightArr = data
      .map(d => parseFloat(String(d.value)))
      .filter(v => !isNaN(v));

    // Process the "comparison" group (from `patternData`)
    let tempOverallArr: number[] = [];
    if (flag === 'overall') {
      // `patternData` is an array of data objects
      // We just need to extract the value by `featureName`
      tempOverallArr = Array.from(patternData)
        .map(item => parseFloat(item[featureName]))
        .filter(v => !isNaN(v));
    } else {
      // `patternData` is an array of session_ids
      // We must look up the full session in `featureData`
      const comparisonSessionIds = new Set(patternData);
      tempOverallArr = featureData
        .filter(item => comparisonSessionIds.has(item.session_id))
        .map(item => parseFloat(item[featureName]))
        .filter(v => !isNaN(v));
    }
    overallArr = tempOverallArr;
  }

  /**
   * Main function to draw the entire chart.
   */
  function drawChart() {
    if (!canvasEl) return;
    if (!ctx) {
      ctx = canvasEl.getContext('2d');
      if (!ctx) return;
    }

    // --- 1. Canvas Setup ---
    canvasEl.width = CHART_WIDTH * DPR;
    canvasEl.height = CHART_HEIGHT * DPR;
    canvasEl.style.width = CHART_WIDTH + 'px';
    canvasEl.style.height = CHART_HEIGHT + 'px';

    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.clearRect(0, 0, CHART_WIDTH, CHART_HEIGHT);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CHART_WIDTH, CHART_HEIGHT);
    
    // --- 2. Dynamic Binning with binSize ---
    const allValues = [...highlightArr, ...overallArr];
    if (allValues.length === 0) {
      drawEmptyChart('No data to display');
      return;
    }

    const globalMin = 0;
    const globalMax = jStat.max(allValues);

    // Calculate number of bins based on given binSize
    let binCount = Math.ceil((globalMax - globalMin) / binSize);
    if (binCount === 0) binCount = 1;

    let comparisonBins: any[] = [];
    let highlightBins: any[] = [];

    for (let i = 0; i < binCount; i++) {
      const min = globalMin + i * binSize;
      const max = min + binSize;
      const label = `${Math.floor(min * 100) / 100}-${Math.floor(max * 100) / 100}`;    
      comparisonBins.push({ label, min, max, count: 0, percent: 0 });
      highlightBins.push({ label, min, max, count: 0, nowPercent: 0 });
    }

    // Ensure the last bin captures the maximum value
    comparisonBins[comparisonBins.length - 1].max = globalMax + 0.0001;
    highlightBins[highlightBins.length - 1].max = globalMax + 0.0001;

    // --- 3. Populate Bins ---
    overallArr.forEach(val => {
      const binIndex = comparisonBins.findIndex(b => val >= b.min && val < b.max);
      if (binIndex !== -1) comparisonBins[binIndex].count++;
    });

    highlightArr.forEach(val => {
      const binIndex = highlightBins.findIndex(b => val >= b.min && val < b.max);
      if (binIndex !== -1) highlightBins[binIndex].count++;
    });

    // --- Trim empty bins at the start and end ---
    const trimEmptyBins = (binsa, binsb) => {
      let start = 0;
      while (binsa[start].count === 0 && binsb[start].count === 0) start++;
      let end = Math.max(binsa.length, binsb.length) - 1;
      while (end >= 0 && binsa[end].count === 0 && binsb[end].count === 0) end--;
      return [binsa.slice(start, end + 1), binsb.slice(start, end + 1)];
    };

    [comparisonBins, highlightBins] = trimEmptyBins(comparisonBins, highlightBins);

    // Calculate percentages
    const totalCount = comparisonBins.reduce((acc, b) => acc + b.count, 0);
    comparisonBins.forEach(b => { b.percent = totalCount > 0 ? b.count / totalCount : 0; });

    const nowTotalCount = highlightBins.reduce((acc, b) => acc + b.count, 0);
    highlightBins.forEach(b => { b.nowPercent = nowTotalCount > 0 ? b.count / nowTotalCount : 0; });

    // --- 4. Draw Axes and Labels ---
    ctx.fillStyle = '#000';
    ctx.font = '6px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    const barWidth = (CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT) / comparisonBins.length;
    
    // Draw X-axis labels (rotated bin labels)
    comparisonBins.forEach((bin, i) => {
      const x = PADDING_LEFT + i * barWidth + barWidth / 2;
      const y = CHART_HEIGHT - PADDING_BOTTOM + 5;
      const angle = -Math.PI / 4;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.textAlign = 'right';
      ctx.fillText(bin.label, 0, 0);
      ctx.restore();
    });

    // Draw Y-axis labels (%
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.font = '10px sans-serif';
    const ySteps = 5;
    const tickLength = 3;
    for (let i = 0; i <= ySteps; i++) {
      const y = CHART_HEIGHT - PADDING_BOTTOM - (i * (CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM) / ySteps);
      const percent = (i * 100 / ySteps) + '%';
      ctx.fillText(percent, PADDING_LEFT - 10, y);
      ctx.beginPath();
      ctx.strokeStyle = '#999999';
      ctx.lineWidth = 0.5;
      ctx.moveTo(PADDING_LEFT - tickLength, y);
      ctx.lineTo(PADDING_LEFT, y);
      ctx.stroke();
    }
    
    // Draw axis title
    ctx.textAlign = 'center';
    ctx.fillText(featureName, PADDING_LEFT + (CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT) / 2, CHART_HEIGHT - PADDING_BOTTOM + 35);
    
    // Draw axis lines
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(PADDING_LEFT, PADDING_TOP);
    ctx.lineTo(PADDING_LEFT, CHART_HEIGHT - PADDING_BOTTOM);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(PADDING_LEFT, CHART_HEIGHT - PADDING_BOTTOM);
    ctx.lineTo(CHART_WIDTH - PADDING_RIGHT, CHART_HEIGHT - PADDING_BOTTOM);
    ctx.stroke();

    // --- 5. Draw Histogram Bars ---
    const barWidthRatio = 0.4;
    const totalBarsWidth = 2 * barWidth * barWidthRatio;
    const offset = (barWidth - totalBarsWidth) / 2;

    // Draw highlight bars (solid)
    ctx.fillStyle = HIGHLIGHT_COLOR;
    highlightBins.forEach((bin, i) => {
      const barHeight = bin.nowPercent * (CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM);
      const x = PADDING_LEFT + i * barWidth + offset;
      const y = CHART_HEIGHT - PADDING_BOTTOM - barHeight;
      const bw = barWidth * barWidthRatio;
      ctx.fillRect(x, y, bw, barHeight);
    });

    // Create pattern for comparison bars
    const stripedPattern = createStripedPattern(ctx, HIGHLIGHT_COLOR);
    if (stripedPattern) ctx.fillStyle = stripedPattern;

    // Draw comparison bars (striped)
    comparisonBins.forEach((bin, i) => {
      const barHeight = bin.percent * (CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM);
      const x = PADDING_LEFT + i * barWidth + offset + barWidth * barWidthRatio;
      const y = CHART_HEIGHT - PADDING_BOTTOM - barHeight;
      const bw = barWidth * barWidthRatio;
      ctx.fillRect(x, y, bw, barHeight);
      ctx.strokeStyle = HIGHLIGHT_COLOR;
      ctx.lineWidth = 0.3;
      ctx.strokeRect(x, y, bw, barHeight);
    });

    // --- 6. Calculate Stats (p-value, means) ---
    const overallMean = overallArr.length > 0 ? jStat.mean(overallArr) : 0;
    const highlightMean = highlightArr.length > 0 ? jStat.mean(highlightArr) : 0;

    let pValue: number | null = null;
    if (overallArr.length > 1 && highlightArr.length > 1) {
      const mean1 = jStat.mean(overallArr);
      const mean2 = jStat.mean(highlightArr);
      const var1 = jStat.variance(overallArr, true);
      const var2 = jStat.variance(highlightArr, true);
      const n1 = overallArr.length;
      const n2 = highlightArr.length;

      const t = (mean1 - mean2) / Math.sqrt(var1 / n1 + var2 / n2);

      const df = Math.pow(var1 / n1 + var2 / n2, 2) /
                ((Math.pow(var1 / n1, 2) / (n1 - 1)) + (Math.pow(var2 / n2, 2) / (n2 - 1)));

      pValue = 2 * (1 - jStat.studentt.cdf(Math.abs(t), df));
    }


    // --- 7. Draw Top Plot (StdDev Bars) ---
    const topContainerHeight = PADDING_TOP;
    
    // Draw bounding box for top plot
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    ctx.strokeRect(PADDING_LEFT, 0, CHART_WIDTH - PADDING_LEFT, topContainerHeight);

    // Draw std dev bars
    const overallMeanX = drawStdErrorBar(ctx, overallArr, globalMin, globalMax, '#666', topContainerHeight - 5);
    const highlightMeanX = drawStdErrorBar(ctx, highlightArr, globalMin, globalMax, '#000', topContainerHeight - 25);

    // Draw p-value
    if (pValue !== null) {
      ctx.fillStyle = '#000';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'left';
      let displayP = '';
      if (pValue < 1e-16) {
        displayP = 'p<1e-16';
      } else {
        displayP = `p=${pValue.toExponential(2)}`;
      }
      ctx.fillText(displayP, PADDING_LEFT + 5, topContainerHeight + 10);
    }
  }

  /**
   * Helper to draw an empty chart state.
   */
  function drawEmptyChart(message: string) {
    if (!ctx) return;
    ctx.clearRect(0, 0, CHART_WIDTH, CHART_HEIGHT);
    ctx.fillStyle = '#999';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(message, CHART_WIDTH / 2, CHART_HEIGHT / 2);
  }

  /**
   * Helper to create the striped pattern for comparison bars.
   */
  function createStripedPattern(ctx: CanvasRenderingContext2D, color = HIGHLIGHT_COLOR) {
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

  /**
   * Helper to draw the mean and standard deviation bar.
   */
  function drawStdErrorBar(ctx: CanvasRenderingContext2D, values: number[], totalMin: number, totalMax: number, color: string, y: number) {
    if (!ctx || !values || values.length < 2) return 0;

    const mean = jStat.mean(values);
    const stdDev = jStat.stdev(values, true); // true for sample stdev

    // Prevent division by zero if all values are identical
    const range = (totalMax - totalMin) || 1; 

    const meanX = PADDING_LEFT + ((mean - totalMin) / range) * (CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT);
    const stdDevPx = (stdDev / range) * (CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT);

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
    ctx.moveTo(meanX + stdDevPx, y + errorBarHeight);
    ctx.lineTo(meanX + stdDevPx, y - errorBarHeight);
    ctx.stroke();

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(meanX, y, 2.5, 0, 2 * Math.PI);
    ctx.fill();

    // Draw top plot labels
    ctx.font = '10px sans-serif';
    ctx.textBaseline = 'middle';
    
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.fillText(
      truncateText(`avg(${title[0]})=${Math.floor(mean * 100) / 100}`),
      meanX,
      y - errorBarHeight * 2.5
    );
    return meanX;
  }

  /**
   * Helper to truncate long legend text.
   */
  function truncateText(text: string, maxChars = 15) {
      const match = text.match(/^avg\((.*?)\)=(.*)$/);
      if (!match) {
        return text.length > maxChars ? text.slice(0, maxChars) + "…" : text;
      }

      let inside = match[1];
      const after = match[2];

      if (inside.length > maxChars) {
        inside = inside.slice(0, maxChars) + "…";
      }

      return `avg(${inside})=${after}`;
  }

  // --- Lifecycle and Reactivity ---
  onMount(() => {
    drawChart();
  });

  // Re-draw the chart whenever the processed data arrays or titles change
  $: if (canvasEl && highlightArr && overallArr && title) {
    drawChart();
  }

</script>

<canvas bind:this={canvasEl} style="margin-top: 20px;" />

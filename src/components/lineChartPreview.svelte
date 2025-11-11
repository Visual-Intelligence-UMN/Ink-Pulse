<script lang="ts">
  import * as d3 from "d3";

  type SelectionRange = { min: number; max: number };
  type SelectionWindow = {
    time?: SelectionRange | null;
    progress?: SelectionRange | null;
  };

  type NormalizedSelectionWindow = {
    time: SelectionRange | null;
    progress: SelectionRange | null;
  };

  export let chartData;
  export let selectedTimeRange: SelectionRange | null = null;
  export let selectedProgressRange: SelectionRange | null = null;
  export let highlightWindows: SelectionWindow[] = [];
  export let highlightMode: "time" | "progress" | "both" | null = null;
  export let selectionContext: {
    selectionSource?: string | null;
    timeMin?: number | null;
    timeMax?: number | null;
    progressMin?: number | null;
    progressMax?: number | null;
  } | null = null;
  // export let paragraphColor;

  let svgContainer: SVGSVGElement;
  let width = 250;
  let height = 150;
  const margin = { top: 10, right: 10, bottom: 30, left: 50 };

  let xScale: any;
  let yScale = d3
    .scaleLinear()
    .domain([0, 100])
    .range([height - margin.top - margin.bottom, 0]);

  let xAxisG: SVGGElement;
  let yAxisG: SVGGElement;

  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  let maxTime =
    chartData.length > 0 ? chartData[chartData.length - 1].time : 10;

  $: xScale = d3
    .scaleLinear()
    .domain([0, maxTime])
    .nice()
    .range([0, width - margin.left - margin.right]);

  $: yScale = d3
    .scaleLinear()
    .domain([0, 100])
    .range([height - margin.top - margin.bottom, 0]);

  $: if (xScale && yScale && xAxisG && yAxisG) {
    const xAxis = d3.axisBottom(xScale).ticks(5);
    const yAxis = d3.axisLeft(yScale).ticks(5);
    d3.select(xAxisG).call(xAxis);
    d3.select(xAxisG)
      .selectAll(".tick text")
      .filter((_, i) => i === 0)
      .attr("dx", "1px")
      .attr("text-anchor", "start");

    d3.select(yAxisG).call(yAxis);

    // Add Y-axis label
    d3.select(yAxisG).selectAll(".y-axis-label").remove();
    d3.select(yAxisG)
      .append("text")
      .attr("class", "y-axis-label")
      .attr("transform", "rotate(-90)")
      .attr("y", -35)
      .attr("x", -chartHeight / 2)
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .style("fill", "black")
      .text("Writing length");
  }

  function scaledX(val) {
    return xScale ? xScale(val) : 0;
  }

  function scaledY(val) {
    return yScale ? yScale(val) : 0;
  }

  function normalizeRange(
    range: SelectionRange | null | undefined,
    clampToHundred = false,
  ): SelectionRange | null {
    if (!range) return null;
    let min = Number(range.min);
    let max = Number(range.max);
    if (!Number.isFinite(min) || !Number.isFinite(max)) {
      return null;
    }
    if (min > max) {
      [min, max] = [max, min];
    }
    if (clampToHundred) {
      min = Math.max(0, Math.min(min, 100));
      max = Math.max(min, Math.min(max, 100));
    }
    return { min, max };
  }

  let normalizedWindows: NormalizedSelectionWindow[] = [];
  let hasSelection = false;
  let timeMarkers: number[] = [];
  let progressMarkers: number[] = [];
  let resolvedHighlightMode: "time" | "progress" | "both" | null = null;
  let normalizedSelectedTimeRange: SelectionRange | null = null;
  let normalizedSelectedProgressRange: SelectionRange | null = null;
  let effectiveSelection: {
    selectionSource?: string | null;
    timeMin?: number | null;
    timeMax?: number | null;
    progressMin?: number | null;
    progressMax?: number | null;
  } | null = null;

  function toNormalizedWindow(
    window: SelectionWindow,
  ): NormalizedSelectionWindow | null {
    const normalizedTime = normalizeRange(window?.time ?? null, false);
    const normalizedProgress = normalizeRange(window?.progress ?? null, true);

    if (!normalizedTime && !normalizedProgress) {
      return null;
    }

    return {
      time: normalizedTime,
      progress: normalizedProgress,
    };
  }

  $: normalizedWindows = (() => {
    const windowsSource =
      Array.isArray(highlightWindows) && highlightWindows.length > 0
        ? highlightWindows
        : [
            {
              time: selectedTimeRange,
              progress: selectedProgressRange,
            },
          ];

    return windowsSource
      .map((w) => toNormalizedWindow(w))
      .filter((w): w is NormalizedSelectionWindow => Boolean(w));
  })();

  $: hasSelection =
    normalizedWindows.length > 0 ||
    Boolean(selectedTimeRange || selectedProgressRange);

  $: resolvedHighlightMode = (() => {
    if (!hasSelection) return null;
    if (highlightMode) return highlightMode;
    const hasTime = normalizedWindows.some((w) => Boolean(w.time));
    const hasProgress = normalizedWindows.some((w) => Boolean(w.progress));
    if (hasTime && hasProgress) return "both";
    if (hasTime) return "time";
    if (hasProgress) return "progress";
    return null;
  })();

  $: timeMarkers = (() => {
    if (!hasSelection) return [];

    const markers = new Set<number>();
    normalizedWindows.forEach((window) => {
      if (window.time) {
        const minKey = Number(window.time.min.toFixed(4));
        const maxKey = Number(window.time.max.toFixed(4));
        markers.add(minKey);
        markers.add(maxKey);
      }
    });
    if (markers.size === 0 && normalizedSelectedTimeRange) {
      markers.add(Number(normalizedSelectedTimeRange.min.toFixed(4)));
      markers.add(Number(normalizedSelectedTimeRange.max.toFixed(4)));
    }

    return Array.from(markers).sort((a, b) => a - b);
  })();

  $: progressMarkers = (() => {
    if (!hasSelection) return [];

    const markers = new Set<number>();
    normalizedWindows.forEach((window) => {
      if (window.progress) {
        const minKey = Number(window.progress.min.toFixed(4));
        const maxKey = Number(window.progress.max.toFixed(4));
        markers.add(minKey);
        markers.add(maxKey);
      }
    });
    if (markers.size === 0 && normalizedSelectedProgressRange) {
      markers.add(Number(normalizedSelectedProgressRange.min.toFixed(4)));
      markers.add(Number(normalizedSelectedProgressRange.max.toFixed(4)));
    }

    return Array.from(markers).sort((a, b) => a - b);
  })();

  $: showTimeMarkers =
    resolvedHighlightMode === "time" || resolvedHighlightMode === "both";
  $: showProgressMarkers =
    resolvedHighlightMode === "progress" || resolvedHighlightMode === "both";

  $: normalizedSelectedTimeRange =
    selectedTimeRange && showTimeMarkers
      ? normalizeRange(selectedTimeRange, false)
      : null;

  $: normalizedSelectedProgressRange =
    selectedProgressRange && showProgressMarkers
      ? normalizeRange(selectedProgressRange, true)
      : null;

  $: effectiveSelection = (() => {
    if (selectionContext) {
      return selectionContext;
    }

    const selection: {
      selectionSource?: string | null;
      timeMin?: number | null;
      timeMax?: number | null;
      progressMin?: number | null;
      progressMax?: number | null;
    } = {};

    if (normalizedSelectedTimeRange) {
      selection.timeMin = normalizedSelectedTimeRange.min;
      selection.timeMax = normalizedSelectedTimeRange.max;
      selection.selectionSource = "lineChart_x";
    }

    if (normalizedSelectedProgressRange) {
      selection.progressMin = normalizedSelectedProgressRange.min;
      selection.progressMax = normalizedSelectedProgressRange.max;
      if (!selection.selectionSource) {
        selection.selectionSource = "lineChart_y";
      }
    }

    if (
      !selection.timeMin &&
      !selection.timeMax &&
      !selection.progressMin &&
      !selection.progressMax &&
      normalizedWindows.length
    ) {
      const primaryWindow = normalizedWindows[0];
      if (primaryWindow.time) {
        selection.timeMin = primaryWindow.time.min;
        selection.timeMax = primaryWindow.time.max;
        selection.selectionSource = "lineChart_x";
      }
      if (primaryWindow.progress) {
        selection.progressMin = primaryWindow.progress.min;
        selection.progressMax = primaryWindow.progress.max;
        if (!selection.selectionSource) {
          selection.selectionSource = "lineChart_y";
        }
      }
    }

    if (
      selection.timeMin === undefined &&
      selection.timeMax === undefined &&
      selection.progressMin === undefined &&
      selection.progressMax === undefined
    ) {
      return null;
    }

    return selection;
  })();

  function pointInSelection(d: any) {
    const considerTime = showTimeMarkers;
    const considerProgress = showProgressMarkers;

    if (
      (considerTime && normalizedSelectedTimeRange) ||
      (considerProgress && normalizedSelectedProgressRange)
    ) {
      const inTime =
        !considerTime ||
        !normalizedSelectedTimeRange ||
        (d.time >= normalizedSelectedTimeRange.min &&
          d.time <= normalizedSelectedTimeRange.max);
      const inProgress =
        !considerProgress ||
        !normalizedSelectedProgressRange ||
        (d.percentage >= normalizedSelectedProgressRange.min &&
          d.percentage <= normalizedSelectedProgressRange.max);
      return inTime && inProgress;
    }

    if (!normalizedWindows.length) return true;

    return normalizedWindows.some((window) => {
      const inTime =
        !considerTime ||
        !window.time ||
        (d.time >= window.time.min && d.time <= window.time.max);
      const inProgress =
        !considerProgress ||
        !window.progress ||
        (d.percentage >= window.progress.min &&
          d.percentage <= window.progress.max);

      return inTime && inProgress;
    });
  }

  function getSelectionContextOpacity(d: any) {
    if (!effectiveSelection) return null;

    const {
      selectionSource,
      timeMin,
      timeMax,
      progressMin,
      progressMax,
    } = effectiveSelection;

    if (
      selectionSource === "lineChart_x" &&
      Number.isFinite(timeMin) &&
      Number.isFinite(timeMax)
    ) {
      const inTimeRange = d.time >= timeMin && d.time <= timeMax;
      return inTimeRange ? 1 : 0.01;
    }

    if (Number.isFinite(progressMin) && Number.isFinite(progressMax)) {
      const inProgressRange =
        d.percentage >= progressMin && d.percentage <= progressMax;
      return inProgressRange ? 1 : 0.01;
    }

    return null;
  }

  function clampOpacity(opacity: number | undefined, fallback: number) {
    if (typeof opacity !== "number" || Number.isNaN(opacity)) {
      return fallback;
    }
    return Math.max(0, Math.min(opacity, 1));
  }

  const DIMMED_CIRCLE_OPACITY = 0.01;
  const DIMMED_TRIANGLE_OPACITY = 0.3;

  function getCircleOpacity(d: any) {
    const baseOpacity =
      typeof d.opacity === "number" && !Number.isNaN(d.opacity)
        ? d.opacity
        : 1;

    const selectionOpacity = getSelectionContextOpacity(d);
    if (selectionOpacity !== null) {
      return selectionOpacity === 1
        ? clampOpacity(baseOpacity, 1)
        : clampOpacity(selectionOpacity, DIMMED_CIRCLE_OPACITY);
    }

    if (!hasSelection) {
      return clampOpacity(baseOpacity, 1);
    }

    if (pointInSelection(d)) {
      return clampOpacity(baseOpacity, 1);
    }

    return Math.min(baseOpacity, DIMMED_CIRCLE_OPACITY);
  }

  function getTriangleOpacity(d: any) {
    const base =
      typeof d.opacity === "number" && !Number.isNaN(d.opacity)
        ? Math.min(d.opacity + 0.29, 1)
        : 0.6;

    const selectionOpacity = getSelectionContextOpacity(d);
    if (selectionOpacity !== null) {
      return selectionOpacity === 1
        ? clampOpacity(base, 1)
        : clampOpacity(selectionOpacity, DIMMED_TRIANGLE_OPACITY);
    }

    if (!hasSelection) {
      return clampOpacity(base, 1);
    }

    if (pointInSelection(d)) {
      return clampOpacity(base, 1);
    }

    return Math.min(base, DIMMED_TRIANGLE_OPACITY);
  }
</script>

<svg bind:this={svgContainer} {width} {height} style="vertical-align: top">
  <defs>
    <clipPath id="clip_preview">
      <rect
        x="0"
        y="0"
        width={width - margin.left - margin.right}
        height={height - margin.top - margin.bottom}
      />
    </clipPath>
  </defs>

  <g transform={`translate(${margin.left},${margin.top})`}>
    <g clip-path="url(#clip_preview)">
      <g>
        <!-- Selected range highlight -->
        {#if hasSelection}
          {#if showTimeMarkers}
            {#each timeMarkers as marker}
              <line
                x1={scaledX(marker)}
                x2={scaledX(marker)}
                y1={0}
                y2={chartHeight}
                stroke="#000000"
                stroke-width="1"
                stroke-dasharray="3,3"
                vector-effect="non-scaling-stroke"
                pointer-events="none"
              />
            {/each}
          {/if}
          {#if showProgressMarkers}
            {#each progressMarkers as marker}
              <line
                x1={0}
                x2={chartWidth}
                y1={scaledY(marker)}
                y2={scaledY(marker)}
                stroke="#000000"
                stroke-width="1"
                stroke-dasharray="3,3"
                vector-effect="non-scaling-stroke"
                pointer-events="none"
              />
            {/each}
          {/if}
        {/if}

        <!-- {#each paragraphColor as d}
          <rect
            x={scaledX(d.xMin)}
            width={scaledX(d.xMax) - scaledX(d.xMin)}
            y={scaledY(d.yMax)}
            height={scaledY(d.yMin) - scaledY(d.yMax)}
            fill={d.backgroundColor}
          />
        {/each}
        </g> -->

        <g>
          {#each chartData.filter((d) => !d.isSuggestionOpen) as d (d.index)}
            <circle
              cx={scaledX(d.time)}
              cy={scaledY(d.percentage)}
              r={2}
              fill={d.color}
              opacity={getCircleOpacity(d)}
            />
          {/each}

          {#each chartData.filter((d) => d.isSuggestionOpen) as d}
            <path
              d={d3.symbol().type(d3.symbolTriangle).size(40)()}
              fill={d.isSuggestionAccept ? "#ffffff" : "#cccccc"}
              stroke="#aaaaaa"
              stroke-width="1"
              opacity={getTriangleOpacity(d)}
              transform={`translate(${scaledX(d.time)},${scaledY(d.percentage + 6)}) rotate(180)`}
            />
          {/each}
        </g>
      </g>
    </g>

    <g
      class="x-axis"
      transform={`translate(0, ${chartHeight - 4.5})`}
      bind:this={xAxisG}
    >
      <text
        x={chartWidth / 2}
        y={25}
        text-anchor="middle"
        font-size="10px"
        fill="black"
      >
        Time (min)
      </text>
    </g>

    <g class="y-axis" bind:this={yAxisG}></g>
  </g></svg
>
